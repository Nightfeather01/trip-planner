# https://en.wikipedia.org/wiki/List_of_state_capitols_in_the_United_States

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


if __name__ == '__main__':
    all_waypoints: WaypointsList = [
        'Alabama State Capitol, 600 Dexter Avenue, Montgomery, AL 36130',
        # 'Alaska State Capitol, Juneau, AK',
        'Arizona State Capitol, 1700 W Washington St, Phoenix, AZ 85007',
        'Arkansas State Capitol, 500 Woodlane Street, Little Rock, AR 72201',
        'L St & 10th St, Sacramento, CA 95814',
        '200 E Colfax Ave, Denver, CO 80203',
        'Connecticut State Capitol, 210 Capitol Ave, Hartford, CT 06106',
        'Legislative Hall: The State Capitol, Legislative Avenue, Dover, DE 19901',
        '402 S Monroe St, Tallahassee, FL 32301',
        'Georgia State Capitol, Atlanta, GA 30334',
        # 'Hawaii State Capitol, 415 S Beretania St, Honolulu, HI 96813'
        '700 W Jefferson St, Boise, ID 83720',
        'Illinois State Capitol, Springfield, IL 62756',
        'Indiana State Capitol, Indianapolis, IN 46204',
        'Iowa State Capitol, 1007 E Grand Ave, Des Moines, IA 50319',
        '300 SW 10th Ave, Topeka, KS 66612',
        'Kentucky State Capitol Building, 700 Capitol Avenue, Frankfort, KY 40601',
        'Louisiana State Capitol, Baton Rouge, LA 70802',
        'Maine State House, Augusta, ME 04330',
        'Maryland State House, 100 State Cir, Annapolis, MD 21401',
        'Massachusetts State House, Boston, MA 02108',
        'Michigan State Capitol, Lansing, MI 48933',
        'Minnesota State Capitol, St Paul, MN 55155',
        '400-498 N West St, Jackson, MS 39201',
        'Missouri State Capitol, Jefferson City, MO 65101',
        'Montana State Capitol, 1301 E 6th Ave, Helena, MT 59601',
        'Nebraska State Capitol, 1445 K Street, Lincoln, NE 68509',
        'Nevada State Capitol, Carson City, NV 89701',
        'State House, 107 North Main Street, Concord, NH 03303',
        'New Jersey State House, Trenton, NJ 08608',
        'New Mexico State Capitol, Santa Fe, NM 87501',
        'New York State Capitol, State St. and Washington Ave, Albany, NY 12224',
        'North Carolina State Capitol, Raleigh, NC 27601',
        'North Dakota State Capitol, Bismarck, ND 58501',
        'Ohio State Capitol, 1 Capitol Square, Columbus, OH 43215',
        'Oklahoma State Capitol, Oklahoma City, OK 73105',
        'Oregon State Capitol, 900 Court St NE, Salem, OR 97301',
        'Pennsylvania State Capitol Building, North 3rd Street, Harrisburg, PA 17120',
        'Rhode Island State House, 82 Smith Street, Providence, RI 02903',
        'South Carolina State House, 1100 Gervais Street, Columbia, SC 29201',
        '500 E Capitol Ave, Pierre, SD 57501',
        'Tennessee State Capitol, 600 Charlotte Avenue, Nashville, TN 37243',
        'Texas Capitol, 1100 Congress Avenue, Austin, TX 78701',
        'Utah State Capitol, Salt Lake City, UT 84103',
        'Vermont State House, 115 State Street, Montpelier, VT 05633',
        'Virginia State Capitol, Richmond, VA 23219',
        'Washington State Capitol Bldg, 416 Sid Snyder Ave SW, Olympia, WA 98504',
        'West Virginia State Capitol, Charleston, WV 25317',
        '2 E Main St, Madison, WI 53703',
        'Wyoming State Capitol, Cheyenne, WY 82001'
    ]

    # config.waypoint_distances, config.waypoint_durations, config.all_waypoints_set = readFromTsv()
    file_path: str = 'C://xampp//WWW//Developer//week4_2//trip-planner-core//trip_plan//all_place_details_deprecated1.json'
    waypointReader = WaypointManager(file_path=file_path, stay_time=1.6)
    # 每個景點停 stay_time 固定駐留時間
    config.waypoint_distances, config.waypoint_durations, config.all_waypoints_set, attractionsDetail, place_additional_info = waypointReader.read()

    # debug for the data read in
    '''
    print('\n attractionsDetail in main.py')
    for attraction in attractionsDetail:
        print(attraction.name, attraction.open_time, attraction.close_time)
    '''

    # print(all_waypoints)
    config.all_waypoints = list(config.all_waypoints_set)
    # print('set')
    # print(config.all_waypoints_set)
    # exit(0)

    algo = NSGAIIAlgorithm(population_size=500, ngen=51)
    algo.setup(config.all_waypoints_set, config.waypoint_distances, attractionsDetail, place_additional_info)
    pop, hof, route_list = algo.run()

    # Print statistics for the best route (first route in hall of fame)
    best_route = list(hof)[0]
    print_trip_statistics(best_route, place_additional_info)

    print()
    for route in route_list:
        for attr in route:
            print(attr["place_id"])
            print(attr['place_start_datetime'])
            print(attr['place_end_datetime'])
        print()

    from core.create_animated_road_trip_map import create_animated_road_trip_map

    output_file_path = '../displayResult/trip_plan_result.json'
    create_animated_road_trip_map(reversed(hof),
                                  output_file_path=output_file_path)