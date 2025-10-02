import json
import logging
from typing import Dict, List, Any
import requests
from config import API_KEY, NEARBY_URL

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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
    def __init__(self, api_key: str, nearby_url: str):
        self.api_key = api_key
        self.nearby_url = nearby_url
        self.all_results = []

    def search_nearby_places(self, preference: Dict[str, Any]) -> None:
        """
        執行 nearby search 並儲存所有結果

        Args:
            preference: 搜尋參數字典
        """
        # 設定基本參數
        base_params = {
            'location': preference['location'],
            'radius': preference['radius'],
            'language': 'zh-TW',
            'key': self.api_key
        }

        # 對每個關鍵字執行搜尋
        for type in preference['type']:
            params = base_params.copy()
            params['type'] = type

            # 發出請求
            logger.info(f"搜尋關鍵字: {type}")
            response = make_request(self.nearby_url, params)

            if response and 'results' in response:
                # 儲存所有結果
                self.all_results.extend(response['results'])
                logger.info(f"找到 {len(response['results'])} 個結果")
            else:
                logger.warning(f"關鍵字 {type} 沒有結果")

        # 移除重複的地點 (根據 place_id)
        unique_results = {place['place_id']: place for place in self.all_results}
        self.all_results = list(unique_results.values())

        # 將結果寫入 JSON 檔案
        self.save_results()

    def save_results(self) -> None:
        """將搜尋結果儲存為 JSON 檔案"""
        output_file = 'nearby_search_results.json'
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'total_places': len(self.all_results),
                    'results': self.all_results
                }, f, ensure_ascii=False, indent=2)
            logger.info(f"已將 {len(self.all_results)} 個結果儲存至 {output_file}")
        except Exception as e:
            logger.error(f"儲存結果時發生錯誤: {e}")


def main():
    # 假資料
    preference = {
        'location': '23.4812732, 120.4514065',
        'radius': 4000,
        'type': ['tourist_attraction']
    }

    api = GooglePlacesAPI(API_KEY, NEARBY_URL)
    api.search_nearby_places(preference)


if __name__ == "__main__":
    main()

