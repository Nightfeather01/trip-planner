
import unittest
from datetime import datetime, timedelta
from generate_multiple_day_trip import (
    Attraction,
    TimeRange,
    AttractionModify,
    DayConfig,
    MultiDayScheduleGenerator,
    MultiDayInitIndividual
)


class TestMultipleDayTripGenerator(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures for all tests"""
        self.attractions = self._create_test_attractions()
        self.day_configs = self._create_test_day_configs()
        self.place_additional_info = self._create_test_place_info()

        # Initialize the generator
        self.generator = MultiDayInitIndividual(
            attractions=self.attractions,
            day_configs=self.day_configs,
            place_additional_info=self.place_additional_info
        )

    def _create_test_attractions(self):
        """Create a set of test attractions"""
        test_data = [
            ("Museum A", "09:00", "17:00", 2.0),
            ("Park B", "08:00", "20:00", 1.5),
            ("Restaurant C", "11:00", "23:00", 1.0),
            ("Gallery D", "10:00", "18:00", 1.5),
            ("Monument E", "09:00", "19:00", 1.0),
            ("Market F", "07:00", "22:00", 2.0),
            ("Temple G", "06:00", "18:00", 1.5),
            ("Theater H", "12:00", "23:00", 2.5),
        ]

        return [
            Attraction(
                name=name,
                open_time=datetime.strptime(open_time, "%H:%M"),
                close_time=datetime.strptime(close_time, "%H:%M"),
                stay_time=stay_time
            )
            for name, open_time, close_time, stay_time in test_data
        ]

    def _create_test_day_configs(self):
        """Create test day configurations"""
        start_date = datetime(2024, 3, 20)
        configs = []

        for i in range(3):  # Create a 3-day trip
            current_date = start_date + timedelta(days=i)
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

    def _create_test_place_info(self):
        """Create test place additional information"""
        return {
            "Museum A": {
                "price_level": 3,
                "rating": 4.5,
                "user_rating_totals": 1000,
                "category": {"museum", "culture"}
            },
            "Park B": {
                "price_level": 1,
                "rating": 4.3,
                "user_rating_totals": 2000,
                "category": {"nature", "outdoor"}
            },
            "Restaurant C": {
                "price_level": 2,
                "rating": 4.2,
                "user_rating_totals": 1500,
                "category": {"restaurant", "food"}
            },
            "Gallery D": {
                "price_level": 2,
                "rating": 4.4,
                "user_rating_totals": 800,
                "category": {"museum", "art"}
            },
            "Monument E": {
                "price_level": 1,
                "rating": 4.6,
                "user_rating_totals": 3000,
                "category": {"landmark", "culture"}
            },
            "Market F": {
                "price_level": 1,
                "rating": 4.1,
                "user_rating_totals": 2500,
                "category": {"market", "food"}
            },
            "Temple G": {
                "price_level": 1,
                "rating": 4.7,
                "user_rating_totals": 1800,
                "category": {"temple", "culture"}
            },
            "Theater H": {
                "price_level": 3,
                "rating": 4.3,
                "user_rating_totals": 1200,
                "category": {"entertainment", "culture"}
            }
        }

    def test_schedule_generation(self):
        """Test basic schedule generation"""
        schedules = self.generator.getInitIndi()

        # Test that we got some schedules
        self.assertGreater(len(schedules), 0, "No schedules were generated")

        # Test schedule structure
        self.assertEqual(len(schedules[0]), len(self.day_configs),
                         "Schedule doesn't match requested number of days")

    def test_schedule_constraints(self):
        """Test that generated schedules meet basic constraints"""
        schedules = self.generator.getInitIndi()

        for schedule in schedules:
            # Test for correct number of days
            self.assertEqual(len(schedule), len(self.day_configs))

            used_attractions = set()
            for day_idx, day_schedule in enumerate(schedule):
                day_config = self.day_configs[day_idx]

                # Test minimum attractions per day
                self.assertGreaterEqual(len(day_schedule), 2,
                                        "Day has too few attractions")

                # Test maximum attractions per day
                self.assertLessEqual(len(day_schedule), 6,
                                     "Day has too many attractions")

                # Test time ordering
                for i in range(1, len(day_schedule)):
                    self.assertLess(
                        day_schedule[i - 1].time_range.end_time,
                        day_schedule[i].time_range.start_time,
                        "Time overlap in schedule"
                    )

                # Test for duplicates
                for attr_mod in day_schedule:
                    self.assertNotIn(attr_mod.attr.name, used_attractions,
                                     f"Duplicate attraction found: {attr_mod.attr.name}")
                    used_attractions.add(attr_mod.attr.name)

                # Test day time boundaries
                for attr_mod in day_schedule:
                    self.assertGreaterEqual(
                        attr_mod.time_range.start_time,
                        day_config.start_time,
                        "Attraction starts before day start time"
                    )
                    self.assertLessEqual(
                        attr_mod.time_range.end_time,
                        day_config.end_time,
                        "Attraction ends after day end time"
                    )

    def test_attraction_business_hours(self):
        """Test that attractions are scheduled within their business hours"""
        schedules = self.generator.getInitIndi()

        for schedule in schedules:
            for day_schedule in schedule:
                for attr_mod in day_schedule:
                    # Convert times to time objects for comparison
                    visit_time = attr_mod.time_range.start_time.time()
                    end_visit_time = attr_mod.time_range.end_time.time()
                    open_time = attr_mod.attr.open_time.time()
                    close_time = attr_mod.attr.close_time.time()

                    self.assertGreaterEqual(visit_time, open_time,
                                            f"{attr_mod.attr.name} scheduled before opening time")
                    self.assertLessEqual(end_visit_time, close_time,
                                         f"{attr_mod.attr.name} scheduled after closing time")

    def test_restaurant_distribution(self):
        """Test that restaurants are reasonably distributed across days"""
        schedules = self.generator.getInitIndi()

        for schedule in schedules:
            for day_schedule in schedule:
                # Count restaurants in each day
                restaurant_count = sum(
                    1 for attr_mod in day_schedule
                    if "restaurant" in self.place_additional_info[attr_mod.attr.name]["category"]
                )

                # Test maximum restaurants per day
                self.assertLessEqual(restaurant_count, 2,
                                     "Too many restaurants scheduled in one day")

    def test_schedule_diversity(self):
        """Test that generated schedules are sufficiently diverse"""
        schedules = self.generator.getInitIndi()

        # Compare each schedule with every other schedule
        for i in range(len(schedules)):
            for j in range(i + 1, len(schedules)):
                # Count common attractions
                schedule1_attractions = set(
                    attr_mod.attr.name
                    for day in schedules[i]
                    for attr_mod in day
                )
                schedule2_attractions = set(
                    attr_mod.attr.name
                    for day in schedules[j]
                    for attr_mod in day
                )

                common_attractions = len(schedule1_attractions & schedule2_attractions)
                total_attractions = len(schedule1_attractions | schedule2_attractions)

                similarity = common_attractions / total_attractions if total_attractions > 0 else 0

                # Test that schedules are not too similar
                self.assertLess(similarity, 0.8,
                                "Generated schedules are too similar")


if __name__ == '__main__':
    unittest.main()