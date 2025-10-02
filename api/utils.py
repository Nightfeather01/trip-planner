import logging
import requests
from typing import Dict, Any

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
