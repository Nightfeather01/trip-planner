import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PreferenceValidator:
    @staticmethod
    def validate_form_data(form_data: Dict[str, Any]) -> List[str]:
        """
        驗證表單數據

        Args:
            form_data: 表單數據字典

        Returns:
            List[str]: 錯誤訊息列表，如果沒有錯誤則返回空列表
        """
        if not form_data:
            return ["無效的表單數據"]

        errors = []

        # 驗證必要欄位是否存在
        required_fields = {
            'p_name': '旅行偏好名稱',
            'departure_datetime': '出發時間',
            'return_datetime': '返回時間',
            'daily_depart_time': '每日啟程時間',
            'daily_return_time': '每日返回時間',
            'budget': '預算',
            'travel_mode': '旅遊模式',
            'city': '城市',
            'place_types_keywords': '地點類型和關鍵字'
        }

        # 檢查必要欄位
        for field, field_name in required_fields.items():
            if field not in form_data:
                errors.append(f"請填寫{field_name}")

        # 如果有基本欄位缺失，直接返回錯誤
        if errors:
            return errors

        try:
            # 驗證時間格式和邏輯
            departure = datetime.strptime(form_data['departure_datetime'], '%Y-%m-%dT%H:%M')
            return_time = datetime.strptime(form_data['return_datetime'], '%Y-%m-%dT%H:%M')

            if departure >= return_time:
                errors.append("返回時間必須晚於出發時間")

            # 驗證每日時間
            daily_depart = datetime.strptime(form_data['daily_depart_time'], '%H:%M').time()
            daily_return = datetime.strptime(form_data['daily_return_time'], '%H:%M').time()

            if daily_depart >= daily_return:
                errors.append("每日返回時間必須晚於啟程時間")

            # 驗證預算
            try:
                budget = int(form_data['budget'])
                if budget < 0 or budget > 4:  # 假設預算範圍是0-4
                    errors.append("預算必須在0到4之間")
            except ValueError:
                errors.append("預算必須是有效的數字")

            # 驗證地點類型和關鍵字
            place_types_keywords = form_data.get('place_types_keywords', {})
            if not isinstance(place_types_keywords, dict):
                errors.append("無效的地點類型和關鍵字格式")
            else:
                # 檢查是否至少選擇了一個地點類型
                if not place_types_keywords:
                    errors.append("請至少選擇一個地點類型")
                else:
                    # 驗證每個類型的關鍵字
                    for type_id, keywords in place_types_keywords.items():
                        if not isinstance(keywords, list):
                            errors.append(f"地點類型 {type_id} 的關鍵字格式無效")
                        elif not keywords:
                            errors.append(f"地點類型 {type_id} 需要至少一個關鍵字")

        except ValueError as e:
            errors.append("日期或時間格式無效")
        except Exception as e:
            logger.error(f"表單驗證時發生錯誤: {str(e)}")
            errors.append("表單驗證過程發生錯誤")

        return errors

    @staticmethod
    def _validate_place_types(form_data: Dict[str, Any]) -> bool:
        """驗證place_type=1~8之情形"""
        # 驗證景點類型選擇(place_types=1~6)
        place_types = {
            k: v for k, v in form_data['place_types_keywords'].items()
            if k.isdigit() and 1 <= int(k) <= 6
        }

        # 驗證觀光景點類型選擇(place_types=7)
        tourist_types = form_data['place_types_keywords'].get('7', [])

        # 驗證觀光景點類型選擇(place_types=7)
        food_types = form_data['place_types_keywords'].get('8', [])

        return (1 <= len(place_types) <= 3 and
                5 <= len(tourist_types) <= 10 and
                5 <= len(food_types) <= 10)

    @staticmethod
    def _validate_times(form_data: dict) -> Optional[List[str]]:
        """
        驗證時間相關的欄位

        Args:
            form_data: 包含時間欄位的表單數據字典

        Returns:
            如果驗證失敗，返回錯誤信息列表；如果驗證成功，返回None
        """
        errors = []

        try:
            # 解析時間字符串為datetime對象
            departure_datetime = datetime.strptime(
                form_data['departure_datetime'], '%Y-%m-%dT%H:%M')
            return_datetime = datetime.strptime(
                form_data['return_datetime'], '%Y-%m-%dT%H:%M')
            daily_depart_time = datetime.strptime(
                form_data['daily_depart_time'], '%H:%M').time()
            daily_return_time = datetime.strptime(
                form_data['daily_return_time'], '%H:%M').time()

            # 檢查是否為過去的時間
            current_time = datetime.now()
            if departure_datetime < current_time:
                errors.append('去程時間不可為過去的時間')

            if return_datetime < current_time:
                errors.append('回程時間不可為過去的時間')

            # 檢查回程是否早於去程
            if return_datetime <= departure_datetime:
                errors.append('回程時間必須晚於去程時間')

            # 檢查行程是否超過一週
            max_return_datetime = departure_datetime + timedelta(days=7)
            if return_datetime > max_return_datetime:
                errors.append('行程時間不可超過一週')

            # 檢查每日回程時間是否早於每日出發時間
            if daily_return_time <= daily_depart_time:
                errors.append('每日回程時間必須晚於每日出發時間')

        except ValueError as e:
            errors.append(f'時間格式錯誤: {str(e)}')

        return errors if errors else None
