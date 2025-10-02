import unittest
from datetime import datetime, timedelta
from typing import List, Dict, Any
from generate_multiple_day_trip import (
    Attraction,
    TimeRange,
    AttractionModify,
    DayConfig,
    MultiDayScheduleGenerator,
    MultiDayInitIndividual
)


class TestMultiDayTripGeneration(unittest.TestCase):
    def setUp(self):
        """Set up test data and configurations"""
        self.attractions = self._create_test_attractions()
        self.day_configs = self._create_test_day_configs()
        self.place_additional_info = self._create_test_place_info()

        # Initialize the generator
        self.generator = MultiDayInitIndividual(
            attractions=self.attractions,
            day_configs=self.day_configs,
            place_additional_info=self.place_additional_info
        )

    def _create_test_attractions(self) -> List[Attraction]:
        """Create test attraction data with more diverse options"""
        attractions_data = [
            # 早上開放的景點
            {
                "name": "國立博物館",
                "open_time": "08:30",
                "close_time": "17:30",
                "stay_time": 2.5
            },
            {
                "name": "動物園",
                "open_time": "09:00",
                "close_time": "17:00",
                "stay_time": 4.0
            },
            {
                "name": "植物園",
                "open_time": "08:00",
                "close_time": "16:30",
                "stay_time": 2.0
            },
            {
                "name": "歷史博物館",
                "open_time": "09:30",
                "close_time": "18:00",
                "stay_time": 2.5
            },
            # 全天開放的景點
            {
                "name": "中央公園",
                "open_time": "06:00",
                "close_time": "22:00",
                "stay_time": 1.5
            },
            {
                "name": "城市展望台",
                "open_time": "10:00",
                "close_time": "21:00",
                "stay_time": 1.0
            },
            {
                "name": "藝術中心",
                "open_time": "10:00",
                "close_time": "20:00",
                "stay_time": 2.0
            },
            # 下午至晚上的景點
            {
                "name": "美食街",
                "open_time": "11:00",
                "close_time": "22:00",
                "stay_time": 2.0
            },
            {
                "name": "夜市",
                "open_time": "16:00",
                "close_time": "23:59",
                "stay_time": 2.5
            },
            {
                "name": "購物中心",
                "open_time": "11:00",
                "close_time": "21:30",
                "stay_time": 2.0
            },
            # 文化景點
            {
                "name": "古蹟寺廟",
                "open_time": "07:00",
                "close_time": "17:30",
                "stay_time": 1.0
            },
            {
                "name": "傳統市場",
                "open_time": "06:00",
                "close_time": "14:00",
                "stay_time": 1.5
            },
            {
                "name": "文化園區",
                "open_time": "09:00",
                "close_time": "18:00",
                "stay_time": 3.0
            },
            # 戶外活動
            {
                "name": "登山步道",
                "open_time": "05:00",
                "close_time": "19:00",
                "stay_time": 3.0
            },
            {
                "name": "海濱公園",
                "open_time": "08:00",
                "close_time": "20:00",
                "stay_time": 2.0
            },
            # 特色景點
            {
                "name": "溫泉會館",
                "open_time": "10:00",
                "close_time": "23:00",
                "stay_time": 2.5
            },
            {
                "name": "觀光工廠",
                "open_time": "09:30",
                "close_time": "17:30",
                "stay_time": 1.5
            },
            {
                "name": "遊樂園",
                "open_time": "10:00",
                "close_time": "19:00",
                "stay_time": 5.0
            },
            # 餐飲場所
            {
                "name": "特色餐廳",
                "open_time": "11:30",
                "close_time": "21:30",
                "stay_time": 1.5
            },
            {
                "name": "咖啡街區",
                "open_time": "10:00",
                "close_time": "22:00",
                "stay_time": 1.0
            }
        ]

        return [
            Attraction(
                name=data["name"],
                open_time=datetime.strptime(data["open_time"], "%H:%M"),
                close_time=datetime.strptime(data["close_time"], "%H:%M"),
                stay_time=data["stay_time"]
            )
            for data in attractions_data
        ]

    def _create_test_day_configs(self) -> List[DayConfig]:
        """Create test day configurations"""
        base_date = datetime(2024, 3, 20)
        configs = []

        for i in range(3):  # Create 3-day trip
            current_date = base_date + timedelta(days=i)
            configs.append(
                DayConfig(
                    date=current_date,
                    start_time=datetime.combine(current_date.date(),
                                                datetime.strptime("09:00", "%H:%M").time()),
                    end_time=datetime.combine(current_date.date(),
                                              datetime.strptime("21:00", "%H:%M").time())
                )
            )
        return configs

    def _create_test_place_info(self) -> Dict[str, Dict[str, Any]]:
        """Create test place additional information"""
        place_info = {
            # 博物館和文化設施
            "國立博物館": {
                "price_level": 2,
                "rating": 4.5,
                "user_rating_totals": 3000,
                "category": {"museum", "culture", "indoor"}
            },
            "歷史博物館": {
                "price_level": 2,
                "rating": 4.3,
                "user_rating_totals": 2500,
                "category": {"museum", "culture", "indoor"}
            },
            "藝術中心": {
                "price_level": 2,
                "rating": 4.2,
                "user_rating_totals": 1800,
                "category": {"museum", "art", "indoor"}
            },
            # 自然和戶外景點
            "動物園": {
                "price_level": 3,
                "rating": 4.4,
                "user_rating_totals": 5000,
                "category": {"outdoor", "nature", "family"}
            },
            "植物園": {
                "price_level": 1,
                "rating": 4.2,
                "user_rating_totals": 2000,
                "category": {"outdoor", "nature"}
            },
            "中央公園": {
                "price_level": 0,
                "rating": 4.6,
                "user_rating_totals": 4500,
                "category": {"outdoor", "nature", "park"}
            },
            "登山步道": {
                "price_level": 0,
                "rating": 4.7,
                "user_rating_totals": 3200,
                "category": {"outdoor", "nature", "sports"}
            },
            "海濱公園": {
                "price_level": 1,
                "rating": 4.3,
                "user_rating_totals": 2800,
                "category": {"outdoor", "nature", "park"}
            },
            # 購物和娛樂
            "購物中心": {
                "price_level": 3,
                "rating": 4.1,
                "user_rating_totals": 6000,
                "category": {"shopping", "indoor", "entertainment"}
            },
            "夜市": {
                "price_level": 1,
                "rating": 4.4,
                "user_rating_totals": 7000,
                "category": {"food", "shopping", "nightlife"}
            },
            "美食街": {
                "price_level": 2,
                "rating": 4.2,
                "user_rating_totals": 4000,
                "category": {"food", "restaurant"}
            },
            # 觀光景點
            "城市展望台": {
                "price_level": 3,
                "rating": 4.6,
                "user_rating_totals": 5500,
                "category": {"landmark", "viewpoint"}
            },
            "古蹟寺廟": {
                "price_level": 0,
                "rating": 4.5,
                "user_rating_totals": 3500,
                "category": {"culture", "religious", "landmark"}
            },
            "文化園區": {
                "price_level": 2,
                "rating": 4.3,
                "user_rating_totals": 2800,
                "category": {"culture", "art", "outdoor"}
            },
            # 特色場所
            "溫泉會館": {
                "price_level": 4,
                "rating": 4.4,
                "user_rating_totals": 2000,
                "category": {"leisure", "spa"}
            },
            "觀光工廠": {
                "price_level": 2,
                "rating": 4.0,
                "user_rating_totals": 1500,
                "category": {"industry", "education", "indoor"}
            },
            "遊樂園": {
                "price_level": 4,
                "rating": 4.5,
                "user_rating_totals": 8000,
                "category": {"amusement", "family", "outdoor"}
            },
            # 市場和在地特色
            "傳統市場": {
                "price_level": 1,
                "rating": 4.2,
                "user_rating_totals": 2500,
                "category": {"market", "food", "local"}
            },
            "特色餐廳": {
                "price_level": 3,
                "rating": 4.4,
                "user_rating_totals": 3000,
                "category": {"restaurant", "food"}
            },
            "咖啡街區": {
                "price_level": 2,
                "rating": 4.3,
                "user_rating_totals": 2200,
                "category": {"cafe", "food", "leisure"}
            }
        }
        return place_info

    def test_schedule_generation(self):
        """Test basic schedule generation"""
        schedules = self.generator.getInitIndi()

        # Test that schedules were generated
        self.assertIsNotNone(schedules)
        self.assertGreater(len(schedules), 0)

        # Test structure of generated schedules
        for schedule in schedules:
            # Check number of days
            self.assertEqual(len(schedule), len(self.day_configs))

            # Check each day's schedule
            for day_schedule in schedule:
                self._validate_day_schedule(day_schedule)

        idx = 0
        for schedule in schedules:
            print(f"{idx}'s schedule")
            for day_schedule in schedule:
                for i, attr_modify in enumerate(day_schedule):
                    print(f"{attr_modify.attr.name} {attr_modify.time_range.start_time} {attr_modify.time_range.end_time}")

            print()
            idx += 1

    def test_time_constraints(self):
        """Test that generated schedules respect time constraints"""
        schedules = self.generator.getInitIndi()

        for schedule in schedules:
            for day_idx, day_schedule in enumerate(schedule):
                day_config = self.day_configs[day_idx]

                for attr_mod in day_schedule:
                    # Check if within day's time range
                    self.assertGreaterEqual(
                        attr_mod.time_range.start_time,
                        day_config.start_time
                    )
                    self.assertLessEqual(
                        attr_mod.time_range.end_time,
                        day_config.end_time
                    )

                    # Check if within attraction's opening hours
                    attraction_open = datetime.combine(
                        attr_mod.time_range.start_time.date(),
                        attr_mod.attr.open_time.time()
                    )
                    attraction_close = datetime.combine(
                        attr_mod.time_range.start_time.date(),
                        attr_mod.attr.close_time.time()
                    )

                    self.assertGreaterEqual(
                        attr_mod.time_range.start_time,
                        attraction_open
                    )
                    self.assertLessEqual(
                        attr_mod.time_range.end_time,
                        attraction_close
                    )

    def test_no_overlap(self):
        """Test that attractions don't overlap in time"""
        schedules = self.generator.getInitIndi()

        for schedule in schedules:
            for day_schedule in schedule:
                for i in range(1, len(day_schedule)):
                    self.assertLess(
                        day_schedule[i - 1].time_range.end_time,
                        day_schedule[i].time_range.start_time,
                        "Found overlapping attractions in schedule"
                    )

    def test_no_duplicate_attractions(self):
        """Test that no attraction appears more than once in entire trip"""
        schedules = self.generator.getInitIndi()

        for schedule in schedules:
            used_attractions = set()
            for day_schedule in schedule:
                for attr_mod in day_schedule:
                    self.assertNotIn(
                        attr_mod.attr.name,
                        used_attractions,
                        f"Found duplicate attraction: {attr_mod.attr.name}"
                    )
                    used_attractions.add(attr_mod.attr.name)

    def test_stay_time_respect(self):
        """Test that stay times are respected in schedule"""
        schedules = self.generator.getInitIndi()

        for schedule in schedules:
            for day_schedule in schedule:
                for attr_mod in day_schedule:
                    expected_duration = timedelta(hours=attr_mod.attr.stay_time)
                    actual_duration = attr_mod.time_range.end_time - attr_mod.time_range.start_time
                    self.assertEqual(
                        expected_duration,
                        actual_duration,
                        f"Stay time not respected for {attr_mod.attr.name}"
                    )

    def test_restaurant_distribution(self):
        """Test that restaurants are properly distributed across days"""
        schedules = self.generator.getInitIndi()

        for schedule in schedules:
            for day_schedule in schedule:
                # Count restaurants in each day
                restaurant_count = sum(
                    1 for attr_mod in day_schedule
                    if any(category in ['restaurant', 'food', 'cafe']
                           for category in self.place_additional_info[attr_mod.attr.name]['category'])
                )
                # Should not have more than 2 restaurants per day
                self.assertLessEqual(
                    restaurant_count,
                    2,
                    "Found too many restaurants in one day"
                )

    def test_attraction_distribution(self):
        """Test that different types of attractions are well distributed"""
        schedules = self.generator.getInitIndi()

        for schedule in schedules:
            categories = set()
            for day_schedule in schedule:
                for attr_mod in day_schedule:
                    categories.update(
                        self.place_additional_info[attr_mod.attr.name]['category']
                    )

            # Should have a good mix of indoor and outdoor activities
            self.assertTrue(
                'indoor' in categories and 'outdoor' in categories,
                "Schedule lacks balance between indoor and outdoor activities"
            )

            # Should have some cultural elements
            self.assertTrue(
                any(cat in categories for cat in ['culture', 'museum', 'art']),
                "Schedule lacks cultural activities"
            )

    def test_timing_distribution(self):
        """Test that activities are well-distributed throughout the day"""
        schedules = self.generator.getInitIndi()

        for schedule in schedules:
            for day_schedule in schedule:
                if len(day_schedule) >= 2:
                    # Calculate time gaps between attractions
                    gaps = []
                    for i in range(1, len(day_schedule)):
                        gap = (day_schedule[i].time_range.start_time -
                               day_schedule[i - 1].time_range.end_time).total_seconds() / 3600
                        gaps.append(gap)

                    # Check that gaps are reasonable (not too long)
                    for gap in gaps:
                        self.assertLessEqual(
                            gap,
                            2.0,  # Maximum 2 hours gap
                            "Found too large gap between attractions"
                        )

    def test_schedule_feasibility(self):
        """Test that schedules are practically feasible"""
        schedules = self.generator.getInitIndi()

        for schedule in schedules:
            for day_schedule in schedule:
                # Test daily duration
                if day_schedule:
                    day_start = day_schedule[0].time_range.start_time
                    day_end = day_schedule[-1].time_range.end_time
                    duration = (day_end - day_start).total_seconds() / 3600

                    # Day should not be too long or too short
                    self.assertGreaterEqual(duration, 4.0, "Day schedule too short")
                    self.assertLessEqual(duration, 12.0, "Day schedule too long")

    def test_attraction_compatibility(self):
        """Test that nearby attractions are scheduled together when possible"""
        schedules = self.generator.getInitIndi()

        for schedule in schedules:
            for day_schedule in schedule:
                categories_by_time = {}
                for attr_mod in day_schedule:
                    hour = attr_mod.time_range.start_time.hour
                    if hour not in categories_by_time:
                        categories_by_time[hour] = set()
                    categories_by_time[hour].update(
                        self.place_additional_info[attr_mod.attr.name]['category']
                    )

                # Check logical sequence of activities
                # e.g., avoid scheduling intense activities right after meals
                for hour in range(min(categories_by_time.keys()), max(categories_by_time.keys())):
                    if hour in categories_by_time and hour + 1 in categories_by_time:
                        if 'restaurant' in categories_by_time[hour]:
                            # After restaurant, should not have intense activities
                            self.assertFalse(
                                any(cat in ['sports', 'hiking']
                                    for cat in categories_by_time.get(hour + 1, set())),
                                "Found intense activity scheduled right after meal"
                            )

    def test_price_distribution(self):
        """Test that expenses are reasonably distributed"""
        schedules = self.generator.getInitIndi()

        for schedule in schedules:
            for day_schedule in schedule:
                # Calculate daily expenses
                daily_price_level = sum(
                    self.place_additional_info[attr_mod.attr.name]['price_level']
                    for attr_mod in day_schedule
                )

                # Check that daily expenses are within reasonable limits
                self.assertLessEqual(
                    daily_price_level,
                    15,  # Arbitrary maximum daily price level sum
                    "Daily expenses too high"
                )

    def test_popular_attractions_inclusion(self):
        """Test that popular attractions are included in the schedules"""
        schedules = self.generator.getInitIndi()

        for schedule in schedules:
            # Get all attractions in the schedule
            included_attractions = set()
            for day_schedule in schedule:
                for attr_mod in day_schedule:
                    included_attractions.add(attr_mod.attr.name)

            # Find high-rated attractions
            high_rated = {
                name for name, info in self.place_additional_info.items()
                if info['rating'] >= 4.5 and info['user_rating_totals'] >= 5000
            }

            # Should include at least some popular attractions
            self.assertTrue(
                len(included_attractions.intersection(high_rated)) > 0,
                "Schedule doesn't include any popular attractions"
            )

    def test_schedule_printability(self):
        """Test that schedules can be properly formatted for display"""
        schedules = self.generator.getInitIndi()

        for schedule_idx, schedule in enumerate(schedules):
            try:
                self._print_schedule(schedule, schedule_idx)
            except Exception as e:
                self.fail(f"Failed to print schedule: {str(e)}")

    def _print_schedule(self, schedule, schedule_idx):
        """Helper method to print schedule in readable format"""
        print(f"\nSchedule {schedule_idx + 1}")
        for day_idx, day_schedule in enumerate(schedule):
            print(f"\nDay {day_idx + 1}")
            for attr_mod in day_schedule:
                print(
                    f"  {attr_mod.time_range.start_time.strftime('%H:%M')} - "
                    f"{attr_mod.time_range.end_time.strftime('%H:%M')}: "
                    f"{attr_mod.attr.name}"
                )

    def _validate_day_schedule(self, day_schedule: List[AttractionModify]):
        """Helper method to validate a single day's schedule"""
        # Check that day has reasonable number of attractions
        self.assertGreater(len(day_schedule), 0, "Day schedule empty")
        self.assertLessEqual(len(day_schedule), 8, "Too many attractions in one day")

        # Check time sequence
        for i in range(1, len(day_schedule)):
            self.assertLess(
                day_schedule[i - 1].time_range.end_time,
                day_schedule[i].time_range.start_time,
                "Time sequence violation"
            )

        # Check attraction validity
        for attr_mod in day_schedule:
            self.assertIsInstance(attr_mod, AttractionModify)
            self.assertIsInstance(attr_mod.attr, Attraction)
            self.assertIsInstance(attr_mod.time_range, TimeRange)

            # Verify attraction exists in test data
            self.assertIn(
                attr_mod.attr.name,
                self.place_additional_info,
                f"Invalid attraction: {attr_mod.attr.name}"
            )

if __name__ == '__main__':
    unittest.main(verbosity=2)