from typing import List, Dict, Any, Tuple, Union
from datetime import datetime, time, timedelta
import logging
import json
from flask import session, render_template, flash, redirect, url_for
import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class JourneyDataService:
    """處理行程資料的服務類"""

    def __init__(self):
        """初始化服務"""
        self.GOOGLE_MAPS_API_KEY = config.API_KEY

    def show_journey_result(self) -> str:
        """
        顯示行程結果頁面

        Returns:
            str: 渲染後的模板或重定向
        """
        try:
            journey_data = session.get('journey_data')
            if not journey_data:
                flash({'message': '找不到行程資料，請重新規劃行程'}, 'error')
                return redirect(url_for('homepage'))

            # 處理日期時間格式
            processed_data = self.process_session_journey_data(journey_data)

            return render_template(
                'trip_planning_result.html',
                google_maps_api_key=self.GOOGLE_MAPS_API_KEY,
                journey=processed_data.get('journey', []),
                recommended_places=processed_data.get('recommended_places', [])
            )
        except Exception as e:
            logger.error(f"顯示結果時發生錯誤: {str(e)}")
            flash({'message': '顯示結果時發生錯誤，請重新規劃行程'}, 'error')
            return redirect(url_for('homepage'))

    def get_route_info(self) -> Dict[str, Any]:
        """
        獲取路線資訊

        Returns:
            Dict: 包含路線資訊的字典
        """
        try:
            journey_data = session.get('journey_data')
            if not journey_data:
                return {
                    'status': 'ERROR',
                    'message': '找不到行程資料，請重新規劃行程'
                }

            # 處理日期時間格式
            processed_data = self.process_session_journey_data(journey_data)

            return {
                'status': 'OK',
                'journey': processed_data.get('journey', []),
                'route': processed_data.get('route', {})
            }

        except Exception as e:
            logger.error(f"獲取路線資料時發生錯誤: {str(e)}")
            return {
                'status': 'ERROR',
                'message': str(e)
            }

    def process_journey_data(self, journey: List[Dict[str, Any]],
                             available_places: List[Dict[str, Any]],
                             budget: int) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """處理行程資料並生成增強的行程和推薦地點"""
        try:
            available_places_dict = {place['place_id']: place for place in available_places}
            enhanced_journey, journey_place_ids = self._enhance_journey(journey, available_places_dict)
            recommended_places = self._generate_recommended_places(journey_place_ids, available_places, budget)

            return enhanced_journey, recommended_places

        except Exception as e:
            logger.error(f"處理行程資料時發生錯誤: {str(e)}")
            return [], []

    def process_session_journey_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """處理 session 中的行程資料"""
        processed_data = data.copy()
        try:
            if 'journey' in processed_data:
                for place in processed_data['journey']:
                    for time_field in ['place_start_datetime', 'place_end_datetime']:
                        if time_field in place and isinstance(place[time_field], str):
                            place[time_field] = self.parse_datetime(place[time_field])
            return processed_data

        except Exception as e:
            logger.error(f"處理 session 行程資料時發生錯誤: {str(e)}")
            return processed_data

    @staticmethod
    def parse_datetime(date_str: str) -> Union[datetime, str]:
        """解析日期時間字串"""
        try:
            return datetime.fromisoformat(date_str)
        except (ValueError, TypeError):
            return date_str

    @staticmethod
    def serialize_datetime(obj: Any) -> str:
        """序列化日期時間物件"""
        if isinstance(obj, (datetime, time)):
            return obj.isoformat()
        return obj

    @staticmethod
    def _enhance_journey(journey: List[Dict[str, Any]],
                         available_places_dict: Dict[str, Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], set]:
        """
        增強現有行程資料

        Returns:
            Tuple[List[Dict], set]: (增強的行程, 已使用的地點ID集合)
        """
        enhanced_journey = []
        journey_place_ids = set()

        for place in journey:
            place_id = place.get('place_id')
            if not place_id:
                logger.warning(f"跳過缺少place_id的地點: {place}")
                continue

            journey_place_ids.add(place_id)
            if place_id in available_places_dict:
                enhanced_place = JourneyDataService._create_enhanced_place(
                    place, available_places_dict[place_id]
                )
                enhanced_journey.append(enhanced_place)
                logger.info(f"已增強地點資訊: {place_id}")
            else:
                logger.warning(f"在可用地點中找不到: {place_id}")

        return enhanced_journey, journey_place_ids

    @staticmethod
    def _create_enhanced_place(place: Dict[str, Any],
                               place_info: Dict[str, Any]) -> Dict[str, Any]:
        """創建增強的地點資訊"""
        return {
            'place_id': place['place_id'],
            'place_name': place_info.get('place_name'),
            'place_start_datetime': place['place_start_datetime'],
            'place_end_datetime': place['place_end_datetime'],
            'lat': place_info.get('lat'),
            'lng': place_info.get('lng'),
            'types': place_info.get('types', []),
            'opening_hour': place_info.get('opening_hour', {}),
            'price_level': place_info.get('price_level', 0),
            'rating': place_info.get('rating', 0.0),
            'user_rating_totals': place_info.get('user_rating_totals', 0)
        }

    @staticmethod
    def _generate_recommended_places(existing_place_ids: set,
                                     available_places: List[Dict[str, Any]],
                                     budget: int) -> List[Dict[str, Any]]:
        """
        生成推薦地點列表

        Args:
            existing_place_ids: 已經在行程中的地點ID集合
            available_places: 所有可用地點
            budget: 預算限制

        Returns:
            List[Dict]: 推薦地點列表
        """
        recommended_places = []
        for place in available_places:
            if place.get('place_id') not in existing_place_ids and place.get('price_level', 0) <= budget:
                recommended_places.append(JourneyDataService._create_recommended_place(place))

        # 根據評分和評論數排序
        recommended_places.sort(
            key=lambda x: (x['rating'], x['user_rating_totals']),
            reverse=True
        )

        return recommended_places

    @staticmethod
    def _create_recommended_place(place: Dict[str, Any]) -> Dict[str, Any]:
        """創建推薦地點資訊"""
        return {
            'place_id': place['place_id'],
            'place_name': place.get('place_name'),
            'lat': place.get('lat'),
            'lng': place.get('lng'),
            'types': place.get('types', []),
            'opening_hour': place.get('opening_hour', {}),
            'price_level': place.get('price_level', 0),
            'rating': place.get('rating', 0.0),
            'user_rating_totals': place.get('user_rating_totals', 0)
        }

    @staticmethod
    def serialize_journey_data(obj: Any) -> str:
        """
        將日期時間物件序列化為字串格式

        Args:
            obj: 要序列化的物件

        Returns:
            str: 序列化後的字串
        """
        if isinstance(obj, (datetime, time)):
            return obj.isoformat()
        return obj

    @staticmethod
    def adjust_transit_times(journey: list, routes_data: list) -> None:
        """根據交通時間調整景點開始時間"""
        for route in routes_data:
            for place in journey:
                if place['place_id'] == route['destination_id']:
                    transit_time = route['total_duration_value']
                    prev_end_time = route['departure_time']
                    if isinstance(prev_end_time, str):
                        prev_end_time = datetime.strptime(prev_end_time, '%Y-%m-%d %H:%M:%S')
                    new_start_time = prev_end_time + timedelta(seconds=transit_time)
                    place['place_start_datetime'] = new_start_time.strftime('%Y-%m-%d %H:%M:%S')
                    break

    def store_journey_data(self, journey_data: Dict[str, Any]) -> bool:
        """
        將行程資料存入session

        Args:
            journey_data: 要儲存的行程資料

        Returns:
            bool: 是否成功儲存
        """
        try:
            serialized_data = json.loads(
                json.dumps(journey_data, default=self.serialize_journey_data)
            )
            session['journey_data'] = serialized_data
            session.modified = True
            return True
        except Exception as e:
            logger.error(f"儲存行程資料時發生錯誤: {str(e)}")
            return False
