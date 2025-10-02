from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple
import logging
from flask import render_template, flash
from extensions import db
from werkzeug.datastructures import ImmutableMultiDict
from models import Keywords, CityInfosMapping, UserInfos

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PreferenceFormService:
    """處理表單相關的服務"""

    def __init__(self, db_session: db):
        self.db = db_session

    def pre_process_form_data(self, form: ImmutableMultiDict) -> Dict[str, Any]:
        """
        處理提交的表單數據

        Args:
            form: Flask request.form 對象

        Returns:
            Dict: 處理後的表單數據
        """
        try:
            # 處理景點類型和關鍵字
            place_types_keywords = self._process_place_types_keywords(form)

            # 整理基本表單數據
            form_data = {
                'p_name': form.get('tripName'),
                'departure_datetime': form.get('startTime'),
                'return_datetime': form.get('endTime'),
                'daily_depart_time': form.get('dailyStartTime'),
                'daily_return_time': form.get('dailyEndTime'),
                'budget': int(form.get('budget')),
                'travel_mode': form.get('travelMode') == 'fast',
                'city': int(form.get('city')),
                'price_level_weight': float(form.get('priceLevelWeight', 5.0)),
                'rating_weight': float(form.get('ratingWeight', 5.0)),
                'user_rating_total_weight': float(form.get('userRatingTotalWeight', 5.0)),
                'ngen': int(form.get('ngen', 200)),
                'place_types_keywords': place_types_keywords
            }

            # 處理城市位置資訊
            city_info = self._get_city_location(form_data['city'])
            if not city_info:
                flash({'message': '找不到指定的城市資訊'}, 'error')
                return None

            # 將市政廳位置資訊加入form_data
            form_data.update({
                'city_hall_lat': city_info.city_hall_lat,
                'city_hall_lng': city_info.city_hall_lng
            })

            logger.info(f"表單數據處理完成: {form_data}")
            return form_data

        except Exception as e:
            logger.error(f"處理表單數據時發生錯誤: {str(e)}")
            raise

    def post_process_form_data(self, form_data, preference_uuid=None):
        """處理表單數據的格式"""
        # 轉換日期時間格式
        departure = datetime.strptime(form_data['departure_datetime'], '%Y-%m-%dT%H:%M')
        return_time = datetime.strptime(form_data['return_datetime'], '%Y-%m-%dT%H:%M')
        form_data['departure_datetime'] = departure.strftime('%Y年%m月%d日%H:%M')
        form_data['return_datetime'] = return_time.strftime('%Y年%m月%d日%H:%M')

        # 轉換城市ID為城市名稱
        city_info = db.session.query(CityInfosMapping).filter_by(c_id=form_data['city']).first()
        if city_info:
            form_data['city'] = city_info.c_chinese

        # 處理關鍵字列表
        for type_id, keywords in form_data['place_types_keywords'].items():
            # 移除重複元素
            keywords = list(dict.fromkeys(keywords))

            # 特殊處理type 7和8
            if type_id == '7' and '觀光景點' in keywords:
                keywords.remove('觀光景點')
            elif type_id == '8' and '餐廳' in keywords:
                keywords.remove('餐廳')

            form_data['place_types_keywords'][type_id] = keywords

        # 添加UUID
        if preference_uuid:
            form_data['uuid'] = preference_uuid

        return form_data

    def _process_place_types_keywords(self, form: ImmutableMultiDict) -> Dict[str, List[str]]:
        """
        處理景點類型和關鍵字

        Returns:
            Dict[str, List[str]]: 景點類型ID對應的關鍵字列表
        """
        place_types_keywords = {}

        try:
            # 處理基本景點類型 (t_id 1-6)
            self._process_basic_place_types(form, place_types_keywords)

            # 處理觀光景點類型 (t_id 7)
            self._process_tourist_types(form, place_types_keywords)

            # 處理食物類型 (t_id 8)
            self._process_food_types(form, place_types_keywords)

            return place_types_keywords

        except Exception as e:
            logger.error(f"處理景點類型和關鍵字時發生錯誤: {str(e)}")
            raise

    def _process_basic_place_types(self, form: ImmutableMultiDict,
                                   result: Dict[str, List[str]]) -> None:
        """處理基本景點類型 (t_id 1-6)"""
        selected_types = form.getlist('placeTypes[]')
        for type_id in selected_types:
            # 獲取基本關鍵字
            keyword = self.db.query(Keywords).filter_by(k_id=int(type_id)).first()
            if keyword:
                result[type_id] = [keyword.k_name]

                # 處理額外關鍵字
                extra_keywords = form.get(f'placeTypeKeywords_{type_id}', '').strip()
                if extra_keywords:
                    result[type_id].extend(
                        [kw.strip() for kw in extra_keywords.split(',') if kw.strip()]
                    )

    def _process_tourist_types(self, form: ImmutableMultiDict,
                               result: Dict[str, List[str]]) -> None:
        """處理觀光景點類型 (t_id 7)"""
        tourist_types = form.getlist('touristTypes[]')
        if tourist_types:
            # 添加基本觀光景點關鍵字
            keyword = self.db.query(Keywords).filter_by(k_name='觀光景點').first()
            tourist_keywords = [keyword.k_name] if keyword else []

            # 添加選擇的觀光景點類型
            for k_id in tourist_types:
                keyword = self.db.query(Keywords).filter_by(k_id=int(k_id)).first()
                if keyword:
                    tourist_keywords.append(keyword.k_name)

            # 添加額外的觀光景點關鍵字
            extra_tourist = form.get('touristKeywords', '').strip()
            if extra_tourist:
                tourist_keywords.extend(
                    [kw.strip() for kw in extra_tourist.split(',') if kw.strip()]
                )

            result['7'] = tourist_keywords

    def _process_food_types(self, form: ImmutableMultiDict,
                            result: Dict[str, List[str]]) -> None:
        """處理食物類型 (t_id 8)"""
        food_types = form.getlist('foodTypes[]')
        if food_types:
            # 添加基本餐廳關鍵字
            keyword = self.db.query(Keywords).filter_by(k_name='餐廳').first()
            food_keywords = [keyword.k_name] if keyword else []

            # 添加選擇的食物類型
            for k_id in food_types:
                keyword = self.db.query(Keywords).filter_by(k_id=int(k_id)).first()
                if keyword:
                    food_keywords.append(keyword.k_name)

            # 添加額外的食物關鍵字
            extra_food = form.get('foodKeywords', '').strip()
            if extra_food:
                food_keywords.extend(
                    [kw.strip() for kw in extra_food.split(',') if kw.strip()]
                )

            result['8'] = food_keywords

    def _get_city_location(self, city_id: str) -> Optional[CityInfosMapping]:
        """
        獲取城市位置資訊

        Args:
            city_id: 城市ID

        Returns:
            Optional[CityInfosMapping]: 城市資訊對象，如果找不到則返回None
        """
        try:
            return self.db.query(CityInfosMapping).filter(
                CityInfosMapping.c_id == int(city_id)
            ).first()
        except Exception as e:
            logger.error(f"獲取城市位置資訊時發生錯誤: {str(e)}")
            return None

    def render_home_page(self, form_data: Optional[Dict[str, Any]] = None) -> str:
        """
        渲染首頁

        Args:
            form_data: 可選的表單數據，用於回填表單

        Returns:
            str: 渲染後的HTML
        """
        try:
            # 獲取前6種景點類型
            place_types = self.db.query(Keywords).filter(
                Keywords.k_id <= 6
            ).all()

            # 獲取觀光景點關鍵字
            tourist_keywords = self.db.query(Keywords).filter(
                Keywords.place_types == 7,
                Keywords.k_id >= 33,
                Keywords.k_id <= 58
            ).all()

            # 獲取食物關鍵字
            food_keywords = self.db.query(Keywords).filter(
                Keywords.place_types == 8,
                Keywords.k_id >= 9,
                Keywords.k_id <= 32
            ).all()

            # 獲取城市資訊
            city_infos = self.db.query(CityInfosMapping).all()

            return render_template(
                'home.html',
                form_data=form_data,
                place_types=place_types,
                tourist_keywords=tourist_keywords,
                food_keywords=food_keywords,
                city_infos=city_infos
            )

        except Exception as e:
            logger.error(f"渲染首頁時發生錯誤: {str(e)}")
            raise


class UserFormService:
    """處理用戶表單相關的服務"""

    @staticmethod
    def validate_login_form(form_data: Dict[str, str]) -> Tuple[bool, Optional[str]]:
        """
        驗證登入表單數據

        Returns:
            Tuple[bool, Optional[str]]: (是否有效, 錯誤信息)
        """
        try:
            # 檢查必要欄位
            if not all(key in form_data for key in ['account', 'password']):
                return False, "請填寫所有必要欄位"

            account = form_data['account'].strip()
            password = form_data['password'].strip()

            # 驗證長度限制
            if len(account) > 16 or len(password) > 16:
                return False, "帳號和密碼長度不可超過16個字元"

            if len(account) == 0 or len(password) == 0:
                return False, "帳號和密碼不可為空"

            return True, None

        except Exception as e:
            logger.error(f"驗證登入表單時發生錯誤: {str(e)}")
            return False, "表單驗證發生錯誤"

    @staticmethod
    def validate_register_form(form_data: Dict[str, str]) -> Tuple[bool, Optional[str]]:
        """
        驗證註冊表單數據
        """
        try:
            # 檢查所有必要欄位是否存在且不為空
            required_fields = ['nickname', 'account', 'password', 'confirm_password']
            if not all(form_data.get(key) for key in required_fields):
                return False, "請填寫所有必要欄位"

            # 清理並驗證數據
            nickname = form_data['nickname'].strip()
            account = form_data['account'].strip()
            password = form_data['password']
            confirm_password = form_data['confirm_password']

            # 驗證長度限制
            if len(nickname) > 16:
                return False, "暱稱不可超過16個字元"
            if len(account) > 16:
                return False, "帳號不可超過16個字元"
            if len(password) > 16:
                return False, "密碼不可超過16個字元"

            # 驗證非空
            if not all([nickname, account, password, confirm_password]):
                return False, "所有欄位都不能為空"

            # 驗證密碼匹配
            if password != confirm_password:
                return False, "兩次輸入的密碼不匹配"

            # 驗證帳號是否已存在
            existing_user = db.session.query(UserInfos).filter_by(account=account).first()
            if existing_user:
                return False, "此帳號已被註冊"

            return True, None

        except Exception as e:
            logger.error(f"驗證註冊表單時發生錯誤: {str(e)}")
            return False, "表單驗證發生錯誤"