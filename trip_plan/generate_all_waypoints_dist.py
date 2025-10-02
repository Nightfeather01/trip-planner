import logging
from itertools import combinations

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def calculate_dist(place1, place2, p):
    lat1, lng1 = place1['lat'], place1['lng']
    lat2, lng2 = place2['lat'], place2['lng']

    d_lat = abs(lat2 - lat1)
    d_lng = abs(lng2 - lng1)
    distance = (d_lat ** p + d_lng ** p) ** (1 / p)

    earth_radius_km = 6371

    waypoint_distance = earth_radius_km * distance
    return {'distance': waypoint_distance}


class GenerateAllWaypointsDist:
    # 初始化
    def __init__(self, all_place_details_subset: list[dict], p: float):
        if len(all_place_details_subset) < 2:
            logger.error(f"place detail結果僅為{len(all_place_details_subset)}個，無法計算距離")
        else:
            self.all_place_details_subset = all_place_details_subset
        self.p = p

    def generate_all_waypoints_dist(self):
        all_waypoints_dist = []
        for (place1, place2) in combinations(self.all_place_details_subset, 2):
            waypoint = {
                'place_id1': place1['place_id'],
                'place_id2': place2['place_id']
            }
            waypoint.update(calculate_dist(place1, place2, self.p))
            all_waypoints_dist.append(waypoint)
        return all_waypoints_dist
