from flask import session
import logging
from typing import Dict, Any, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def store_journey_data(journey_data: Dict[str, Any]) -> bool:
    """儲存行程資料到 session

    Args:
        journey_data: 行程資料字典

    Returns:
        bool: 是否成功儲存
    """
    try:
        session['journey_data'] = journey_data
        session.modified = True
        return True
    except Exception as e:
        logger.error(f"儲存行程資料失敗: {str(e)}")
        return False


def get_journey_data() -> Optional[Dict[str, Any]]:
    """從 session 取得行程資料"""
    return session.get('journey_data')


def clear_journey_data() -> None:
    """清除 session 中的行程資料"""
    session.pop('journey_data', None)
    session.modified = True