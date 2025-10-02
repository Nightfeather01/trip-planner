import re
from typing import Dict, List, Any, Set, Optional
from datetime import datetime, time, timedelta
import logging
from .utils import make_request

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _validate_place_details_response(response: Dict[str, Any], place_id: str) -> bool:
    """驗證地點詳細資訊的回應是否有效"""
    if not response or response.get('status') != 'OK':
        logger.error(f"地點 {place_id} 的API請求失敗")
        return False

    result = response.get('result', {})

    # 檢查必要欄位
    required_fields = ['geometry', 'name', 'formatted_address']
    if not all(field in result for field in required_fields):
        logger.error(f"地點 {place_id} 缺少必要欄位")
        return False

    # 檢查位置資訊
    if not all(key in result.get('geometry', {}).get('location', {})
               for key in ['lat', 'lng']):
        logger.error(f"地點 {place_id} 缺少位置資訊")
        return False

    # 檢查營業時間
    if not all(key in result.get('opening_hours', {})
               for key in ['periods']):
        logger.warning(f"地點 {place_id} 缺少營業時間資訊")
        return False

    return True


def _is_valid_place(place: Dict[str, Any]) -> bool:
    """驗證地點是否符合條件

    過濾條件:
    1. 必須有評分和評分總數
    2. 評分總數需達到500以上
    3. 排除已知連鎖店品牌
    """
    try:
        # 檢查必要評分欄位
        if not all(key in place for key in ['rating', 'user_ratings_total']):
            return False

        # 檢查評分數量門檻
        if place['user_ratings_total'] < 500:
            return False

        # 取得地點名稱，轉換為大寫以進行不區分大小寫的比對
        name = place.get('name', '').upper()

        # 連鎖店品牌名稱列表
        chain_patterns = [
            # 便利商店
            r'7-ELEVEN|統一超商|全家|FAMILY MART|萊爾富|OK超商|美廉社',
            # 速食連鎖
            r'麥當勞|MCDONALD|肯德基|KFC|漢堡王|BURGER KING|頂呱呱|德克士|摩斯漢堡|MOS BURGER',
            # 連鎖咖啡
            r'星巴克|STARBUCKS|路易莎|LOUISA|CAMA|丹堤|西雅圖|ZEN|85度C',
            # 連鎖百貨/量販
            r'家樂福|CARREFOUR|大潤發|愛買|全聯|COSTCO|好市多|大樂|DOLLAR|特力屋|B&Q',
            # 連鎖餐飲
            r'必勝客|PIZZA HUT|達美樂|DOMINO|拿坡里|subway|賽百味|胖老爹|丹丹漢堡|21世紀風味館|西堤|品田牧場',
            # 連鎖飲料
            r'清心福全|可不可熟成|COMEBUY|一芳|50嵐|珍煮丹|迷客夏|MILKSHA|鮮茶道|茶湯會|大苑子',
            # 連鎖美式餐廳
            r'TGI FRIDAY|FRIDAY|CHILI\'S',
            # 連鎖火鍋
            r'海底撈|陶板屋|王品|hot pot|涮涮鍋|石二鍋|六扇門|築間',
            # 其他連鎖
            r'無印良品|MUJI|屈臣氏|WATSON|寶雅|美華泰|小七|小七景點|7-11'
        ]

        # 檢查地點名稱是否匹配任何連鎖店模式
        if any(re.search(pattern, name) for pattern in chain_patterns):
            return False

        return True

    except Exception as e:
        logger.error(f"驗證地點時發生錯誤: {str(e)}")
        return False


class GooglePlacesAPI:
    def __init__(self, api_key: str, nearby_url: str, detail_url: str):
        self.api_key = api_key
        self.nearby_url = nearby_url
        self.detail_url = detail_url

    def get_nearby_places(self, params: Dict[str, Any]) -> Set[str]:
        """執行 Nearby Search 請求並返回符合條件的地點ID集合"""
        base_params = {
            'location': params['location'],
            'radius': params['radius'],
            'key': self.api_key
        }

        if 'type' in params:
            base_params['type'] = params['type']
        if 'keyword' in params:
            base_params['keyword'] = params['keyword']

        try:
            response = make_request(self.nearby_url, base_params)
            if not response or 'status' not in response:
                logger.error("Nearby Search 請求失敗: 無效的回應")
                return set()

            if response['status'] != 'OK':
                if response['status'] == 'ZERO_RESULTS':
                    logger.info(
                        f"Nearby Search 沒有找到結果 (type: {params.get('type')}, keyword: {params.get('keyword')})")
                else:
                    logger.error(f"Nearby Search 請求失敗: {response['status']}")
                return set()

            valid_places = {
                place['place_id']
                for place in response.get('results', [])
                if _is_valid_place(place)
            }

            logger.info(f"Nearby Search 找到 {len(valid_places)} 個有效地點")
            return valid_places

        except Exception as e:
            logger.error(f"執行 Nearby Search 時發生錯誤: {str(e)}")
            return set()

    def get_place_details(self, place_id: str) -> Optional[Dict[str, Any]]:
        """獲取地點的詳細資訊"""
        # 所需參數
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
            if not _validate_place_details_response(response, place_id):
                return None

            return response

        except Exception as e:
            logger.error(f"獲取地點 {place_id} 詳細資訊時發生錯誤: {str(e)}")
            return None

    @staticmethod
    def parse_opening_hours(periods: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """解析營業時間格式"""
        result = []

        # 處理24小時營業
        if (len(periods) == 1 and
                periods[0].get('open', {}).get('time') == '0000' and
                'close' not in periods[0]):
            return [{
                'day_of_week': day,
                'open_time': time(0, 0),
                'close_time': time(23, 59)
            } for day in range(7)]

        # 處理一般營業時間
        for period in periods:
            day = period.get('open', {}).get('day')
            open_time_str = period.get('open', {}).get('time')

            if not all([day is not None, open_time_str]):
                continue

            open_time = datetime.strptime(open_time_str, '%H%M').time()

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
        """檢查地點資訊是否需要更新"""
        return datetime.now() - last_updated > timedelta(days=180)
