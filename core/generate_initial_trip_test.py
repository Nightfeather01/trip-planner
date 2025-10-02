from datetime import datetime

from generate_initial_trip import DiverseScheduleGenerator

'''
generator = DiverseScheduleGenerator(
    attractions=self.attractionsDetail,
    start_time=datetime.strptime("08:00", "%H:%M"),
    end_time=datetime.strptime("22:00", "%H:%M"),
    place_additional_info=self.place_additional_info
)

# 生成初始行程
schedules = generator.generate_population()

print('population in problem.py')
for schedule in schedules:
    check_duplicate = set()
    for attraction_modify in schedule:
        if attraction_modify.attr.name in check_duplicate:
            print('error id is duplicate')
            exit()
        check_duplicate.add(attraction_modify.attr.name)
        print(
            f"{attraction_modify.attr.name}, {attraction_modify.time_range.start_time}, {attraction_modify.time_range.end_time}")
        
'''



import unittest
from datetime import datetime, timedelta
from typing import List, Dict, Any
from core.generate_initial_trip import DiverseScheduleGenerator, Attraction

def print_schedule(schedule, index: int):
    """印出單一行程的詳細資訊"""
    print(f"\n=== 行程 {index + 1} ===")
    print(f"景點數量: {len(schedule)}")

    for i, attraction_modify in enumerate(schedule):
        print(f"\n{i + 1}. {attraction_modify.attr.name}")
        print(f"   到達時間: {attraction_modify.time_range.start_time.strftime('%H:%M')}")
        print(f"   離開時間: {attraction_modify.time_range.end_time.strftime('%H:%M')}")
        print(f"   停留時間: {attraction_modify.attr.stay_time:.1f}小時")
        print(f"   營業時間: {attraction_modify.attr.open_time.strftime('%H:%M')} - {attraction_modify.attr.close_time.strftime('%H:%M')}")

def print_schedule_statistics(schedules, place_additional_info):
    """印出行程統計資訊"""
    print("\n=== 行程統計 ===")
    print(f"總行程數: {len(schedules)}")

    # 計算平均景點數
    avg_attractions = sum(len(schedule) for schedule in schedules) / len(schedules)
    print(f"平均景點數: {avg_attractions:.1f}")

    # 統計各類型景點出現次數
    category_counts = {}
    for schedule in schedules:
        for attr_mod in schedule:
            place_info = place_additional_info.get(attr_mod.attr.name, {})
            categories = place_info.get('category', set())
            for category in categories:
                category_counts[category] = category_counts.get(category, 0) + 1

    print("\n景點類型統計:")
    for category, count in sorted(category_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"- {category}: {count}次")

class TestDiverseScheduleGenerator(unittest.TestCase):
    def setUp(self):
        """設置測試環境和測試資料"""
        self.attractions = self._create_test_attractions()
        self.start_time = datetime.strptime("08:00", "%H:%M")
        self.end_time = datetime.strptime("22:00", "%H:%M")
        self.place_additional_info = self._create_test_place_info()

        self.generator = DiverseScheduleGenerator(
            attractions=self.attractions,
            start_time=self.start_time,
            end_time=self.end_time,
            place_additional_info=self.place_additional_info
        )

    def _create_test_attractions(self) -> List[Attraction]:
        """創建測試用的景點資料"""
        attractions = []

        test_attractions_data = [
            {
                "name": "國立故宮博物院",
                "open_time": datetime.strptime("08:30", "%H:%M"),
                "close_time": datetime.strptime("18:30", "%H:%M"),
                "stay_time": 3.0
            },
            {
                "name": "台北101觀景台",
                "open_time": datetime.strptime("09:00", "%H:%M"),
                "close_time": datetime.strptime("22:00", "%H:%M"),
                "stay_time": 2.0
            },
            {
                "name": "龍山寺",
                "open_time": datetime.strptime("08:00", "%H:%M"),
                "close_time": datetime.strptime("19:00", "%H:%M"),
                "stay_time": 1.5
            },
            {
                "name": "士林夜市",
                "open_time": datetime.strptime("16:00", "%H:%M"),
                "close_time": datetime.strptime("23:59", "%H:%M"),
                "stay_time": 2.0
            },
            {
                "name": "鼎泰豐信義店",
                "open_time": datetime.strptime("10:00", "%H:%M"),
                "close_time": datetime.strptime("21:00", "%H:%M"),
                "stay_time": 1.5
            },
            {
                "name": "陽明山國家公園",
                "open_time": datetime.strptime("08:00", "%H:%M"),
                "close_time": datetime.strptime("17:00", "%H:%M"),
                "stay_time": 3.0
            },
            {
                "name": "中正紀念堂",
                "open_time": datetime.strptime("09:00", "%H:%M"),
                "close_time": datetime.strptime("18:00", "%H:%M"),
                "stay_time": 2.0
            }
        ]

        for attr_data in test_attractions_data:
            attraction = Attraction(
                name=attr_data["name"],
                open_time=attr_data["open_time"],
                close_time=attr_data["close_time"],
                stay_time=attr_data["stay_time"]
            )
            attractions.append(attraction)

        return attractions

    def _create_test_place_info(self) -> Dict[str, Dict[str, Any]]:
        """創建測試用的地點額外資訊"""
        return {
            "國立故宮博物院": {
                "price_level": 3,
                "rating": 4.7,
                "user_rating_totals": 25000,
                "category": {"museum", "tourist_attraction", "culture"}
            },
            "台北101觀景台": {
                "price_level": 4,
                "rating": 4.6,
                "user_rating_totals": 20000,
                "category": {"tourist_attraction", "viewpoint"}
            },
            "龍山寺": {
                "price_level": 1,
                "rating": 4.5,
                "user_rating_totals": 15000,
                "category": {"temple", "tourist_attraction", "culture"}
            },
            "士林夜市": {
                "price_level": 2,
                "rating": 4.3,
                "user_rating_totals": 30000,
                "category": {"market", "food", "shopping"}
            },
            "鼎泰豐信義店": {
                "price_level": 3,
                "rating": 4.6,
                "user_rating_totals": 12000,
                "category": {"restaurant", "food"}
            },
            "陽明山國家公園": {
                "price_level": 1,
                "rating": 4.5,
                "user_rating_totals": 18000,
                "category": {"park", "nature", "tourist_attraction"}
            },
            "中正紀念堂": {
                "price_level": 1,
                "rating": 4.4,
                "user_rating_totals": 22000,
                "category": {"monument", "tourist_attraction", "culture"}
            }
        }

    def test_generate_and_print_schedules(self):
        """生成行程並印出詳細資訊"""
        print("\n=== 開始生成行程測試 ===")
        print("測試時間範圍:", self.start_time.strftime('%H:%M'), "-", self.end_time.strftime('%H:%M'))
        print("測試景點數量:", len(self.attractions))

        # 生成行程
        schedules = self.generator.generate_population()

        # 印出每個行程的詳細資訊
        for i, schedule in enumerate(schedules):
            print_schedule(schedule, i)

        # 印出統計資訊
        print_schedule_statistics(schedules, self.place_additional_info)

        # 基本驗證
        self._validate_schedules(schedules)

        return schedules

    def _validate_schedules(self, schedules):
        """驗證生成的行程是否符合基本要求"""
        for schedule in schedules:
            # 檢查景點數量限制
            self.assertGreaterEqual(len(schedule), self.generator.config.min_attractions)
            self.assertLessEqual(len(schedule), self.generator.config.max_attractions)

            # 檢查時間順序和營業時間限制
            visited = set()
            for i, attr_mod in enumerate(schedule):
                # 檢查重複景點
                self.assertNotIn(attr_mod.attr.name, visited)
                visited.add(attr_mod.attr.name)

                # 檢查時間順序
                if i > 0:
                    prev_end = schedule[i-1].time_range.end_time
                    curr_start = attr_mod.time_range.start_time
                    self.assertLessEqual(prev_end, curr_start)

                # 檢查營業時間限制
                self.assertGreaterEqual(
                    attr_mod.time_range.start_time,
                    attr_mod.attr.open_time
                )
                self.assertLessEqual(
                    attr_mod.time_range.end_time,
                    attr_mod.attr.close_time
                )

if __name__ == '__main__':
    # 建立測試實例
    test = TestDiverseScheduleGenerator()
    test.setUp()

    # 運行測試並印出結果
    try:
        schedules = test.test_generate_and_print_schedules()
        print("\n=== 測試完成 ===")
        print("所有行程生成和驗證都成功完成！")
    except AssertionError as e:
        print("\n=== 測試失敗 ===")
        print("錯誤信息:", str(e))
