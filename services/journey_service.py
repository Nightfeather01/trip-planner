from typing import List, Dict, Any
import logging
from extensions import db
from models import Journey, PlacesOfTheJourney, UserInfosJourney, Preference

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class JourneyService:
    def __init__(self, db_session: db):
        self.db = db_session

    def save_journey_result(self,
                            preference: Preference,
                            journey_result: List[Dict[str, Any]],
                            user_id: str = None) -> Journey:
        """
        儲存旅程結果到資料庫

        Args:
            preference: Preference物件
            journey_result: 包含地點和時間安排的旅程結果列表
            user_id: 使用者ID (選填)

        Returns:
            Journey: 新建立的journey物件
        """
        try:
            # 創建新的journey記錄，設定對應的preference資訊
            new_journey = Journey(
                preference=preference.p_id,
                city=preference.city,
                j_budget=preference.budget
            )
            self.db.add(new_journey)
            self.db.flush()  # 取得new_journey.j_id

            # 如果有user_id，建立user和journey的關聯
            if user_id:
                user_journey = UserInfosJourney(
                    u_id=user_id,
                    j_id=new_journey.j_id
                )
                self.db.add(user_journey)

            # 儲存每個地點的行程安排
            for place in journey_result:
                journey_place = PlacesOfTheJourney(
                    place_start_datetime=place['place_start_datetime'],
                    place_end_datetime=place['place_end_datetime'],
                    place_id=place['place_id'],
                    journey=new_journey.j_id
                )
                self.db.add(journey_place)

            self.db.commit()
            logger.info(f"成功儲存 {preference.p_id} 的旅程 {Journey.j_id}")
            return new_journey

        except Exception as e:
            self.db.rollback()
            logger.error(f"儲存旅程失敗 {str(e)}")
            raise

    def get_journey_by_preference(self, preference_id: str) -> Dict[str, Any]:
        """
        根據preference_id獲取旅程詳細資訊

        Args:
            preference_id: Preference的UUID

        Returns:
            Dict[str, Any]: 包含journey資訊和地點安排的字典
        """
        try:
            # 先找到對應的journey
            journey = self.db.query(Journey).filter_by(preference=preference_id).all()
            if not journey:
                return {}
            # FIXME:應抓取該preference的所有journey回傳
            '''
            # 獲取該journey的所有地點安排
            places = self.db.query(PlacesOfTheJourney).filter_by(
                journey=journey.j_id
            ).order_by(PlacesOfTheJourney.place_start_datetime).all()

            return {
                'journey_info': {
                    'j_id': journey.j_id,
                    'j_name': journey.j_name,
                    'city': journey.city,
                    'budget': journey.j_budget
                },
                'places': [{
                    'place_start_datetime': place.place_start_datetime,
                    'place_end_datetime': place.place_end_datetime,
                    'place_id': place.place_id
                } for place in places]
            }
            '''
        except Exception as e:
            logger.error(f"獲取 {preference_id} 的旅程失敗: {str(e)}")
            raise
