import numpy as np
import json
import pandas as pd
from geopy.distance import geodesic
from itertools import combinations
from typing import Dict, Set, FrozenSet, List, Tuple, Any
from core.generate_initial_trip import Attraction

from datetime import datetime, timedelta
from abc import ABC, abstractmethod


class Place:

    def __init__(self, place_id: str, lat: float, lng: float, open_time: str,
                 close_time: str, category: list[str], price_level: int,
                 rating, user_rating_totals):
        self.place_id: str = place_id
        self.lat: float = lat
        self.lng: float = lng
        self.open_time: str = open_time
        self.close_time: str = close_time
        self.category: list[str] = category
        self.price_level: int = price_level
        self.rating = rating
        self.user_rating_totals = user_rating_totals


class BaseWayPointManager(ABC):
    '''
    def __init__(self):
        self.places: List[Place] = []
    '''

    def __parse_places(self):
        pass

    def read(self):
        pass


class DistanceCalculator():

    def __init__(self, places: list[Place]):
        self.waypoint_distances: Dict[FrozenSet[str], float] = {}
        self.waypoint_durations: Dict[FrozenSet[str], float] = {}
        self.all_waypoints_set: Set[
            list[str]] = set()  # Fix: not sure about the type
        self.places: list[Place] = places

    def __calculateDistance(self, fixed_speed: int = 60):
        for (place1, place2) in combinations(self.places, 2):
            distance = geodesic((place1.lat, place1.lng),
                                (place2.lat, place2.lng)).kilometers
            duration = distance / fixed_speed

            place_ids = frozenset([place1.place_id, place2.place_id])
            self.waypoint_distances[place_ids] = distance
            self.waypoint_durations[place_ids] = duration
            self.all_waypoints_set.update([place1.place_id, place2.place_id])

    def run(self):
        self.__calculateDistance()
        return self.waypoint_distances, self.waypoint_durations, self.all_waypoints_set


def time_to_datetime(time: str) -> datetime:
    return datetime.strptime(time, '%H:%M')


def to_attraction(place: Place, stay_time=1.5) -> Attraction:
    return Attraction(place.place_id,
                      place.open_time,
                      place.close_time,
                      stay_time=stay_time)  # TODO: add stay time


def to_list_attraction(places: list[Place],
                       stay_time: float) -> list[Attraction]:
    return [to_attraction(place, stay_time) for place in places]


class WaypointManager(BaseWayPointManager):

    def __init__(self, file_path: str, stay_time: float):
        # self.waypoint_distances: Dict[FrozenSet[str], float] = {}
        # self.waypoint_durations: Dict[FrozenSet[str], float] = {}
        # self.all_waypoints_set: Set[list[str]] = set()  # Fix: not sure about the type
        self.places: List[Place] = []
        self.file_path = file_path
        self.stay_time = stay_time

    def read(self):
        # Load JSON data
        with open(self.file_path, 'r') as file:
            data: list[Dict[str, Any]] = json.load(file)

        # Extract necessary information (latitude, longitude, and name)
        self.places = self.__parse_places(data)
        # Calculate distances and times between all pairs of places
        distance_calculator = DistanceCalculator(self.places)
        waypoint_distances, waypoint_durations, all_waypoints_set, = distance_calculator.run(
        )

        place_additional_info = self.__get_eval_info()

        return (waypoint_distances, waypoint_durations, all_waypoints_set,
                to_list_attraction(self.places,
                                   self.stay_time), place_additional_info)

    def __get_eval_info(self):
        place_price_rating = {
            place.place_id: {
                "price_level": place.price_level,
                "rating": place.rating,
                "user_rating_totals": place.user_rating_totals,
                "category": place.category
            }
            for place in self.places
        }
        return place_price_rating

    def __parse_places(self, data: list[Dict[str, Any]]) -> list[Place]:
        places: list[Place] = []
        for place_data in data:
            placeId: str = place_data['place_id']
            lat: float = place_data['geometry']['location']['lat']
            lng: float = place_data['geometry']['location']['lng']
            price_level: int = place_data.get('price_level', 0)
            rating = place_data.get("rating", 0.0)
            user_rating_totals = place_data.get("user_rating_totals", 0.0)

            open_time, close_time = self.__extract_open_close_times(place_data)
            if open_time is None or close_time is None:
                continue

            # read the category
            category: str = place_data.get('types', 0)
            places.append(
                Place(placeId, lat, lng, time_to_datetime(open_time),
                      time_to_datetime(close_time), category, price_level,
                      rating, user_rating_totals))
        return places

    def __extract_open_close_times(self, place_data):
        # read the open time and close time
        key = 'opening_hours'
        if key in place_data and 'close' in place_data['opening_hours'][
                'periods'][0]:
            open_time: str = str(
                place_data['opening_hours']['periods'][0]['open']['time'])
            close_time: str = str(
                place_data['opening_hours']['periods'][0]['close']['time'])
            open_time = open_time[0:2] + open_time[2:4]
            close_time = close_time[0:2] + close_time[2:4]
        else:
            open_time = None
            close_time = None
        return open_time, close_time

    def readFromTsv(self):
        waypoint_data = pd.read_csv(self.file_path, sep='\t')
        for i, row in waypoint_data.iterrows():
            # Distance = meters
            self.waypoint_distances[frozenset([row.waypoint1, row.waypoint2
                                               ])] = row.distance_m

            # Duration = hours
            self.waypoint_durations[frozenset(
                [row.waypoint1, row.waypoint2])] = row.duration_s / (60. * 60.)
            self.all_waypoints_set.update([row.waypoint1, row.waypoint2])
        print(self.waypoint_distances)

        return self.waypoint_distances, self.waypoint_durations, self.all_waypoints_set
        # exit(0)


class DictReader(BaseWayPointManager):

    def __init__(self, data, stay_time: float):
        self.places: list[Place] = self.__parse_places(data)
        self.stay_time = stay_time

    def read(self):
        distance_calculator = DistanceCalculator(self.places)
        waypoint_distances, waypoint_durations, all_waypoints_set = distance_calculator.run(
        )

        place_additional_info = self.__get_eval_info()
        return (waypoint_distances, waypoint_durations, all_waypoints_set,
                to_list_attraction(self.places, stay_time=self.stay_time),
                place_additional_info)

    def __parse_places(self, data):
        places: list[Place] = []
        for place_data in data:
            placeId: str = place_data['place_id']
            lat: float = place_data['lat']
            lng: float = place_data['lng']
            price_level: int = place_data.get('price_level', 0)
            rating = place_data.get("rating", 0.0)
            user_rating_totals = place_data.get("user_rating_totals", 0.0)

            open_time, close_time = self.__extract_open_close_times(place_data)
            if open_time is None or close_time is None:
                continue

            # read the category
            category: list[str] = place_data.get('types', 0)
            places.append(
                Place(placeId, lat, lng, time_to_datetime(open_time),
                      time_to_datetime(close_time), category, price_level,
                      rating, user_rating_totals))
        return places

    def __get_eval_info(self):
        place_price_rating = {
            place.place_id: {
                "price_level": place.price_level,
                "rating": place.rating,
                "user_rating_totals": place.user_rating_totals,
                "category": place.category
            }
            for place in self.places
        }
        return place_price_rating

    @staticmethod
    def __extract_open_close_times(place_data):

        # read the open time and close time
        key = list(place_data['opening_hour'])[0]
        open_time: str = str(place_data['opening_hour'][key][0])
        close_time: str = str(place_data['opening_hour'][key][1])
        open_time = open_time[0:2] + open_time[2:4]
        close_time = close_time[0:2] + close_time[2:4]
        return open_time, close_time
