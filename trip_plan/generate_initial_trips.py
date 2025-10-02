import logging
import datetime
from itertools import permutations

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GenerateInitialTrips:

    def __init__(self, all_place_details_subset: list[dict], preference: dict):
        self.all_place_detail_subset = all_place_details_subset
        self.start_datetime = preference['est_dep']
        self.end_datetime = preference['est_ret']
        self.start_time = preference['dep_day']
        self.end_time = preference['ret_day']
        self.current_weekday = preference['est_dep'].weekday()
        self.current_datetime = self.start_datetime

    # 檢查店家是否有開啟
    def is_place_open(self, place: dict, check_time: datetime.datetime) -> bool:
        # 抓取目前星期幾以抓出對應營業時間
        weekday = str(check_time.weekday())
        # 抓取營業時間，存為list
        opening_hours = place['opening_hours'].get(weekday, [])
        # 如果沒有營業時間
        # print(opening_hours)
        if not opening_hours:
            # logger.error("缺少營業時間")
            return False
        # 轉換為time
        check_time = check_time.time()
        # 作時間切割，偶數為開始營業時間，奇數為結束營業時間
        for start, end in zip(opening_hours[::2], opening_hours[1::2]):
            # 確認符合其中之一的營業時間，回傳True
            if start <= check_time <= end:
                return True
        # 全部不符合，回傳False
        return False

    def generate_initial_trips(self):
        all_initial_trips = []
        max_trips = 100 # 設置最大生成數量
        for perm in permutations(self.all_place_detail_subset):
            # 超過最大數量即停止
            if len(all_initial_trips) >= max_trips:
                break
            initial_trip = []
            # 設定現在時間
            # current_time = self.current_datetime
            current_time = self.current_datetime.replace(hour=self.start_time.hour, minute=self.start_time.minute)
            for place in perm:
                # 現在日期超過結束日期，結束
                if current_time.date() > self.end_datetime.date():
                    break
                # 現在時間小於開始時間，設現在時間為start_time
                # if current_time.time() < self.start_time:
                #     current_time = current_time.replace(hour=self.start_time.hour, minute=self.start_time.minute)
                # 現在時間超過結束時間，換至隔日start_time
                if current_time.time() >= self.end_time:
                    current_time = (current_time + datetime.timedelta(days=1)).replace(hour=self.start_time.hour, minute=self.start_time.minute)
                    continue
                # 營業時間符合規定
                if self.is_place_open(place, current_time):
                    # 將駐留時間轉換為timedelta進行計算
                    stay_timedelta = datetime.timedelta(hours=place['stay_time'].hour, minutes=place['stay_time'].minute)
                    # 計算此行程結束時間，現在時間+駐留時間
                    end_time = current_time + stay_timedelta
                    # 未超過結束時間，為合法的景點，加入其中
                    if end_time.time() <= self.end_time:
                        initial_trip.append({
                            'place_id': place['place_id'],
                            'start_time': current_time,
                            'end_time': end_time
                        })
                        current_time = end_time
                    # 如果超過結束時間，則進入至隔天
                    else:
                        break
                else:
                    continue
            # 將一個合理排程加入all_initial_trip中
            if initial_trip and initial_trip not in all_initial_trips:
                all_initial_trips.append(initial_trip)
        return all_initial_trips
