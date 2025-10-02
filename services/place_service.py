from typing import Dict, Any, Set, Tuple, List, Optional
import logging
import re
from datetime import datetime, timedelta
from sqlalchemy import and_
from extensions import db
from api.google_places import GooglePlacesAPI
from models import (
    PlaceInfos, PlaceTypes, Keywords,
    PlaceInfosKeywords, PlaceOpeningHoursForEachDays,
    CityInfosMapping, Preference, PreferenceKeywords
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _get_travel_days(start_datetime: str, end_datetime: str) -> List[int]:
    """獲取旅程期間的星期幾"""
    start_date = datetime.strptime(start_datetime, '%Y-%m-%dT%H:%M').date()
    end_date = datetime.strptime(end_datetime, '%Y-%m-%dT%H:%M').date()

    days = set()
    current_date = start_date
    while current_date <= end_date:
        # 轉換星期幾格式 (0=星期日, 1-6=星期一到星期六)
        weekday = current_date.weekday()
        adjusted_weekday = 0 if weekday == 6 else weekday + 1
        days.add(adjusted_weekday)
        current_date += timedelta(days=1)

    return sorted(list(days))


class PlaceService:
    def __init__(self, db_session: db):
        self.db = db_session

    def collect_place_ids(self, api: GooglePlacesAPI,
                          city_info: CityInfosMapping,
                          preference: Preference) -> Dict[str, Set[Tuple[int, int]]]:
        """收集所有符合條件的地點ID及其搜尋資訊"""
        all_places = {}
        base_params = {
            'location': f"{city_info.lat},{city_info.lng}",
            'radius': city_info.radius
        }

        try:

            # 獲取所有與該Preference關聯的關鍵字，並確保基本類別先執行
            all_keywords = (
                self.db.query(Keywords)  # 從Keywords表中
                .join(PreferenceKeywords, PreferenceKeywords.k_id == Keywords.k_id)  # 與PreferenceKeywords join找出與該Preference相同的k_id
                .filter(PreferenceKeywords.p_id == preference.p_id)  # 並且須為相同的p_id
                .order_by(Keywords.k_id)
                .all()
            )

            logger.info(f"找到 {len(all_keywords)} 個關聯的關鍵字")

            # 處理每個關鍵字
            for keyword in all_keywords:
                place_type = self.db.query(PlaceTypes).filter_by(
                    t_id=keyword.place_types
                ).first()

                # Nearby Search所需參數
                search_params = {
                    **base_params,
                    'type': place_type.t_name,
                    'keyword': keyword.k_name
                }

                logger.info(
                    f"執行搜尋: type={place_type.t_name}, keyword={keyword.k_name}, type_id={keyword.place_types}, k_id={keyword.k_id}")

                # 蒐集經篩選過後的Nearby Search結果，存為place_ids['place_id']:place_id
                place_ids = api.get_nearby_places(search_params)
                for place_id in place_ids:
                    if place_id not in all_places:
                        all_places[place_id] = set()
                    all_places[place_id].add((keyword.place_types, keyword.k_id))
                    logger.info(f"找到地點: place_id={place_id}, type={place_type.t_name}, keyword={keyword.k_name}")

            total_searches = len(all_keywords)
            logger.info(f"共收集到 {len(all_places)} 個地點")
            logger.info(f"總共執行了 {total_searches} 次搜尋")
            return all_places

        except Exception as e:
            logger.error(f"收集地點ID時發生錯誤: {str(e)}")
            raise

    def _save_place_info(self, details: Dict[str, Any],
                         city_id: int,
                         type_keyword_pairs: Set[Tuple[int, int]]) -> None:
        """儲存地點資訊到資料庫"""
        try:
            place_id = details['place_id']
            location = details['geometry']['location']

            # 更新或創建地點資訊
            place_info = (self.db.query(PlaceInfos)
                          .get(place_id)) or PlaceInfos(place_id=place_id)

            # 更新基本資訊
            place_info.place_last_updated = datetime.now()
            place_info.place_lat = float(location['lat'])
            place_info.place_lng = float(location['lng'])
            place_info.place_name = details['name']
            place_info.formatted_address = details['formatted_address']
            place_info.place_phone_number = details.get('formatted_phone_number')
            place_info.place_price_level = details.get('price_level', 0)
            place_info.place_rating = details.get('rating', 0.0)
            place_info.place_rating_total = details.get('user_ratings_total', 0)
            place_info.place_disabilities_friendly = details.get(
                'wheelchair_accessible_entrance', False)
            place_info.city = city_id

            self.db.add(place_info)

            # 只處理關鍵字關聯
            self._update_place_keywords(place_info, type_keyword_pairs)
            self._handle_opening_hours(
                place_info, details['opening_hours']['periods'])

            self.db.commit()

        except Exception as e:
            self.db.rollback()
            logger.error(f"儲存地點 {place_id} 時發生錯誤: {str(e)}")
            raise

    def process_place_details(self, api: GooglePlacesAPI,
                            places: Dict[str, Set[Tuple[int, int]]]) -> None:
        """處理並儲存地點詳細資訊"""
        processed = skipped = errors = 0

        for place_id, type_keyword_pairs in places.items():
            try:

                # 檢查是否需要更新
                existing_place = self.db.query(PlaceInfos).get(place_id)
                # 如果存在則檢查是否需要更新，以及是不是用其他關鍵字所搜索到，如果是，加上PlaceInfosKeywords關聯並且跳過
                if (existing_place and
                        not api.is_place_info_outdated(existing_place.place_last_updated)):
                    self._update_place_keywords(existing_place, type_keyword_pairs)
                    skipped += 1
                    continue

                # 獲取place資訊
                details = api.get_place_details(place_id)
                if not details or 'result' not in details:
                    errors += 1
                    continue

                # 解析city
                city_id = self._get_city_from_address(
                    details['result'].get('formatted_address', ''))
                if city_id is None:
                    errors += 1
                    continue

                # 儲存資訊
                self._save_place_info(details['result'], city_id, type_keyword_pairs)
                processed += 1

            except Exception as e:
                errors += 1
                logger.error(f"處理地點 {place_id} 時發生錯誤: {str(e)}")

        logger.info(
            f"地點處理完成: 成功 {processed}, 跳過 {skipped}, 失敗 {errors}")

    def _get_city_from_address(self, formatted_address: str) -> Optional[int]:
        """從地址中解析城市ID"""
        try:
            # 從地址中前三碼提取郵遞區號
            postal_code_match = re.match(r'^(\d{3})', formatted_address)
            if not postal_code_match:
                logger.warning(f"無法從地址 '{formatted_address}' 提取郵遞區號")
                return None

            postal_code = int(postal_code_match.group(1))

            # 查詢符合郵遞區號範圍的城市
            city = self.db.query(CityInfosMapping).filter(
                CityInfosMapping.postal_code_min <= postal_code,
                CityInfosMapping.postal_code_max >= postal_code
            ).first()

            if city:
                logger.info(f"從郵遞區號 {postal_code} 判定城市為 {city.c_chinese}")
                return city.c_id
            else:
                logger.warning(f"郵遞區號 {postal_code} 不在任何已知城市範圍內")
                return None

        except Exception as e:
            logger.error(f"解析地址 '{formatted_address}' 時發生錯誤: {str(e)}")
            return None

    def _update_place_keywords(self, place_info: PlaceInfos,
                             type_keyword_pairs: Set[Tuple[int, int]]) -> None:
        """更新地點的關鍵字關聯"""
        try:
            # 獲取該place在資料庫中有的keywords
            existing_relations = self.db.query(PlaceInfosKeywords).filter_by(
                place_id=place_info.place_id).all()
            existing_k_ids = {rel.k_id for rel in existing_relations}
            # 添加其他關鍵字關聯
            for _, k_id in type_keyword_pairs:
                if k_id not in existing_k_ids:
                    new_relation = PlaceInfosKeywords(
                        place_id=place_info.place_id,
                        k_id=k_id
                    )
                    self.db.add(new_relation)

            self.db.commit()

        except Exception as e:
            self.db.rollback()
            logger.error(f"更新地點關鍵字關聯時發生錯誤: {str(e)}")
            raise

    def _handle_opening_hours(self, place_info: PlaceInfos,
                              periods: List[Dict[str, Any]]) -> None:
        """處理營業時間資訊"""
        try:
            # 清除現有營業時間
            self.db.query(PlaceOpeningHoursForEachDays).filter_by(
                place_id=place_info.place_id).delete()

            # 處理24小時營業的情況
            if (len(periods) == 1 and
                    'open' in periods[0] and
                    periods[0]['open'].get('time') == '0000' and
                    'close' not in periods[0]):
                # 第一種情況：每天24小時營業
                # 只有一個period且只有open沒有close，表示全天24小時營業
                for day in range(7):  # 0-6 代表週日到週六
                    opening_hour = PlaceOpeningHoursForEachDays(
                        place_id=place_info.place_id,
                        day_of_week=day,
                        open_time=datetime.strptime('0000', '%H%M').time(),
                        close_time=datetime.strptime('2359', '%H%M').time()
                    )
                    self.db.add(opening_hour)
            else:
                # 處理一般營業時間或部分日子24小時營業
                for period in periods:
                    if 'open' not in period:
                        continue

                    day = period['open'].get('day')
                    open_time_str = period['open'].get('time')

                    if not all([day is not None, open_time_str]):
                        continue

                    open_time = datetime.strptime(open_time_str, '%H%M').time()

                    # 檢查是否為當天24小時營業（第二種情況）
                    if 'close' not in period:
                        close_time = datetime.strptime('2359', '%H%M').time()
                    else:
                        close_time = datetime.strptime(period['close']['time'], '%H%M').time()

                    opening_hour = PlaceOpeningHoursForEachDays(
                        place_id=place_info.place_id,
                        day_of_week=day,
                        open_time=open_time,
                        close_time=close_time
                    )
                    self.db.add(opening_hour)

            self.db.commit()

        except Exception as e:
            self.db.rollback()
            logger.error(f"處理營業時間時發生錯誤: {str(e)}")
            raise

    def get_available_places(self, city_id: int, keyword_ids: Set[int],
                         start_datetime: str, end_datetime: str) -> Dict[str, Dict[str, Any]]:
        """
        獲取符合條件的地點資訊

        Args:
            city_id: 城市ID
            keyword_ids: 關鍵字ID集合
            start_datetime: 開始日期時間 (格式: 'YYYY-MM-ddTHH:mm')
            end_datetime: 結束日期時間 (格式: 'YYYY-MM-ddTHH:mm')

        Returns:
            Dict格式為:
            {
                place_id: {
                    'place_id': str,
                    'place_name': str
                    'lat': float,
                    'lng': float,
                    'opening_hour': {
                        '6': [open_time1, close_time1, open_time2, close_time2, ...],
                        '0': [...],
                        '1': [...]
                    },
                    'types': [str, str, ...],  # keywords的place_types列表
                    'price_level': int,
                    'rating': float,
                    'user_rating_totals': int
                },
                ...
            }
        """
        try:
            # 1. 獲取符合城市和關鍵字的地點
            matching_places = self._get_matching_places(city_id, keyword_ids)
            if not matching_places:
                logger.info("沒有找到符合條件的地點")
                return {}

            # 2. 獲取旅程日期對應的星期幾
            travel_days = _get_travel_days(start_datetime, end_datetime)

            # 3. 構建結果
            result = {}
            for place in matching_places:
                # 獲取營業時間
                opening_hours = self._get_opening_hours(place.place_id, travel_days)
                if not opening_hours:
                    continue  # 如果沒有營業時間記錄，跳過此地點

                # 獲取地點類型
                place_types = self._get_place_types(place.place_id)

                # 構建地點資訊
                result[place.place_id] = {
                    'place_id': place.place_id,
                    'place_name': place.place_name,
                    'lat': place.place_lat,
                    'lng': place.place_lng,
                    'opening_hour': opening_hours,
                    'types': place_types,
                    'price_level': place.place_price_level,
                    'rating': place.place_rating,
                    'user_rating_totals': place.place_rating_total
                }

            logger.info(f"找到 {len(result)} 個符合條件的地點")
            return result

        except Exception as e:
            logger.error(f"獲取可用地點時發生錯誤: {str(e)}")
            raise

    def _get_matching_places(self, city_id: int, keyword_ids: Set[int]) -> List[PlaceInfos]:
        """獲取符合城市和關鍵字的地點"""
        return self.db.query(PlaceInfos).join(
            PlaceInfosKeywords,
            PlaceInfos.place_id == PlaceInfosKeywords.place_id
        ).filter(
            and_(
                PlaceInfos.city == city_id,
                PlaceInfosKeywords.k_id.in_(keyword_ids)
            )
        ).distinct().all()

    def _get_opening_hours(self, place_id: str, days: List[int]) -> Dict[str, List[Any]]:
        """獲取指定日期的營業時間"""
        opening_hours = {}
        for day in days:
            hours = self.db.query(PlaceOpeningHoursForEachDays).filter(
                and_(
                    PlaceOpeningHoursForEachDays.place_id == place_id,
                    PlaceOpeningHoursForEachDays.day_of_week == day
                )
            ).order_by(PlaceOpeningHoursForEachDays.open_time).all()

            if hours:
                # 將同一天的營業時間整理成列表
                time_list = []
                for hour in hours:
                    time_list.extend([hour.open_time, hour.close_time])
                opening_hours[str(day)] = time_list

        return opening_hours

    def _get_place_types(self, place_id: str) -> List[str]:
        """獲取地點的所有關鍵字對應的地點類型"""
        types = self.db.query(PlaceTypes.t_name).distinct().join(
            Keywords, Keywords.place_types == PlaceTypes.t_id
        ).join(
            PlaceInfosKeywords,
            PlaceInfosKeywords.k_id == Keywords.k_id
        ).filter(
            PlaceInfosKeywords.place_id == place_id
        ).all()

        return [t[0] for t in types]
