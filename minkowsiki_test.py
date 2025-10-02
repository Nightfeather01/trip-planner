

from geopy.distance import geodesic
from math import radians, sin, cos, sqrt, atan2

def minkowski_distance(lng1, lat1, lng2, lat2, p=1.0):
    # 將經緯度從度轉換為弧度
    lng1, lat1, lng2, lat2 = map(radians, [lng1, lat1, lng2, lat2])

    # Minkowski距離的計算
    d_lat = abs(lat2 - lat1)
    d_lng = abs(lng2 - lng1)
    distance = (d_lat ** p + d_lng ** p) ** (1 / p)

    # 假設地球半徑為6371公里
    earth_radius_km = 6371

    # 將弧度轉換為實際距離
    path_length = earth_radius_km * distance
    return path_length

lng1, lat1 = 125.15769, 22.28552  # Point 1
lng2, lat2 = 114.15951, 22.28596  # Point 2

distance_strightline = geodesic((lat1, lng1), (lat2, lng2)).kilometers
print(distance_strightline)

distance = minkowski_distance(lng1, lat1, lng2, lat2, p=45)
print(f"The estimated path length is {distance:.2f} km")