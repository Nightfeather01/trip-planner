from datetime import datetime, timedelta
from pandas.io.formats.info import _TableBuilderVerboseMixin
from typing_extensions import Annotated
from typing import Any

Hours = Annotated[float, "hours"]

import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',  # 設置日誌格式
    handlers=[
        # logging.StreamHandler(),  # 設置輸出到控制台
        logging.FileHandler("generate_initial_individual.log", mode='w', encoding='utf-8')  # 設置輸出到文件
    ]
)

logger = logging.getLogger(__name__)


class Attraction:

    def __init__(self, name, open_time, close_time, stay_time: Hours):
        self.name = name
        self.open_time = open_time
        self.close_time = close_time
        self.stay_time = stay_time


class TimeRange:

    def __init__(self, start_time, end_time) -> None:
        self.start_time = start_time
        self.end_time = end_time


class AttractionModify:

    def __init__(self, attr: Attraction, time_range: TimeRange) -> None:
        self.attr = attr
        self.time_range = time_range


from datetime import datetime, timedelta
from typing import List, Set, Dict, Tuple
from dataclasses import dataclass
import random
import numpy as np
from collections import defaultdict



@dataclass
class ScheduleConfig:
    """行程生成的配置參數"""
    min_attractions: int = 3
    max_attractions: int = 8
    travel_time: timedelta = timedelta(minutes=30)
    max_schedules: int = 100

class DiverseScheduleGenerator:
    def __init__(self,
                 attractions: List[Attraction],
                 start_time: datetime,
                 end_time: datetime,
                 place_additional_info: Dict[str, Dict[str, Any]]):
        # attractionsDetail include attraction.name, attraction.open_time, attraction.close_time
        self.attractions = attractions
        self.start_time = start_time
        self.end_time = end_time
        self.place_additional_info = place_additional_info
        self.config = ScheduleConfig()

    def generate_population(self) -> List[List[AttractionModify]]:
        """使用多種方法生成多樣化的初始行程"""
        schedules = []

        # 1. 貪婪法生成部分行程
        greedy_schedules = self._generate_greedy_schedules()
        schedules.extend(greedy_schedules)

        # 2. 隨機採樣法生成部分行程
        random_schedules = self._generate_random_schedules()
        schedules.extend(random_schedules)

        # 3. 時間槽分配法生成部分行程
        timeslot_schedules = self._generate_timeslot_based_schedules()
        schedules.extend(timeslot_schedules)

        # 4. 分群生成法
        cluster_schedules = self._generate_cluster_based_schedules()
        schedules.extend(cluster_schedules)

        # 移除無效或重複的行程
        valid_schedules = [s for s in schedules if self._is_valid_schedule(s)]
        return self._ensure_diversity(valid_schedules)

    def _generate_greedy_schedules(self) -> List[List[AttractionModify]]:
        """貪婪法生成行程"""
        schedules = []
        priorities = [
            lambda x: self.place_additional_info.get(x.name, {}).get('rating', 0),
            lambda x: -self.place_additional_info.get(x.name, {}).get('price_level', 0),
            lambda x: self.place_additional_info.get(x.name, {}).get('user_rating_totals', 0),
            lambda x: (x.close_time - x.open_time).total_seconds()
        ]

        for priority_func in priorities:
            available_attractions = sorted(self.attractions, key=priority_func, reverse=True)
            schedule = []
            current_time = self.start_time
            used_attractions = set()  # 追踪已使用的景點

            for attraction in available_attractions:
                if (attraction.name not in used_attractions and  # 確保不重複
                        len(schedule) < self.config.max_attractions and
                        self._can_add_to_schedule(attraction, current_time)):
                    end_time = current_time + timedelta(hours=attraction.stay_time)
                    schedule.append(AttractionModify(
                        attr=attraction,
                        time_range=TimeRange(current_time, end_time)
                    ))
                    used_attractions.add(attraction.name)  # 記錄已使用的景點
                    current_time = end_time + self.config.travel_time

            if len(schedule) >= self.config.min_attractions:
                schedules.append(schedule)

        return schedules

    def _generate_random_schedules(self) -> List[List[AttractionModify]]:
        """隨機生成行程"""
        schedules = []
        for _ in range(self.config.max_schedules // 3):
            schedule = []
            current_time = self.start_time
            available_attractions = self.attractions.copy()
            used_attractions = set()  # 追踪已使用的景點

            while (len(available_attractions) > 0 and
                   len(schedule) < self.config.max_attractions):
                attraction = random.choice(available_attractions)
                available_attractions.remove(attraction)  # 從可用列表中移除

                if (attraction.name not in used_attractions and  # 確保不重複
                        self._can_add_to_schedule(attraction, current_time)):
                    end_time = current_time + timedelta(hours=attraction.stay_time)
                    schedule.append(AttractionModify(
                        attr=attraction,
                        time_range=TimeRange(current_time, end_time)
                    ))
                    used_attractions.add(attraction.name)  # 記錄已使用的景點
                    current_time = end_time + self.config.travel_time

            if len(schedule) >= self.config.min_attractions:
                schedules.append(schedule)

        return schedules

    def _generate_timeslot_based_schedules(self) -> List[List[AttractionModify]]:
        """基於時間槽生成行程"""
        time_slots = self._create_time_slots()
        schedules = []

        for _ in range(self.config.max_schedules // 3):
            schedule = []
            used_attractions = set()  # 追踪已使用的景點

            for slot_start, slot_end in time_slots:
                suitable_attractions = [
                    attr for attr in self.attractions
                    if (attr.name not in used_attractions and  # 確保不重複
                        attr.open_time <= slot_start and
                        attr.close_time >= slot_end and
                        timedelta(hours=attr.stay_time) <= (slot_end - slot_start))
                ]

                if suitable_attractions:
                    attraction = random.choice(suitable_attractions)
                    schedule.append(AttractionModify(
                        attr=attraction,
                        time_range=TimeRange(slot_start, slot_end)
                    ))
                    used_attractions.add(attraction.name)  # 記錄已使用的景點

            if len(schedule) >= self.config.min_attractions:
                schedules.append(schedule)

        return schedules

    def _generate_cluster_based_schedules(self) -> List[List[AttractionModify]]:
        """基於分群生成行程"""
        # 根據營業時間分群
        time_clusters = defaultdict(list)
        for attraction in self.attractions:
            key = (attraction.open_time.hour, attraction.close_time.hour)
            time_clusters[key].append(attraction)

        schedules = []
        for _ in range(self.config.max_schedules // 3):
            schedule = []
            current_time = self.start_time
            used_attractions = set()  # 追踪已使用的景點

            # 從每個時間群集中選擇景點
            for cluster in time_clusters.values():
                if cluster and len(schedule) < self.config.max_attractions:
                    available_attractions = [
                        attr for attr in cluster
                        if attr.name not in used_attractions  # 確保不重複
                    ]

                    if available_attractions and self._can_add_to_schedule(available_attractions[0], current_time):
                        attraction = random.choice(available_attractions)
                        end_time = current_time + timedelta(hours=attraction.stay_time)
                        schedule.append(AttractionModify(
                            attr=attraction,
                            time_range=TimeRange(current_time, end_time)
                        ))
                        used_attractions.add(attraction.name)  # 記錄已使用的景點
                        current_time = end_time + self.config.travel_time

            if len(schedule) >= self.config.min_attractions:
                schedules.append(schedule)

        return schedules

    def _can_add_to_schedule(self, attraction: Attraction, current_time: datetime) -> bool:
        """檢查是否可以將景點添加到當前時間"""
        visit_end_time = current_time + timedelta(hours=attraction.stay_time)
        return (current_time >= attraction.open_time and
                visit_end_time <= attraction.close_time and
                visit_end_time <= self.end_time)

    def _create_time_slots(self) -> List[Tuple[datetime, datetime]]:
        """創建時間槽"""
        slots = []
        current = self.start_time
        while current < self.end_time:
            slot_end = min(current + timedelta(hours=2), self.end_time)
            slots.append((current, slot_end))
            current = slot_end
        return slots

    def _is_valid_schedule(self, schedule: List[AttractionModify]) -> bool:
        """檢查行程是否有效（無重複且時間順序正確）"""
        if not schedule:
            return False

        # 檢查重複
        attraction_ids = set()
        for attr_mod in schedule:
            if attr_mod.attr.name in attraction_ids:
                return False
            attraction_ids.add(attr_mod.attr.name)

        # 檢查時間順序
        for i in range(1, len(schedule)):
            if schedule[i-1].time_range.end_time > schedule[i].time_range.start_time:
                return False

        return len(schedule) >= self.config.min_attractions

    def _ensure_diversity(self, schedules: List[List[AttractionModify]]) -> List[List[AttractionModify]]:
        """確保行程多樣性"""
        diverse_schedules = []
        for schedule in schedules:
            if not self._is_too_similar(schedule, diverse_schedules):
                diverse_schedules.append(schedule)
        return diverse_schedules

    def _is_too_similar(self, schedule: List[AttractionModify],
                        existing_schedules: List[List[AttractionModify]],
                        similarity_threshold: float = 0.8) -> bool:
        """檢查行程是否與現有行程過於相似"""
        schedule_attractions = set(attr.attr.name for attr in schedule)

        for existing_schedule in existing_schedules:
            existing_attractions = set(attr.attr.name for attr in existing_schedule)
            intersection = len(schedule_attractions.intersection(existing_attractions))
            union = len(schedule_attractions.union(existing_attractions))

            if intersection / union > similarity_threshold:
                return True

        return False

class InitIndividual:
    visited = []
    allSchedules: list[list[AttractionModify]] = []
    allAttractionSet = set()

    maxInteration = 200

    def __init__(self, attractions: list[Attraction], start_time, end_time,
                 days: int) -> None:
        self.attractions = attractions
        self.startTime = start_time
        self.tripEndTime = end_time

        self.days = days

    def sortAttractions(self):
        self.attractions = sorted(self.attractions,
                                  key=lambda x: (x.open_time, x.close_time))

    def isOpenTime(self, currentTime, attraction: Attraction):
        end_time = self.addTimedelta(currentTime, attraction.stay_time)
        logger.debug('\ndebug isOpenTime in generate_initial_trip.py isOpenTime')
        logger.debug(currentTime, end_time, attraction.open_time,
                     attraction.close_time)

        if currentTime >= attraction.open_time and end_time <= attraction.close_time:
            return True
        return False

    def canArrangeMore(self, start_idx, currentTime):
        for i in range(start_idx, len(self.attractions)):
            if self.isOpenTime(currentTime, self.attractions[i]):
                # print(currentTime)
                # print(attractions[i].name, attractions[i].open_time)
                return True
        return False

    @staticmethod
    def debugCurrentSchedule(currentSchedule):
        logger.debug('\ncurrentSchedule')
        for i in currentSchedule:
            logger.debug(i.name)

    @staticmethod
    def addTimedelta(current_time: datetime, stay_time: Hours):
        return current_time + timedelta(hours=stay_time)

    def getInitIndi(self):
        self.sortAttractions()
        logger.debug('\nattractions sorted in generate_initial_trip.py')
        for attr in self.attractions:
            logger.debug(attr.name, attr.open_time, attr.close_time, attr.stay_time)

        # allSchedules: list[list[AttractionModify]] = []
        # for i in range(0, self.days):
        self.dfs(0, self.startTime, [])

        return self.allSchedules

    @classmethod
    def getTimeRange(cls, currentTime, attraction):
        endTime = cls.addTimedelta(currentTime,
                                   attraction.stay_time)
        return TimeRange(currentTime, endTime)

    def dfs(self, startIdx, currentTime,
            currentSchedule: list[AttractionModify]):
        # if isValid(currentTime):
        #     currentTime += timedelta(hours=1.5)

        # print(len(self.attractions))

        # print('debug bool')
        # print(self.canArrangeMore(startIdx, currentTime))

        if self.maxInteration < 0:
            return False

        if currentTime > self.tripEndTime or (self.canArrangeMore(
                startIdx, currentTime) == False):
            if len(currentSchedule) >= 1:
                # otherwise the referecne will be append to the list not the value
                self.allSchedules.append(list(currentSchedule))

                self.maxInteration -= 1

                # self.allAttractionSet = self.allAttractionSet | set(currentSchedule)

                # print(len((self.allSchedules[0])))
                # print(self.allSchedules)
            return True

        for i in range(startIdx, len(self.attractions)):
            logger.debug('\n in dfs')
            logger.debug(self.attractions[i].name)
            if self.isOpenTime(currentTime, self.attractions[i]):
                endTime = self.addTimedelta(currentTime,
                                            self.attractions[i].stay_time)

                # logger.debug(f'stay time: {stay_time}')
                # logger.debug(currentTime, end_time)
                currentAttractionModify = AttractionModify(
                    attr=self.attractions[i],
                    time_range=TimeRange(currentTime, endTime))
                currentSchedule.append(currentAttractionModify)

                # self.debugCurrentSchedule(currentSchedule)
                self.dfs(i + 1, endTime, currentSchedule)
                currentSchedule.pop()


def is_valid_schedule2(schedule):
    current_time = datetime.strptime("08:00", "%H:%M")
    for attraction in schedule:
        if current_time > attraction.close_time or current_time < attraction.open_time:
            return False

        current_time += timedelta(hours=1)
    return True


def dfs2(current_schedule, remaining_attractions, all_schedules):
    if not remaining_attractions:
        if is_valid_schedule2(current_schedule):
            all_schedules.append(list(current_schedule))
        return

    for i in range(len(remaining_attractions)):
        attraction = remaining_attractions[i]
        new_schedule = current_schedule + [attraction]
        new_remaining = remaining_attractions[:i] + remaining_attractions[i +
                                                                          1:]
        dfs2(new_schedule, new_remaining, all_schedules)


'''
all_possible_schedules = []
dfs2([], attractions, all_possible_schedules)

for index, schedule in enumerate(all_possible_schedules):
    print(f"排程集合 {index + 1}:")
    for attraction in schedule:
        print(f"  {attraction.name}, 營業時間: {attraction.open_time.strftime('%H:%M')}-{attraction.close_time.strftime('%H:%M')}")
    print()
'''
