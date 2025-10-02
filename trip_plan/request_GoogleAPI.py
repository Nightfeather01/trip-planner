import json
import os
import re
from datetime import datetime, time, timedelta
from typing import Dict, List, Any, Optional, Set
import requests
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def make_request(url: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """發送 HTTP 請求並處理回應"""
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"請求失敗: {e}")
        return {}
    except ValueError as e:
        logger.error(f"解析 JSON 出錯: {e}")
        return {}


class GooglePlacesAPI:
    def __init__(self, api_key: str, nearby_url: str, detail_url: str):
        self.api_key = api_key
        self.nearby_url = nearby_url
        self.detail_url = detail_url

    def get_nearby_places(self, params: Dict[str, Any]) -> Set[str]:
        """執行 Nearby Search 請求"""
        base_params = {
            'location': params['location'],
            'radius': params['radius'],
            'key': self.api_key
        }

        # 添加可選參數
        if 'type' in params:
            base_params['type'] = params['type']
        if 'keyword' in params:
            base_params['keyword'] = params['keyword']

        try:
            response = make_request(self.nearby_url, base_params)
            if not response or 'status' not in response:
                logger.error(f"Nearby Search 請求失敗: 無效的回應")
                return set()

            if response['status'] != 'OK':
                if response['status'] == 'ZERO_RESULTS':
                    logger.info(
                        f"Nearby Search 沒有找到結果 (type: {params.get('type')}, keyword: {params.get('keyword')})")
                else:
                    logger.error(
                        f"Nearby Search 請求失敗: {response['status']} - {response.get('error_message', '未知錯誤')}")
                return set()

            if 'results' not in response:
                logger.error("Nearby Search 回應缺少 results 欄位")
                return set()

            # 過濾結果
            valid_places = set()
            for place in response['results']:
                if self._is_valid_place(place):
                    valid_places.add(place['place_id'])
                    logger.debug(f"找到有效地點: {place['place_id']} ({place.get('name', '未知')})")

            logger.info(
                f"Nearby Search 找到 {len(valid_places)} 個有效地點 (type: {params.get('type')}, keyword: {params.get('keyword')})")
            return valid_places

        except Exception as e:
            logger.error(f"執行 Nearby Search 時發生錯誤: {str(e)}")
            return set()

    def get_place_details(self, place_id: str) -> Optional[Dict[str, Any]]:
        """獲取地點詳細資訊"""
        params = {
            'place_id': place_id,
            'fields': ('place_id,geometry,name,formatted_address,opening_hours,'
                       'types,formatted_phone_number,wheelchair_accessible_entrance,'
                       'business_status,price_level,rating,user_ratings_total'),
            'language': 'zh-TW',
            'key': self.api_key
        }

        try:
            response = make_request(self.detail_url, params)

            # 檢查API回應
            if not response:
                logger.error(f"地點 {place_id} 的API請求沒有回應")
                return None

            if response.get('status') != 'OK':
                logger.error(
                    f"地點 {place_id} 的API請求失敗: {response.get('status')} - {response.get('error_message', '未知錯誤')}")
                return None

            if 'result' not in response:
                logger.error(f"地點 {place_id} 的API回應缺少 result 欄位")
                return None

            result = response['result']

            # 檢查必要欄位
            required_fields = ['geometry', 'name', 'formatted_address']
            missing_fields = [field for field in required_fields if field not in result]
            if missing_fields:
                logger.error(f"地點 {place_id} 缺少必要欄位: {', '.join(missing_fields)}")
                return None

            # 檢查位置資訊
            if ('location' not in result['geometry'] or
                    'lat' not in result['geometry']['location'] or
                    'lng' not in result['geometry']['location']):
                logger.error(f"地點 {place_id} 缺少位置資訊")
                return None

            # 檢查營業時間資訊
            if ('opening_hours' not in result or
                    'periods' not in result['opening_hours']):
                logger.warning(f"地點 {place_id} ({result.get('name', '未知')}) 缺少營業時間資訊")
                return None

            logger.info(f"成功獲取地點詳細資訊: {place_id} ({result.get('name', '未知')})")
            return response

        except Exception as e:
            logger.error(f"獲取地點 {place_id} 詳細資訊時發生錯誤: {str(e)}")
            return None

    def _is_valid_place(self, place: Dict[str, Any]) -> bool:
        """驗證地點是否符合條件"""
        try:
            # 檢查必要欄位
            if not all(key in place for key in ['rating', 'user_ratings_total']):
                logger.debug(f"地點 {place.get('place_id', '未知')} 缺少評分資訊")
                return False

            # 評分數量門檻
            if place['user_ratings_total'] < 100:  # 降低門檻以便測試
                logger.debug(f"地點 {place.get('place_id', '未知')} 評分數量不足")
                return False

            # 嘗試過濾連鎖店
            name = place.get('name', '')
            chain_patterns = [
                r'7-ELEVEN|全家|萊爾富|OK超商',
                r'麥當勞|肯德基|漢堡王',
                r'星巴克|路易莎|cama',
                r'家樂福|大潤發|愛買',
            ]

            for pattern in chain_patterns:
                if re.search(pattern, name, re.IGNORECASE):
                    logger.debug(f"地點 {place.get('place_id', '未知')} 被識別為連鎖店")
                    return False

            return True

        except Exception as e:
            logger.error(f"驗證地點時發生錯誤: {str(e)}")
            return False
    def parse_opening_hours(self, periods: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        解析營業時間

        Args:
            periods: Google API 回傳的營業時間週期列表

        Returns:
            解析後的營業時間列表，每個元素包含 day_of_week, open_time, close_time
        """
        result = []

        # 處理24小時營業的情況
        if len(periods) == 1 and periods[0].get('open', {}).get('time') == '0000' and 'close' not in periods[0]:
            for day in range(7):
                result.append({
                    'day_of_week': day,
                    'open_time': time(0, 0),
                    'close_time': time(23, 59)
                })
            return result

        # 處理一般營業時間
        for period in periods:
            day = period.get('open', {}).get('day')
            if day is None:
                continue

            open_time_str = period.get('open', {}).get('time')
            if not open_time_str:
                continue

            # 解析開始時間
            open_time = datetime.strptime(open_time_str, '%H%M').time()

            # 解析結束時間
            close_time = None
            if 'close' in period:
                close_time_str = period['close'].get('time')
                if close_time_str:
                    close_time = datetime.strptime(close_time_str, '%H%M').time()

            if close_time:
                result.append({
                    'day_of_week': day,
                    'open_time': open_time,
                    'close_time': close_time
                })

        return result

    @staticmethod
    def is_place_info_outdated(last_updated: datetime) -> bool:
        """
        檢查地點資訊是否需要更新

        Args:
            last_updated: 最後更新時間

        Returns:
            是否需要更新
        """
        six_months = timedelta(days=180)
        return datetime.now() - last_updated > six_months


'''
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# 發出請求
def make_request(url: str, params: Dict[str, Any]) -> Dict[str, Any]:
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"請求失敗: {e}")
        return {}
    except ValueError as e:
        logger.error(f"解析 JSON 出錯: {e}")
        return {}


class GooglePlacesAPI:
    def __init__(self, api_key: str, nearby_url: str, detail_url: str):
        self.api_key = api_key
        self.nearby_url = nearby_url
        self.detail_url = detail_url

    def get_nearby_places(self, preference: Dict[str, Any]) -> List[str]:
        # 設定基本參數
        base_nearby_request_paras = {
            'location': preference['location'],
            'radius': preference['radius'],
            'key': self.api_key
        }

        # 儲存所有nearby request參數
        all_nearby_request_paras = []

        # 對每個keyword建立一個請求參數
        for keyword in preference['keyword']:
            nearby_request_paras = base_nearby_request_paras.copy()
            nearby_request_paras['keyword'] = keyword
            all_nearby_request_paras.append(nearby_request_paras)

        print(all_nearby_request_paras)
        # 儲存所有nearby search結果，20cases/request
        all_nearby_responses = []
        for nearby_request in all_nearby_request_paras:
            # 發出請求
            nearby_response = make_request(self.nearby_url, nearby_request)
            if nearby_response and 'results' in nearby_response:
                # 儲存place_id
                all_nearby_responses.extend([place['place_id'] for place in nearby_response['results']])

        # 回傳所有搜尋到的place_id
        print(all_nearby_responses)
        return all_nearby_responses

    # 利用all_nearby_responses的所有place_id，進行place_details request
    def get_place_details(self, place_id: str) -> Dict[str, Any]:
        detail_request_paras = {
            'place_id': place_id,
            'fields': 'place_id,geometry,name,formatted_address,opening_hours,types,formatted_phone_number,wheelchair_accessible_entrance,business_status,price_level,rating,user_ratings_total',
            'language': 'zh-TW',
            'key': self.api_key
        }
        return make_request(self.detail_url, detail_request_paras)

    # 創建營業時間的字典以儲存營業時間
    @staticmethod
    def parse_opening_hours(periods: List[Dict[str, Any]]) -> Dict[str, List[time]]:
        opening_hours = {}
        if len(periods) == 1 and periods[0]['open']['time'] == '0000' and 'close' not in periods[0]:
            for day in range(7):
                opening_hours[str(day)] = [time(0, 0), time(23, 59)]
        else:
            for day in range(7):
                day_periods = [period for period in periods if period['open']['day'] == day]
                opening_hours[str(day)] = []
                for period in day_periods:
                    open_time = datetime.strptime(period['open']['time'], '%H%M').time()
                    opening_hours[str(day)].append(open_time)
                    if 'close' in period:
                        close_time = datetime.strptime(period['close']['time'], '%H%M').time()
                        opening_hours[str(day)].append(close_time)
        return opening_hours


    # 處理回傳資料
    @staticmethod
    def parse_opening_hours(periods: List[Dict[str, Any]]) -> Dict[str, List[time]]:
        opening_hours = {}
        if len(periods) == 1 and periods[0]['open']['time'] == '0000' and 'close' not in periods[0]:
            for day in range(7):
                opening_hours[str(day)] = [time(0, 0), time(23, 59)]
        else:
            for day in range(7):
                day_periods = [period for period in periods if period['open']['day'] == day]
                opening_hours[str(day)] = []
                for period in day_periods:
                    open_time = datetime.strptime(period['open']['time'], '%H%M').time()
                    opening_hours[str(day)].append(open_time)
                    if 'close' in period:
                        close_time = datetime.strptime(period['close']['time'], '%H%M').time()
                        opening_hours[str(day)].append(close_time)
        return opening_hours

    def process_place_details(self, place_details: Dict[str, Any]) -> Dict[str, Any]:
        if 'result' not in place_details:
            return {}

        result = place_details['result']
        if 'opening_hours' not in result or 'periods' not in result['opening_hours']:
            logger.warning(f"place_id: {result['place_id']} 缺少營業時間資訊，跳過")
            return {}

        file_path = 'all_place_details.json'

        file_empty = not os.path.exists(file_path) or os.path.getsize(file_path) == 0

        if file_empty:
            json_content = [result]
        else:
            with open(file_path, 'r', encoding='utf-8') as fp:
                content = fp.read()
                if not content.startswith('[') or not content.endswith(']'):
                    raise ValueError("JSON 檔案格式不正確")

                json_content = json.loads(content)
                if not isinstance(json_content, list):
                    raise ValueError("JSON 檔案不包含陣列")

                new_place_id = result.get('place_id')
                updated = False
                for i, place in enumerate(json_content):
                    if place.get('place_id') == new_place_id:
                        json_content[i] = result
                        updated = True
                        logger.info(f"已更新 place_id: {new_place_id} 的資訊")
                        break

                if not updated:
                    json_content.append(result)
                    logger.info(f"已添加新的 place_id: {new_place_id}")

        with open(file_path, 'w', encoding='utf-8') as fp:
            json.dump(json_content, fp, ensure_ascii=False, indent=2)

        place_details_field = {
            'place_id': result['place_id'],
            'lat': result['geometry']['location']['lat'],
            'lng': result['geometry']['location']['lng'],
            'name': result['name'],
            'formatted_address': result['formatted_address'],
            'types': result['types'],
            'formatted_phone_number': result.get('formatted_phone_number'),
            'wheelchair_accessible_entrance': result.get('wheelchair_accessible_entrance', False),
            'business_status': result['business_status'],
            'price_level': result.get('price_level'),
            'rating': result.get('rating'),
            'user_ratings_total': result.get('user_ratings_total'),
            'opening_hours': self.parse_opening_hours(result['opening_hours']['periods']),
            'stay_time': time(1, 30)
        }

        return {}
'''
