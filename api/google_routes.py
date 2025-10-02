from typing import Dict, Any, List
import logging
from datetime import datetime, timedelta
from .utils import make_request

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GoogleRoutesAPI:
    def __init__(self, api_key: str, directions_url: str):
        self.api_key = api_key
        self.directions_url = directions_url

    def get_route_info(self, journey: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Get detailed route information between places using Google Directions API

        Args:
            journey: List of journey places with their details and timing

        Returns:
            Dict containing route details and transit information
        """
        try:
            if not journey or len(journey) < 2:
                logger.warning("Journey must contain at least 2 places")
                return {'status': 'ERROR', 'message': 'Not enough places in journey'}

            routes_data = []
            current_day = None

            # 處理每個行程點之間的路線
            for i in range(len(journey) - 1):
                current_place = journey[i]
                next_place = journey[i + 1]

                # 確保時間格式的一致性
                current_datetime = (current_place['place_end_datetime']
                                    if isinstance(current_place['place_end_datetime'], datetime)
                                    else datetime.strptime(current_place['place_end_datetime'], '%Y-%m-%d %H:%M:%S'))

                next_datetime = (next_place['place_start_datetime']
                                 if isinstance(next_place['place_start_datetime'], datetime)
                                 else datetime.strptime(next_place['place_start_datetime'], '%Y-%m-%d %H:%M:%S'))

                # 如果是不同天的行程，跳過路線規劃
                if current_datetime.date() != next_datetime.date():
                    continue

                # 驗證座標
                if not all(k in current_place for k in ['lat', 'lng']) or \
                        not all(k in next_place for k in ['lat', 'lng']):
                    logger.error(f"Missing coordinates for places at index {i} or {i + 1}")
                    continue

                # 準備API請求參數
                params = {
                    'origin': f"{current_place['lat']},{current_place['lng']}",
                    'destination': f"{next_place['lat']},{next_place['lng']}",
                    'mode': 'transit',
                    'transit_mode': 'rail',
                    'language': 'zh-TW',
                    'departure_time': int(current_datetime.timestamp()),
                    'key': self.api_key
                }

                # 發送API請求
                response = make_request(self.directions_url, params)

                if not response or response.get('status') != 'OK':
                    logger.error(f"API error: {response.get('status', 'Unknown error')}")
                    continue

                route_info = self._process_route_response(
                    response,
                    current_place,
                    next_place,
                    current_datetime
                )

                if route_info:
                    routes_data.append(route_info)

            return {
                'status': 'OK',
                'routes_data': routes_data
            }

        except Exception as e:
            logger.error(f"Error getting route information: {str(e)}")
            return {
                'status': 'ERROR',
                'message': f'Failed to get route information: {str(e)}'
            }

    def _process_route_response(self, response: Dict[str, Any],
                                current_place: Dict[str, Any],
                                next_place: Dict[str, Any],
                                departure_time: datetime) -> Dict[str, Any]:
        """處理路線回應數據"""
        try:
            route = response['routes'][0]
            leg = route['legs'][0]

            # 獲取詳細的交通方式信息
            steps = []
            for step in leg['steps']:
                step_info = {
                    'travel_mode': step['travel_mode'],
                    'duration': step['duration']['text'],
                    'duration_value': step['duration']['value'],
                    'html_instructions': step.get('html_instructions', ''),
                    'distance': step['distance']['text'],
                }

                if step['travel_mode'] == 'TRANSIT':
                    transit_details = step['transit_details']
                    step_info.update({
                        'transit_type': transit_details['line'].get('vehicle', {}).get('type', ''),
                        'line_name': transit_details['line'].get('name', ''),
                        'departure_stop': transit_details['departure_stop']['name'],
                        'arrival_stop': transit_details['arrival_stop']['name'],
                        'departure_time': transit_details['departure_time']['text'],
                        'arrival_time': transit_details['arrival_time']['text']
                    })

                steps.append(step_info)

            # 計算到達時間並轉換為字符串格式
            arrival_time = departure_time + timedelta(seconds=leg['duration']['value'])

            return {
                'origin_id': current_place['place_id'],
                'destination_id': next_place['place_id'],
                'departure_time': departure_time.strftime('%Y-%m-%d %H:%M:%S'),
                'arrival_time': arrival_time.strftime('%Y-%m-%d %H:%M:%S'),
                'total_duration': leg['duration']['text'],
                'total_duration_value': leg['duration']['value'],
                'total_distance': leg['distance']['text'],
                'steps': steps,
                'overview_polyline': route['overview_polyline']['points']
            }

        except Exception as e:
            logger.error(f"Error processing route response: {str(e)}")
            return None