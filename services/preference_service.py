import uuid
from typing import Dict, Any, List, Set, Optional
import logging
from datetime import datetime

from extensions import db
from models import (
    Preference, PreferenceKeywords,
    Keywords, CityInfosMapping, UserInfosPreference
)
from api.google_places import GooglePlacesAPI
from .place_service import PlaceService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PreferenceService:
    def __init__(self, db_session: db):
        self.db = db_session
        self.place_service = PlaceService(db_session)

    def save_preference_and_fetch_places(self,
                                         form_data: Dict[str, Any],
                                         api: GooglePlacesAPI,
                                         user_id: Optional[str] = None) -> Preference:
        """
        儲存偏好設定、建立使用者關聯（如果有）並獲取地點資訊

        Args:
            form_data: 表單資料
            api: Google Places API實例
            user_id: 使用者ID (選填)

        Returns:
            Preference: 新建立的偏好設定實例
        """
        try:
            # 儲存Preference與PreferenceKeywords
            new_preference = self._save_preference(form_data)

            # 如果有使用者ID，建立使用者與偏好設定的關聯
            if user_id:
                if hasattr(user_id, 'u_id'):  # 如果傳入的是UserInfos物件
                    user_uuid = str(user_id.u_id)
                else:  # 如果傳入的是字串
                    user_uuid = str(user_id)

                user_preference = UserInfosPreference(
                    u_id=uuid.UUID(user_uuid),  # 轉換為UUID物件
                    p_id=new_preference.p_id
                )
                self.db.add(user_preference)
                logger.info(f"Created association between user {user_id} and preference {new_preference.p_id}")

            # 獲取CityInfos
            city_info = self.db.query(CityInfosMapping).filter_by(
                c_id=int(form_data['city'])).first()
            if not city_info:
                raise ValueError(f"找不到城市資訊: {form_data['city']}")

            # 獲取place_id的list
            places_info = self.place_service.collect_place_ids(
                api, city_info, new_preference)
            self.place_service.process_place_details(api, places_info)

            self.db.commit()
            return new_preference

        except Exception as e:
            self.db.rollback()
            logger.error(f"儲存偏好設定時發生錯誤: {str(e)}")
            raise

    def _save_preference(self, form_data: Dict[str, Any]) -> Preference:
        """儲存偏好設定到資料庫"""
        try:
            # 創建基本偏好設定
            new_preference = Preference(
                p_name=form_data['p_name'],
                departure_datetime=datetime.strptime(
                    form_data['departure_datetime'], '%Y-%m-%dT%H:%M'),
                return_datetime=datetime.strptime(
                    form_data['return_datetime'], '%Y-%m-%dT%H:%M'),
                daily_depart_time=datetime.strptime(
                    form_data['daily_depart_time'], '%H:%M').time(),
                daily_return_time=datetime.strptime(
                    form_data['daily_return_time'], '%H:%M').time(),
                budget=int(form_data['budget']),
                travel_mode=form_data['travel_mode'],
                price_level_weight=form_data['price_level_weight'],
                rating_weight=form_data['rating_weight'],
                user_rating_total_weight=form_data['user_rating_total_weight'],
                city=int(form_data['city'])
            )

            self.db.add(new_preference)
            self.db.flush()

            # Preference與Keywords進行關聯
            self._handle_keywords(new_preference, form_data['place_types_keywords'])

            return new_preference

        except Exception as e:
            self.db.rollback()
            logger.error(f"儲存偏好設定時發生錯誤: {str(e)}")
            raise

    def _handle_keywords(self, preference: Preference,
                        place_types_keywords: Dict[str, List[str]]) -> None:
        """處理關鍵字關聯"""
        try:
            for type_id, keywords in place_types_keywords.items():

                # 處理關鍵字
                for keyword in keywords:

                    # 尋找是否有相同的k_name與place_types
                    existing_keyword = self.db.query(Keywords).filter_by(
                        k_name=keyword,
                        place_types=int(type_id)
                    ).first()

                    # 如果沒有則添加該關鍵字
                    if not existing_keyword:
                        existing_keyword = Keywords(
                            k_name=keyword,
                            place_types=int(type_id)
                        )
                        self.db.add(existing_keyword)
                        self.db.flush()

                    # 並且將Preference與Keywords透過PreferenceKeywords做多對多關聯
                    preference_keyword = PreferenceKeywords(
                        p_id=preference.p_id,
                        k_id=existing_keyword.k_id
                    )
                    self.db.add(preference_keyword)

            self.db.commit()

        except Exception as e:
            self.db.rollback()
            logger.error(f"處理關鍵字關聯時發生錯誤: {str(e)}")
            raise

    def search_available_places(self, form_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        搜索符合條件的地點

        Args:
            form_data: 表單數據，包含城市、時間和關鍵字等資訊

        Returns:
            List[Dict[str, Any]]格式為:
            [
                {
                    'place_id': str,
                    'place_name: str,
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
            ]
        """
        try:
            # 獲取k_id
            keyword_ids = self._get_keyword_ids_from_form(form_data['place_types_keywords'])

            # 使用 PlaceService 獲取符合條件的地點（返回字典格式）
            places_dict = self.place_service.get_available_places(
                city_id=int(form_data['city']),
                keyword_ids=keyword_ids,
                start_datetime=form_data['departure_datetime'],
                end_datetime=form_data['return_datetime']
            )

            # 將字典格式轉換為列表格式
            places_list = []
            for place_id, place_info in places_dict.items():
                places_list.append({
                    'place_id': place_id,
                    'place_name': place_info['place_name'],
                    'lat': place_info['lat'],
                    'lng': place_info['lng'],
                    'opening_hour': place_info['opening_hour'],
                    'types': place_info['types'],
                    'price_level': place_info['price_level'],
                    'rating': place_info['rating'],
                    'user_rating_totals': place_info['user_rating_totals']
                })

            return places_list

        except Exception as e:
            logger.error(f"搜索可用地點時發生錯誤: {str(e)}")
            raise

    def _get_keyword_ids_from_form(self, place_types_keywords: Dict[str, List[str]]) -> Set[int]:
        try:
            keyword_ids = set()

            for type_id, keywords in place_types_keywords.items():
                type_id_int = int(type_id)

                # 處理基本類型 (1-6)
                if 1 <= type_id_int <= 6:
                    # 從 keywords 表中獲取對應的關鍵字
                    base_keyword = self.db.query(Keywords).filter_by(
                        k_id=type_id_int,
                        place_types=type_id_int
                    ).first()

                    if base_keyword:
                        keyword_ids.add(base_keyword.k_id)
                        # 將基本關鍵字添加到 keywords 列表中
                        keywords.append(base_keyword.k_name)
                        logger.info(
                            f"添加基本類型關鍵字: type_id={type_id_int}, k_id={base_keyword.k_id}, name={base_keyword.k_name}")

                # 處理其他關鍵字
                for keyword_name in keywords:
                    keyword = self.db.query(Keywords).filter_by(
                        k_name=keyword_name,
                        place_types=type_id_int
                    ).first()

                    if keyword:
                        keyword_ids.add(keyword.k_id)
                        logger.info(f"添加關鍵字: type_id={type_id_int}, k_id={keyword.k_id}, name={keyword.k_name}")

            return keyword_ids

        except Exception as e:
            logger.error(f"獲取關鍵字ID時發生錯誤: {str(e)}")
            raise

    def get_user_preferences(self, user_id: str) -> List[Preference]:
        """
        獲取使用者的所有偏好設定

        Args:
            user_id: 使用者ID

        Returns:
            List[Preference]: 使用者的偏好設定列表
        """
        try:
            return self.db.query(Preference) \
                .join(UserInfosPreference) \
                .filter(UserInfosPreference.u_id == user_id) \
                .all()
        except Exception as e:
            logger.error(f"獲取使用者 {user_id} 的偏好設定時發生錯誤: {str(e)}")
            raise
