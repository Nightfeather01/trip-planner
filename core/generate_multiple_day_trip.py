import random
from datetime import datetime, timedelta
from typing import List, Dict, Set, Tuple, Any
from dataclasses import dataclass
import logging
from collections import defaultdict
import unittest

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("generate_initial_individual.log",
                            mode='w',
                            encoding='utf-8')
    ])
logger = logging.getLogger(__name__)


class Attraction:

    def __init__(self, name, open_time, close_time, stay_time: float):
        self.name = name
        self.open_time = open_time
        self.close_time = close_time
        self.stay_time = stay_time


class TimeRange:

    def __init__(self, start_time: datetime, end_time: datetime) -> None:
        self.start_time = start_time
        self.end_time = end_time


class AttractionModify:

    def __init__(self, attr: Attraction, time_range: TimeRange) -> None:
        self.attr = attr
        self.time_range = time_range


@dataclass
class DayConfig:
    """每天的时间配置"""
    date: datetime
    start_time: datetime
    end_time: datetime

    @classmethod
    def create_day_configs(cls, departure_datetime: str, return_datetime: str,
                           daily_depart_time: str, daily_return_time: str):
        """
        根據旅行數據創建每天的時間配置

        Args:
            departure_datetime: 旅程開始時間 (格式: "YYYY-MM-DDTHH:MM")
            return_datetime: 旅程結束時間 (格式: "YYYY-MM-DDTHH:MM")
            daily_depart_time: 每天的開始時間 (格式: "HH:MM")
            daily_return_time: 每天的結束時間 (格式: "HH:MM")

        Returns:
            List[DayConfig]: 每天的時間配置列表
        """
        # 解析日期和時間
        departure = datetime.strptime(departure_datetime, "%Y-%m-%dT%H:%M")
        return_time = datetime.strptime(return_datetime, "%Y-%m-%dT%H:%M")
        daily_start = datetime.strptime(daily_depart_time, "%H:%M").time()
        daily_end = datetime.strptime(daily_return_time, "%H:%M").time()

        # 計算總天數
        total_days = (return_time.date() - departure.date()).days + 1

        day_configs = []
        current_date = departure.date()

        for day_num in range(total_days):
            if day_num == 0:  # 第一天
                # 使用實際的 departure 時間
                day_start = departure
                day_end = datetime.combine(current_date, daily_end)

            elif day_num == total_days - 1:  # 最後一天
                # 使用實際的 return 時間
                day_start = datetime.combine(current_date, daily_start)
                day_end = return_time

            else:  # 中間的天數
                # 使用每日固定的開始和結束時間
                day_start = datetime.combine(current_date, daily_start)
                day_end = datetime.combine(current_date, daily_end)

            # 創建 DayConfig
            day_configs.append(
                DayConfig(date=datetime.combine(current_date, daily_start),
                          start_time=day_start,
                          end_time=day_end))

            # 移到下一天
            current_date += timedelta(days=1)

        return day_configs


class ScheduleTransformer:
    """處理行程轉換的類別"""

    @staticmethod
    def flatten_schedule(multi_day_schedule):
        """將多天行程轉換為單一序列"""
        flattened = []
        for day_schedule in multi_day_schedule:
            flattened.extend(day_schedule)
        return flattened

    @staticmethod
    def flatten_schedules(multi_day_schedules):
        """將多個多天行程轉換為單一序列列表"""
        return [
            ScheduleTransformer.flatten_schedule(schedule)
            for schedule in multi_day_schedules
        ]

    @staticmethod
    def split_by_date(flattened_schedule):
        """將單一序列重新分割為多天行程"""
        daily_schedules = []
        current_day = []
        current_date = None

        for attraction in flattened_schedule:
            attraction_date = attraction.time_range.start_time.date()
            if current_date is None:
                current_date = attraction_date

            if attraction_date != current_date:
                if current_day:
                    daily_schedules.append(current_day)
                current_day = []
                current_date = attraction_date

            current_day.append(attraction)

        if current_day:
            daily_schedules.append(current_day)

        return daily_schedules

    @staticmethod
    def to_response_format(schedule):
        """轉換為API回應格式"""
        return [{
            "place_id": attraction.attr.name,
            "place_start_datetime": attraction.time_range.start_time,
            "place_end_datetime": attraction.time_range.end_time,
        } for attraction in schedule]


@dataclass
class GeneratorConfig:
    """生成器配置参数"""
    min_attractions_per_day: int = 2
    max_attractions_per_day: int = 6  # 增加最大值
    travel_time: timedelta = timedelta(minutes=30)
    attempts_per_strategy: int = 500  # 每個策略的嘗試次數
    max_retry_per_day: int = 10  # 每天的最大重試次數
    similarity_threshold: float = 0.95  # 提高相似度閾值
    min_total_schedules: int = 20  # 最少生成的行程數
    max_total_schedules: int = 100  # 最多生成的行程數


class MultiDayScheduleGenerator:

    def __init__(self, attractions: List[Attraction],
                 day_configs: List[DayConfig],
                 place_additional_info: Dict[str, Dict[str, Any]]):
        self.attractions = attractions
        self.day_configs = day_configs
        self.place_additional_info = place_additional_info
        self.config = GeneratorConfig()
        self.__init_attraction_stats()

    def __init_attraction_stats(self):
        """初始化景點統計信息"""
        self.attraction_stats = {
            'rating':
            self.__normalize_values({
                a.name:
                self.place_additional_info.get(a.name, {}).get('rating', 0)
                for a in self.attractions
            }),
            'price':
            self.__normalize_values({
                a.name:
                self.place_additional_info.get(a.name,
                                               {}).get('price_level', 0)
                for a in self.attractions
            }),
            'popularity':
            self.__normalize_values({
                a.name:
                self.place_additional_info.get(a.name,
                                               {}).get('user_rating_totals', 0)
                for a in self.attractions
            })
        }

    def __normalize_values(self, value_dict: Dict[str,
                                                  float]) -> Dict[str, float]:
        """將值正規化到0-1範圍"""
        if not value_dict:
            return {}
        min_val = min(value_dict.values())
        max_val = max(value_dict.values())
        if max_val == min_val:
            return {k: 1.0 for k in value_dict}
        return {
            k: (v - min_val) / (max_val - min_val)
            for k, v in value_dict.items()
        }

    def generate_population(self) -> List[List[List[AttractionModify]]]:
        """生成多天行程方案"""
        all_schedules = []

        # 使用不同策略生成行程
        strategies = [('greedy', self.__generate_greedy_schedules),
                      ('random', self.__generate_random_schedules),
                      ('timeslot', self.__generate_timeslot_based_schedules),
                      ('cluster', self.__generate_cluster_based_schedules)]

        for strategy_name, strategy_func in strategies:
            logger.info(f"Generating schedules using {strategy_name} strategy")
            schedules = strategy_func()
            valid_schedules = [
                s for s in schedules if self.__is_valid_schedule(s)
            ]
            all_schedules.extend(valid_schedules)
            logger.info(
                f"Generated {len(valid_schedules)} valid schedules using {strategy_name} strategy"
            )

        # 確保生成足夠的行程
        while len(all_schedules) < self.config.min_total_schedules:
            logger.info(
                f"Not enough schedules ({len(all_schedules)}), generating more..."
            )
            additional = self.__generate_random_schedules()
            valid_additional = [
                s for s in additional if self.__is_valid_schedule(s)
            ]
            all_schedules.extend(valid_additional)

        # 確保多樣性並限制數量
        diverse_schedules = self.__ensure_diversity(all_schedules)
        if len(diverse_schedules) > self.config.max_total_schedules:
            diverse_schedules = diverse_schedules[:self.config.
                                                  max_total_schedules]

        logger.info(
            f"Final number of diverse schedules: {len(diverse_schedules)}")
        return diverse_schedules

    def __generate_greedy_schedules(
            self) -> List[List[List[AttractionModify]]]:
        """使用貪婪策略生成行程"""
        schedules = []
        priority_functions = [
            lambda a: self.attraction_stats['rating'][a.name],
            lambda a: -self.attraction_stats['price'][a.name],
            lambda a: self.attraction_stats['popularity'][a.name], lambda a:
            (self.attraction_stats['rating'][a.name] * 0.4 + -self.
             attraction_stats['price'][a.name] * 0.3 + self.attraction_stats[
                 'popularity'][a.name] * 0.3)
        ]

        for _ in range(self.config.attempts_per_strategy):
            priority_func = random.choice(priority_functions)
            schedule = self.__generate_one_schedule(
                sorted(self.attractions, key=priority_func, reverse=True))
            if schedule:
                schedules.append(schedule)

        return schedules

    def __generate_random_schedules(
            self) -> List[List[List[AttractionModify]]]:
        """使用隨機策略生成行程"""
        schedules = []
        for _ in range(self.config.attempts_per_strategy):
            attractions = list(self.attractions)
            random.shuffle(attractions)
            schedule = self.__generate_one_schedule(attractions)
            if schedule:
                schedules.append(schedule)
        return schedules

    def __generate_timeslot_based_schedules(
            self) -> List[List[List[AttractionModify]]]:
        """使用時間槽策略生成行程"""
        schedules = []
        for _ in range(self.config.attempts_per_strategy):
            schedule = self.__generate_one_schedule_with_timeslots()
            if schedule:
                schedules.append(schedule)
        return schedules

    def __generate_cluster_based_schedules(
            self) -> List[List[List[AttractionModify]]]:
        """使用聚類策略生成行程"""
        # 根據營業時間聚類
        clusters = defaultdict(list)
        for attraction in self.attractions:
            key = (attraction.open_time.hour // 3,
                   attraction.close_time.hour // 3)
            clusters[key].append(attraction)

        schedules = []
        for _ in range(self.config.attempts_per_strategy):
            schedule = []
            used_attractions = set()

            for day_config in self.day_configs:
                day_schedule = self.__generate_day_schedule_from_clusters(
                    clusters, day_config, used_attractions)
                if not day_schedule:
                    break
                schedule.append(day_schedule)
                used_attractions.update(attr.attr.name
                                        for attr in day_schedule)

            if len(schedule) == len(self.day_configs):
                schedules.append(schedule)

        return schedules

    def __generate_one_schedule(
            self,
            attractions: List[Attraction]) -> List[List[AttractionModify]]:
        """生成一個完整的行程"""
        schedule = []
        used_attractions = set()

        for day_config in self.day_configs:
            day_schedule = self.__generate_day_schedule(
                attractions, day_config, used_attractions)
            if not day_schedule:
                return []
            schedule.append(day_schedule)
            used_attractions.update(attr.attr.name for attr in day_schedule)

        return schedule if len(schedule) == len(self.day_configs) else []

    def __generate_day_schedule(
            self, attractions: List[Attraction], day_config: DayConfig,
            used_attractions: Set[str]) -> List[AttractionModify]:
        """生成單天行程"""
        for _ in range(self.config.max_retry_per_day):
            day_schedule = []
            current_time = day_config.start_time
            available_attractions = [
                a for a in attractions if a.name not in used_attractions
            ]

            while (len(day_schedule) < self.config.max_attractions_per_day
                   and current_time < day_config.end_time
                   and available_attractions):

                # 找出當前時間可用的景點
                suitable_attractions = [
                    a for a in available_attractions
                    if self.__can_add_to_schedule(a, current_time, day_config)
                ]

                if not suitable_attractions:
                    break

                attraction = random.choice(suitable_attractions)
                available_attractions.remove(attraction)

                end_time = current_time + timedelta(hours=attraction.stay_time)
                day_schedule.append(
                    AttractionModify(attr=attraction,
                                     time_range=TimeRange(
                                         current_time, end_time)))
                current_time = end_time + self.config.travel_time

            if len(day_schedule) >= self.config.min_attractions_per_day:
                return day_schedule

        return []

    def __generate_one_schedule_with_timeslots(
            self) -> List[List[AttractionModify]]:
        """使用時間槽方式生成一個完整行程"""
        schedule = []
        used_attractions = set()

        for day_config in self.day_configs:
            time_slots = self.__create_time_slots(day_config)
            day_schedule = []

            for slot_start, slot_end in time_slots:
                if len(day_schedule) >= self.config.max_attractions_per_day:
                    break

                suitable_attractions = [
                    a for a in self.attractions
                    if (a.name not in used_attractions and
                        self.__can_add_to_schedule(a, slot_start, day_config))
                ]

                if suitable_attractions:
                    attraction = random.choice(suitable_attractions)
                    day_schedule.append(
                        AttractionModify(
                            attr=attraction,
                            time_range=TimeRange(
                                slot_start, slot_start +
                                timedelta(hours=attraction.stay_time))))
                    used_attractions.add(attraction.name)

            if len(day_schedule) >= self.config.min_attractions_per_day:
                schedule.append(day_schedule)
            else:
                return []

        return schedule if len(schedule) == len(self.day_configs) else []

    def __generate_day_schedule_from_clusters(
            self, clusters: Dict[Tuple[int, int],
                                 List[Attraction]], day_config: DayConfig,
            used_attractions: Set[str]) -> List[AttractionModify]:
        """從聚類中生成單天行程"""
        for _ in range(self.config.max_retry_per_day):
            day_schedule = []
            current_time = day_config.start_time

            # 依序嘗試每個時間段的景點群
            cluster_keys = sorted(clusters.keys())
            for key in cluster_keys:
                if len(day_schedule) >= self.config.max_attractions_per_day:
                    break

                available_attractions = [
                    a for a in clusters[key]
                    if (a.name not in used_attractions and self.
                        __can_add_to_schedule(a, current_time, day_config))
                ]

                if available_attractions:
                    attraction = random.choice(available_attractions)
                    end_time = current_time + timedelta(
                        hours=attraction.stay_time)
                    day_schedule.append(
                        AttractionModify(attr=attraction,
                                         time_range=TimeRange(
                                             current_time, end_time)))
                    current_time = end_time + self.config.travel_time

            if len(day_schedule) >= self.config.min_attractions_per_day:
                return day_schedule

        return []

    def __can_add_to_schedule(self, attraction: Attraction,
                              current_time: datetime,
                              day_config: DayConfig) -> bool:
        """檢查是否可以將景點添加到當前時間"""
        # 調整時間到當天
        attraction_open_time = datetime.combine(day_config.date.date(),
                                                attraction.open_time.time())
        attraction_close_time = datetime.combine(day_config.date.date(),
                                                 attraction.close_time.time())
        visit_end_time = current_time + timedelta(hours=attraction.stay_time)

        return (current_time >= attraction_open_time
                and visit_end_time <= attraction_close_time
                and visit_end_time <= day_config.end_time)

    def __create_time_slots(
            self, day_config: DayConfig) -> List[Tuple[datetime, datetime]]:
        """創建時間槽"""
        slots = []
        current = day_config.start_time
        while current < day_config.end_time:
            slot_end = min(current + timedelta(hours=2), day_config.end_time)
            slots.append((current, slot_end))
            current = slot_end
        return slots

    def __is_valid_schedule(self,
                            schedule: List[List[AttractionModify]]) -> bool:
        """檢查行程是否有效"""
        if len(schedule) != len(self.day_configs):
            return False

        all_attractions = set()
        for day_idx, day_schedule in enumerate(schedule):
            if not day_schedule:
                return False

            if len(day_schedule) < self.config.min_attractions_per_day:
                return False

            # 檢查時間順序
            for i in range(1, len(day_schedule)):
                if day_schedule[i - 1].time_range.end_time > day_schedule[
                        i].time_range.start_time:
                    return False

            # 檢查景點不重複
            for attr_mod in day_schedule:
                if attr_mod.attr.name in all_attractions:
                    return False
                all_attractions.add(attr_mod.attr.name)

            # 檢查是否符合當天的時間範圍
            day_config = self.day_configs[day_idx]
            for attr_mod in day_schedule:
                if (attr_mod.time_range.start_time < day_config.start_time
                        or attr_mod.time_range.end_time > day_config.end_time):
                    return False

        return True

    def __ensure_diversity(
        self, schedules: List[List[List[AttractionModify]]]
    ) -> List[List[List[AttractionModify]]]:
        """確保行程多樣性"""
        diverse_schedules = []
        schedules.sort(key=lambda x: self.__calculate_schedule_score(x),
                       reverse=True)

        for schedule in schedules:
            if not self.__is_too_similar(schedule, diverse_schedules):
                diverse_schedules.append(schedule)

        return diverse_schedules

    def __calculate_schedule_score(
            self, schedule: List[List[AttractionModify]]) -> float:
        """計算行程的綜合得分"""
        total_score = 0.0
        total_attractions = 0

        for day_schedule in schedule:
            day_score = 0.0
            for attr_mod in day_schedule:
                name = attr_mod.attr.name
                # 綜合評分、價格和受歡迎度
                attraction_score = (
                    self.attraction_stats['rating'][name] * 0.4 +
                    (1 - self.attraction_stats['price'][name]) * 0.3
                    +  # 價格越低分數越高
                    self.attraction_stats['popularity'][name] * 0.3)
                day_score += attraction_score
                total_attractions += 1

            total_score += day_score

        return total_score / total_attractions if total_attractions > 0 else 0

    def __is_too_similar(
            self, schedule: List[List[AttractionModify]],
            existing_schedules: List[List[List[AttractionModify]]]) -> bool:
        """檢查行程是否與現有行程過於相似"""
        schedule_attractions = set()
        for day_schedule in schedule:
            schedule_attractions.update(attr.attr.name
                                        for attr in day_schedule)

        for existing_schedule in existing_schedules:
            existing_attractions = set()
            for day_schedule in existing_schedule:
                existing_attractions.update(attr.attr.name
                                            for attr in day_schedule)

            intersection = len(
                schedule_attractions.intersection(existing_attractions))
            union = len(schedule_attractions.union(existing_attractions))

            if intersection / union > self.config.similarity_threshold:
                return True

        return False


class MultiDayInitIndividual:

    def __init__(self, attractions: List[Attraction],
                 day_configs: List[DayConfig],
                 place_additional_info: Dict[str, Dict[str, Any]]) -> None:
        self.generator = MultiDayScheduleGenerator(
            attractions=attractions,
            day_configs=day_configs,
            place_additional_info=place_additional_info)

    def getInitIndi(self):
        return self.generator.generate_population()


import unittest
from datetime import datetime, timedelta
from typing import List, Dict, Any


def print_multi_day_schedule(schedule, index: int,
                             day_configs: List[DayConfig]):
    """打印完整的多天行程详细信息"""
    print(f"\n========= 行程方案 {index + 1} =========")

    for day_idx, day_schedule in enumerate(schedule):
        print(
            f"\n--- 第 {day_idx + 1} 天 ({day_configs[day_idx].date.date()}) ---"
        )
        print(
            f"当天时间范围: {day_configs[day_idx].start_time.strftime('%H:%M')} - {day_configs[day_idx].end_time.strftime('%H:%M')}"
        )
        print(f"景点数量: {len(day_schedule)}")

        for i, attraction_modify in enumerate(day_schedule):
            print(f"\n{i + 1}. {attraction_modify.attr.name}")
            print(
                f"   到达时间: {attraction_modify.time_range.start_time.strftime('%Y-%m-%d %H:%M')}"
            )
            print(
                f"   离开时间: {attraction_modify.time_range.end_time.strftime('%Y-%m-%d %H:%M')}"
            )
            print(f"   停留时间: {attraction_modify.attr.stay_time:.1f}小时")
            print(
                f"   营业时间: {attraction_modify.attr.open_time.strftime('%H:%M')} - {attraction_modify.attr.close_time.strftime('%H:%M')}"
            )


def print_schedule_statistics(schedules: List[List[List[AttractionModify]]],
                              place_additional_info: Dict[str, Dict[str, Any]],
                              day_configs: List[DayConfig]):
    """打印多天行程统计信息"""
    print("\n========= 行程统计 =========")
    print(f"总行程方案数: {len(schedules)}")
    print(f"行程天数: {len(day_configs)}")

    # 计算每天平均景点数
    daily_attractions = []
    for schedule in schedules:
        for day_schedule in schedule:
            daily_attractions.append(len(day_schedule))
    avg_attractions_per_day = sum(daily_attractions) / len(daily_attractions)
    print(f"平均每天景点数: {avg_attractions_per_day:.1f}")

    # 统计每个景点被安排的频率
    attraction_counts = {}
    for schedule in schedules:
        for day_schedule in schedule:
            for attr_mod in day_schedule:
                attraction_counts[attr_mod.attr.name] = attraction_counts.get(
                    attr_mod.attr.name, 0) + 1

    print("\n景点使用频率统计:")
    for name, count in sorted(attraction_counts.items(),
                              key=lambda x: x[1],
                              reverse=True):
        print(f"- {name}: {count}次 ({(count / len(schedules) * 100):.1f}%)")

    # 统计类型分布
    category_counts = {}
    for schedule in schedules:
        for day_schedule in schedule:
            for attr_mod in day_schedule:
                place_info = place_additional_info.get(attr_mod.attr.name, {})
                categories = place_info.get('category', set())
                for category in categories:
                    category_counts[category] = category_counts.get(
                        category, 0) + 1

    print("\n景点类型统计:")
    for category, count in sorted(category_counts.items(),
                                  key=lambda x: x[1],
                                  reverse=True):
        print(f"- {category}: {count}次")


class TestMultiDayScheduleGenerator(unittest.TestCase):

    def setUp(self):
        """设置测试环境和测试数据"""
        self.attractions = self._create_test_attractions()
        self.day_configs = self._create_test_day_configs()
        self.place_additional_info = self._create_test_place_info()

        self.generator = MultiDayInitIndividual(
            attractions=self.attractions,
            day_configs=self.day_configs,
            place_additional_info=self.place_additional_info)

    def _create_test_attractions(self) -> List[Attraction]:
        """创建测试用的景点数据"""
        attractions_data = [
            {
                "name": "台北101",
                "open_time": "09:00",
                "close_time": "22:00",
                "stay_time": 2.0
            },
            {
                "name": "故宮博物館",
                "open_time": "08:30",
                "close_time": "18:30",
                "stay_time": 3.0
            },
            {
                "name": "龍山寺",
                "open_time": "08:00",
                "close_time": "19:00",
                "stay_time": 1.5
            },
            {
                "name": "士林夜市",
                "open_time": "16:00",
                "close_time": "23:59",
                "stay_time": 2.0
            },
            {
                "name": "中正紀念堂",
                "open_time": "09:00",
                "close_time": "18:00",
                "stay_time": 2.0
            },
            {
                "name": "象山步道",
                "open_time": "06:00",
                "close_time": "18:00",
                "stay_time": 2.5
            },
            {
                "name": "台北動物園",
                "open_time": "09:00",
                "close_time": "17:00",
                "stay_time": 4.0
            },
            {
                "name": "西門町",
                "open_time": "11:00",
                "close_time": "22:00",
                "stay_time": 3.0
            },
            {
                "name": "國立美術館",
                "open_time": "09:30",
                "close_time": "17:30",
                "stay_time": 2.0
            },
            {
                "name": "陽明山溫泉",
                "open_time": "10:00",
                "close_time": "22:00",
                "stay_time": 3.0
            },
        ]

        return [
            Attraction(name=data["name"],
                       open_time=datetime.strptime(data["open_time"], "%H:%M"),
                       close_time=datetime.strptime(data["close_time"],
                                                    "%H:%M"),
                       stay_time=data["stay_time"])
            for data in attractions_data
        ]

    def _create_test_day_configs(self) -> List[DayConfig]:
        """创建测试用的多天行程配置"""
        start_date = datetime(2024, 3, 20)  # 从3月20日开始的三天行程
        day_configs = []

        # 创建三天的配置
        for i in range(3):
            current_date = start_date + timedelta(days=i)
            day_configs.append(
                DayConfig(date=current_date,
                          start_time=datetime.combine(
                              current_date.date(),
                              datetime.strptime("09:00", "%H:%M").time()),
                          end_time=datetime.combine(
                              current_date.date(),
                              datetime.strptime("21:00", "%H:%M").time())))

        return day_configs

    def _create_test_place_info(self) -> Dict[str, Dict[str, Any]]:
        """创建测试用的地点附加信息"""
        return {
            "台北101": {
                "price_level": 4,
                "rating": 4.6,
                "user_rating_totals": 20000,
                "category": {"landmark", "view_point"}
            },
            "故宮博物館": {
                "price_level": 3,
                "rating": 4.7,
                "user_rating_totals": 25000,
                "category": {"museum", "culture"}
            },
            "龍山寺": {
                "price_level": 1,
                "rating": 4.5,
                "user_rating_totals": 15000,
                "category": {"temple", "culture"}
            },
            "士林夜市": {
                "price_level": 2,
                "rating": 4.3,
                "user_rating_totals": 30000,
                "category": {"market", "food"}
            },
            "中正紀念堂": {
                "price_level": 1,
                "rating": 4.4,
                "user_rating_totals": 22000,
                "category": {"landmark", "culture"}
            },
            "象山步道": {
                "price_level": 1,
                "rating": 4.5,
                "user_rating_totals": 18000,
                "category": {"nature", "outdoor"}
            },
            "台北動物園": {
                "price_level": 2,
                "rating": 4.3,
                "user_rating_totals": 20000,
                "category": {"zoo", "family"}
            },
            "西門町": {
                "price_level": 2,
                "rating": 4.2,
                "user_rating_totals": 25000,
                "category": {"shopping", "food"}
            },
            "國立美術館": {
                "price_level": 2,
                "rating": 4.4,
                "user_rating_totals": 12000,
                "category": {"museum", "art"}
            },
            "陽明山溫泉": {
                "price_level": 3,
                "rating": 4.3,
                "user_rating_totals": 15000,
                "category": {"nature", "leisure"}
            }
        }

    def test_generate_and_print_schedules(self):
        """生成行程并打印详细信息"""
        print("\n=== 开始生成多天行程测试 ===")
        print(f"测试天数: {len(self.day_configs)}")
        print(f"测试景点数量: {len(self.attractions)}")
        print("\n每天时间范围:")
        for i, config in enumerate(self.day_configs):
            print(
                f"第{i + 1}天 ({config.date.date()}): "
                f"{config.start_time.strftime('%H:%M')} - {config.end_time.strftime('%H:%M')}"
            )

        # 生成行程
        schedules = self.generator.getInitIndi()

        # 打印每个行程的详细信息
        for i, schedule in enumerate(schedules):
            print_multi_day_schedule(schedule, i, self.day_configs)

        # 打印统计信息
        print_schedule_statistics(schedules, self.place_additional_info,
                                  self.day_configs)

        # 基本验证
        self._validate_schedules(schedules)

        return schedules

    def _validate_schedules(self, schedules):
        """验证生成的行程是否符合基本要求"""
        for schedule_idx, schedule in enumerate(schedules):
            # 检查天数
            self.assertEqual(len(schedule), len(self.day_configs),
                             f"行程{schedule_idx + 1}的天数不正确")

            # 收集所有景点以检查重复
            all_attractions = set()

            # 检查每天的行程
            for day_idx, day_schedule in enumerate(schedule):
                day_config = self.day_configs[day_idx]

                # 检查景点数量限制
                self.assertGreaterEqual(
                    len(day_schedule), 2,
                    f"行程{schedule_idx + 1}第{day_idx + 1}天的景点数量过少")
                self.assertLessEqual(
                    len(day_schedule), 5,
                    f"行程{schedule_idx + 1}第{day_idx + 1}天的景点数量过多")

                # 检查时间顺序和重复
                for i, attr_mod in enumerate(day_schedule):
                    # 检查景点重复
                    self.assertNotIn(
                        attr_mod.attr.name, all_attractions,
                        f"行程{schedule_idx + 1}中景点{attr_mod.attr.name}重复出现")
                    all_attractions.add(attr_mod.attr.name)

                    # 检查时间顺序
                    if i > 0:
                        self.assertLess(
                            day_schedule[i - 1].time_range.end_time,
                            attr_mod.time_range.start_time,
                            f"行程{schedule_idx + 1}第{day_idx + 1}天的时间顺序有误")

                    # 检查是否在当天的时间范围内
                    self.assertGreaterEqual(
                        attr_mod.time_range.start_time, day_config.start_time,
                        f"行程{schedule_idx + 1}第{day_idx + 1}天的景点{attr_mod.attr.name}开始时间过早"
                    )
                    self.assertLessEqual(
                        attr_mod.time_range.end_time, day_config.end_time,
                        f"行程{schedule_idx + 1}第{day_idx + 1}天的景点{attr_mod.attr.name}结束时间过晚"
                    )


if __name__ == '__main__':
    # 创建测试实例
    test = TestMultiDayScheduleGenerator()
    test.setUp()

    # 运行测试并打印结果
    try:
        schedules = test.test_generate_and_print_schedules()
        print("\n=== 测试完成 ===")
        print("所有行程生成和验证都成功完成！")
    except AssertionError as e:
        print("\n=== 测试失败 ===")
        print("错误信息:", str(e))
