from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, flash, redirect, url_for, g, session, jsonify
from extensions import db
from config import API_KEY, NEARBY_URL, DETAIL_URL, DIRECTIONS_URL
import json
import logging
from api.google_routes import GoogleRoutesAPI
from api.google_places import GooglePlacesAPI
from services.journey_data_service import JourneyDataService
from services.journey_service import JourneyService
from services.preference_service import PreferenceService
from services.form_data_service import PreferenceFormService
from utils.session_utils import clear_journey_data
from utils.validators import PreferenceValidator
from core.read_from_csv import DictReader
from core.algorithms import NSGAIIAlgorithm

trip_plan_bp = Blueprint('trip_plan', __name__, url_prefix='/trip_plan')
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@trip_plan_bp.route('/trip_planning', methods=['POST'])
def trip_planning():
    """處理偏好設定表單提交"""
    try:
        form_data_service = PreferenceFormService(db.session)
        preference_service = PreferenceService(db.session)
        journey_service = JourneyService(db.session)
        journey_data_service = JourneyDataService()
        google_api = GooglePlacesAPI(API_KEY, NEARBY_URL, DETAIL_URL)
        routes_api = GoogleRoutesAPI(API_KEY, DIRECTIONS_URL)

        # 清除先前生成之行程
        clear_journey_data()
        # 獲取並處理表單數據
        form_data = form_data_service.pre_process_form_data(request.form)
        # 驗證表單數據
        errors = PreferenceValidator.validate_form_data(form_data)

        # 驗證表單無誤
        if errors is None:
            errors = ["表單驗證過程發生錯誤"]

        # 驗證表單有誤
        if errors:
            logger.error("表單驗證有誤")
            for error in errors:
                flash({'message': error}, 'error')
            return form_data_service.render_home_page(form_data)

        # 抓取user是否有登入
        user_id = g.user if g.user else None

        # 儲存此偏好
        new_preference = preference_service.save_preference_and_fetch_places(
            form_data=form_data, api=google_api, user_id=user_id)

        # 尋找符合條件的景點
        available_places = preference_service.search_available_places(
            form_data)
        if not available_places:
            logger.error("無法找到符合條件的地點")
            flash({'message': '無法找到符合條件的地點，請調整搜尋條件'}, 'error')
            return form_data_service.render_home_page(form_data)

        # 進行行程規畫並取最佳解
        journey = run(available_places, form_data)[0]
        if not journey:
            logger.error("無法規劃行程")
            flash({'message': '行程規劃失敗，請稍後再試'}, 'error')
            return form_data_service.render_home_page(form_data)

        # 對journey進行數據補齊並推薦景點
        enhanced_journey, recommended_places = journey_data_service.process_journey_data(
            journey=journey,
            available_places=available_places,
            budget=int(form_data['budget']))
        if not enhanced_journey:
            logger.error("無法生成增強行程資料")
            flash({'message': '行程規劃失敗：無法生成行程'}, 'error')
            return form_data_service.render_home_page(form_data)

        # 規劃路程
        route_info = routes_api.get_route_info(enhanced_journey)
        if route_info['status'] == 'OK':
            # 根據交通時間調整景點開始時間
            journey_data_service.adjust_transit_times(
                enhanced_journey, route_info['routes_data'])
        else:
            logger.error(f"路線規劃錯誤: {route_info}")

        form_data = form_data_service.post_process_form_data(form_data, str(new_preference.p_id))
        # 準備行程、路線，以及推薦景點資料
        journey_data = {
            'journey': enhanced_journey,
            'route': route_info,
            'recommended_places': recommended_places,
            'form_data': form_data
        }
        # FIXME: change datetime.datetime to datetime
        # 序列化資料並保存到 session
        serialized_data = json.loads(
            json.dumps(journey_data,
                       default=journey_data_service.serialize_datetime))
        session['journey_data'] = serialized_data
        session.modified = True
        print(serialized_data)
        # 顯示成功訊息
        flash({
            'message': '行程規劃成功！',
            'uuid': str(new_preference.p_id)
        }, 'success')
        return redirect(url_for('trip_plan.show_result'))

    except Exception as e:
        logger.error(f"行程規劃錯誤: {str(e)}")
        flash({'message': f'系統錯誤：{str(e)}'}, 'error')
        return form_data_service.render_home_page(form_data)


@trip_plan_bp.route('/show_result')
def show_result():
    """顯示行程結果頁面"""
    try:
        journey_data_service = JourneyDataService()
        journey_data = session.get('journey_data')

        if not journey_data:
            flash({'message': '找不到行程資料，請重新規劃行程'}, 'error')
            return redirect(url_for('homepage'))

        # 處理日期時間格式
        processed_data = journey_data_service.process_session_journey_data(journey_data)

        return render_template(
            'trip_planning_result.html',
            google_maps_api_key=API_KEY,
            journey=processed_data.get('journey', []),
            route=processed_data.get('route', {}),
            recommended_places=processed_data.get('recommended_places', []),
            form_data=processed_data.get('form_data', {}),  # 添加 form_data
            uuid=processed_data.get('form_data', {}).get('uuid', '')  # 添加 uuid
        )

    except Exception as e:
        logger.error(f"顯示結果時發生錯誤: {str(e)}")
        flash({'message': '顯示結果時發生錯誤，請重新規劃行程'}, 'error')
        return redirect(url_for('homepage'))


@trip_plan_bp.route('/get_route_data')
def get_route_data():
    """取得當前行程的路線資料"""
    try:
        journey_data = session.get('journey_data')
        if not journey_data:
            return jsonify({'status': 'ERROR', 'message': '找不到行程資料，請重新規劃行程'})

        # 不需要再次處理日期時間，因為已經在session中存儲了正確格式
        return jsonify({
            'status': 'OK',
            'journey': journey_data.get('journey', []),
            'route': journey_data.get('route', {})
        })

    except Exception as e:
        logger.error(f"取得路線資料時發生錯誤: {str(e)}")
        return jsonify({'status': 'ERROR', 'message': str(e)})


'''
@trip_plan_bp.route('import_data', methods=['GET', 'POST'])
def import_data():

@trip_plan_bp.route('share', methods=['GET', 'POST'])
def import_data():

@trip_plan_bp.route('management', methods=['GET', 'POST'])
def import_data():
'''


def print_trip_statistics(route, place_to_price_rating, waypoint_distances):
    """
    Calculate and print statistics for a trip itinerary
    Args:
        route: List of AttractionModify objects containing the trip itinerary
        place_to_price_rating: Dictionary containing price, rating and user_ratings data for each place
        waypoint_distances: Dictionary containing distances between pairs of places
    """
    total_price_level = 0
    total_rating = 0
    total_user_ratings = 0
    total_distance = 0
    num_places = len(route)

    print("\n=== Trip Statistics ===")
    print("\nDetailed Schedule:")
    print("-" * 100)
    print(f"{'Location':<40} {'Start Time':<12} {'End Time':<12} {'Distance to Next (km)':<20}")
    print("-" * 100)

    for i, attraction in enumerate(route):
        place_id = attraction.attr.name
        place_stats = place_to_price_rating[place_id]

        # Calculate distance to next location
        distance = 0
        if i < len(route) - 1:
            next_place = route[i + 1].attr.name
            distance = waypoint_distances[frozenset([place_id, next_place])]
            total_distance += distance

        # Add to totals
        total_price_level += place_stats.get('price_level', 0)
        total_rating += place_stats.get('rating', 0)
        total_user_ratings += place_stats.get('user_rating_totals', 0)

        # Print schedule details with distance
        print(
            f"{place_id:<40} {attraction.time_range.start_time.strftime('%H:%M'):<12} "
            f"{attraction.time_range.end_time.strftime('%H:%M'):<12} "
            f"{f'{distance:.2f}' if distance > 0 else 'End':<20}")

    print("\nSummary Statistics:")
    print(f"Total Distance: {total_distance:.2f} km")
    print(f"Average Distance Between Locations: {total_distance / (num_places - 1):.2f} km")
    print(f"Average Price Level: {total_price_level / num_places:.2f} (scale 0-4)")
    print(f"Average Rating: {total_rating / num_places:.2f} (scale 0-5)")
    print(f"Average User Ratings Count: {total_user_ratings / num_places:.0f}")


def get_stay_time_from_form_data(form_data):
    if form_data['travel_mode'] is True:
        return 2
    return 1.5


'''
def get_departure_return_time(form_data):

    # TODO: split the date time of form_data['departure_datetime']
   "departure_datetime":"2024-11-19T14:25",
   "return_datetime":"2024-11-21T13:25",
   "daily_depart_time":"15:25",
   "daily_return_time":"16:25",
'''


def run(available_places, form_data):
    dict_reader = DictReader(data=available_places,
                             stay_time=get_stay_time_from_form_data(form_data))
    waypoint_distances, waypoint_durations, all_waypoints_set, attractionsDetail, place_additional_info = dict_reader.read(
    )

    # print('\n attractionsDetail in main.py')
    # for attraction in attractionsDetail:
        # print(attraction.name, attraction.open_time, attraction.close_time)

    all_waypoints = list(all_waypoints_set)

    algo = NSGAIIAlgorithm(population_size=500, ngen=form_data['ngen'], cxpb=0.5, mutpb=0.2)
    # algo = NSGAIIAlgorithm(population_size=500, ngen=51, cxpb=0.5, mutpb=0.2)
    algo.setup(all_waypoints_set, waypoint_distances, attractionsDetail,
               place_additional_info, form_data['daily_depart_time'],
               form_data['daily_return_time'], form_data['departure_datetime'],
               form_data['return_datetime'])
    pop, hof, route_list = algo.run()

    # Print statistics for the best route (first route in hall of fame)
    best_route = list(hof)[0]
    print_trip_statistics(best_route, place_additional_info, waypoint_distances)

    return route_list
