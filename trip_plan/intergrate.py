from datetime import time, datetime
import logging
import json
from config import API_KEY, NEARBY_URL, DETAIL_URL
from trip_plan.request_GoogleAPI import GooglePlacesAPI
# from generate_all_waypoints_dist import GenerateAllWaypointsDist
# from generate_initial_trips import GenerateInitialTrips

import random
import numpy as np
import copy
from tqdm import tqdm

from deap import algorithms
from deap import base
from deap import creator
from deap import tools

from core.algorithms import NSGAIIAlgorithm
from core.read_from_csv import WaypointManager

from core.read_from_csv import *
import config

from core.type_alias import WaypointsList


def print_trip_statistics(route, place_to_price_rating):
    """
    Calculate and print statistics for a trip itinerary

    Args:
        route: List of AttractionModify objects containing the trip itinerary
        place_to_price_rating: Dictionary containing price, rating and user_ratings data for each place
    """
    total_price_level = 0
    total_rating = 0
    total_user_ratings = 0
    num_places = len(route)

    print("\n=== Trip Statistics ===")
    print("\nDetailed Schedule:")
    print("-" * 80)
    print(f"{'Location':<40} {'Start Time':<12} {'End Time':<12}")
    print("-" * 80)

    for attraction in route:
        place_id = attraction.attr.name
        place_stats = place_to_price_rating[place_id]

        # Add to totals with default values in case keys don't exist
        total_price_level += place_stats.get('price_level', 0)
        total_rating += place_stats.get('rating', 0)
        total_user_ratings += place_stats.get('user_ratings_total', 0)  # Fixed key name here

        # Print schedule details
        print(f"{place_id:<40} {attraction.time_range.start_time.strftime('%H:%M'):<12} "
              f"{attraction.time_range.end_time.strftime('%H:%M'):<12}")

    print("\nAverages:")
    print(f"Average Price Level: {total_price_level / num_places:.2f} (scale 0-4)")
    print(f"Average Rating: {total_rating / num_places:.2f} (scale 0-5)")
    print(f"Average User Ratings Count: {total_user_ratings / num_places:.0f}")


def run():
    file_path: str = 'C://git_repos//trip-planner-core//trip_plan//all_place_details_deprecated1.json'
    waypointReader = WaypointManager(file_path=file_path)
    config.waypoint_distances, config.waypoint_durations, config.all_waypoints_set, attractionsDetail, place_additional_info = waypointReader.read()

    print('\n attractionsDetail in main.py')
    for attraction in attractionsDetail:
        print(attraction.name, attraction.open_time, attraction.close_time)

    config.all_waypoints = list(config.all_waypoints_set)

    algo = NSGAIIAlgorithm(population_size=500, ngen=51)
    algo.setup(config.all_waypoints_set, config.waypoint_distances, attractionsDetail, place_additional_info)
    pop, hof, route_list = algo.run()

    # Print statistics for the best route (first route in hall of fame)
    best_route = list(hof)[0]
    print_trip_statistics(best_route, place_additional_info)

    from core.create_animated_road_trip_map import create_animated_road_trip_map

    output_file_path = '/deprecated/trip_plan_result.json'
    create_animated_road_trip_map(reversed(hof),
                                  output_file_path=output_file_path)


def main():
    preference = {
        'location': '23.4812732, 120.4514065',
        'radius': 4000,
        'maxprice': 4,
        'minprice': 0
    }

    api = GooglePlacesAPI(API_KEY, NEARBY_URL)
    api.search_nearby_places(preference)

    # 取得搜尋結果摘要
    summary = api.get_results_summary()
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    '''
    # 假資料
    preference = {
        'location': '23.4812732, 120.4514065',
        'radius': 20000,
        'keyword': ['café']
    }
        'est_dep': datetime(year=2024, month=8, day=29, hour=10, minute=0),
        'est_ret': datetime(year=2024, month=8, day=30, hour=19, minute=30),
        'dep_day': time(10, 0, 0, 0),
        'ret_day': time(16, 0, 0, 0)
    api = GooglePlacesAPI(API_KEY, NEARBY_URL, DETAIL_URL)
    # 請求並儲存所有相符的place_id資料
    all_nearby_places = api.get_nearby_places(preference)
    # 將place_details資料存為JSON檔
    for place_id in all_nearby_places:
        place_details = api.get_place_details(place_id)
        api.process_place_details(place_details)
    # run()
    '''


if __name__ == "__main__":
    main()
