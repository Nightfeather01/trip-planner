import unittest
from datetime import datetime, timedelta
from generate_multiple_day_trip import DayConfig


class TestDayConfig(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures for all tests"""
        # Sample base dates and times for testing
        self.sample_date = datetime(2024, 3, 20)
        self.sample_start_time = datetime.combine(self.sample_date.date(),
                                                  datetime.strptime("09:00", "%H:%M").time())
        self.sample_end_time = datetime.combine(self.sample_date.date(),
                                                datetime.strptime("17:00", "%H:%M").time())

    def test_day_config_initialization(self):
        """Test basic DayConfig initialization"""
        day_config = DayConfig(
            date=self.sample_date,
            start_time=self.sample_start_time,
            end_time=self.sample_end_time
        )

        self.assertEqual(day_config.date, self.sample_date)
        self.assertEqual(day_config.start_time, self.sample_start_time)
        self.assertEqual(day_config.end_time, self.sample_end_time)

        # Test that end_time is after start_time
        self.assertGreater(day_config.end_time, day_config.start_time)

    def test_create_day_configs_normal_case(self):
        """Test create_day_configs with normal input"""
        departure_datetime = "2024-03-20T09:00"
        return_datetime = "2024-03-22T17:00"
        daily_depart_time = "09:00"
        daily_return_time = "17:00"

        configs = DayConfig.create_day_configs(
            departure_datetime=departure_datetime,
            return_datetime=return_datetime,
            daily_depart_time=daily_depart_time,
            daily_return_time=daily_return_time
        )

        # Should create 3 days of configs
        self.assertEqual(len(configs), 3)

        # Check first day
        self.assertEqual(configs[0].date.date(), datetime(2024, 3, 20).date())
        self.assertEqual(configs[0].start_time.time(),
                         datetime.strptime("09:00", "%H:%M").time())

        # Check last day
        self.assertEqual(configs[-1].date.date(), datetime(2024, 3, 22).date())
        self.assertEqual(configs[-1].end_time.time(),
                         datetime.strptime("17:00", "%H:%M").time())

    def test_create_day_configs_single_day(self):
        """Test create_day_configs for a single day trip"""
        departure_datetime = "2024-03-20T09:00"
        return_datetime = "2024-03-20T17:00"
        daily_depart_time = "09:00"
        daily_return_time = "17:00"

        configs = DayConfig.create_day_configs(
            departure_datetime=departure_datetime,
            return_datetime=return_datetime,
            daily_depart_time=daily_depart_time,
            daily_return_time=daily_return_time
        )

        self.assertEqual(len(configs), 1)
        self.assertEqual(configs[0].date.date(), datetime(2024, 3, 20).date())
        self.assertEqual(configs[0].start_time.hour, 9)
        self.assertEqual(configs[0].end_time.hour, 17)

    def test_create_day_configs_partial_days(self):
        """Test create_day_configs with partial first and last days"""
        departure_datetime = "2024-03-20T14:00"  # Late start
        return_datetime = "2024-03-22T12:00"  # Early end
        daily_depart_time = "09:00"
        daily_return_time = "17:00"

        configs = DayConfig.create_day_configs(
            departure_datetime=departure_datetime,
            return_datetime=return_datetime,
            daily_depart_time=daily_depart_time,
            daily_return_time=daily_return_time
        )

        # Check first day starts late
        self.assertEqual(configs[0].start_time.hour, 14)

        # Check middle day has full hours
        self.assertEqual(configs[1].start_time.hour, 9)
        self.assertEqual(configs[1].end_time.hour, 17)

        # Check last day ends early
        self.assertEqual(configs[-1].end_time.hour, 12)

    def test_create_day_configs_crossing_midnight(self):
        """Test create_day_configs with operating hours crossing midnight"""
        departure_datetime = "2024-03-20T09:00"
        return_datetime = "2024-03-22T17:00"
        daily_depart_time = "22:00"
        daily_return_time = "02:00"

        configs = DayConfig.create_day_configs(
            departure_datetime=departure_datetime,
            return_datetime=return_datetime,
            daily_depart_time=daily_depart_time,
            daily_return_time=daily_return_time
        )

        for config in configs:
            print(f"{config.start_time}, {config.end_time}")

        for config in configs:
            self.assertEqual(config.start_time.hour, 22)
            # The end time should be 2 AM of the next day
            next_day = config.start_time + timedelta(days=1)
            self.assertEqual(config.end_time.hour, 2)
            self.assertEqual(config.end_time.date(), next_day.date())

    def test_create_day_configs_validation(self):
        """Test input validation for create_day_configs"""
        # Test invalid date format
        with self.assertRaises(ValueError):
            DayConfig.create_day_configs(
                departure_datetime="invalid_date",
                return_datetime="2024-03-22T17:00",
                daily_depart_time="09:00",
                daily_return_time="17:00"
            )

        # Test return date before departure date
        with self.assertRaises(ValueError):
            DayConfig.create_day_configs(
                departure_datetime="2024-03-22T09:00",
                return_datetime="2024-03-20T17:00",
                daily_depart_time="09:00",
                daily_return_time="17:00"
            )

        # Test invalid time format
        with self.assertRaises(ValueError):
            DayConfig.create_day_configs(
                departure_datetime="2024-03-20T09:00",
                return_datetime="2024-03-22T17:00",
                daily_depart_time="invalid_time",
                daily_return_time="17:00"
            )

    def test_day_config_equality(self):
        """Test equality comparison of DayConfig objects"""
        config1 = DayConfig(
            date=self.sample_date,
            start_time=self.sample_start_time,
            end_time=self.sample_end_time
        )

        config2 = DayConfig(
            date=self.sample_date,
            start_time=self.sample_start_time,
            end_time=self.sample_end_time
        )

        config3 = DayConfig(
            date=self.sample_date + timedelta(days=1),
            start_time=self.sample_start_time,
            end_time=self.sample_end_time
        )

        self.assertEqual(config1, config2)
        self.assertNotEqual(config1, config3)

    def test_day_duration(self):
        """Test the duration of day configurations"""
        standard_day = DayConfig(
            date=self.sample_date,
            start_time=datetime.combine(self.sample_date.date(),
                                        datetime.strptime("09:00", "%H:%M").time()),
            end_time=datetime.combine(self.sample_date.date(),
                                      datetime.strptime("17:00", "%H:%M").time())
        )

        # Test 8-hour duration
        duration = standard_day.end_time - standard_day.start_time
        self.assertEqual(duration.total_seconds() / 3600, 8)

        # Test short day
        short_day = DayConfig(
            date=self.sample_date,
            start_time=datetime.combine(self.sample_date.date(),
                                        datetime.strptime("14:00", "%H:%M").time()),
            end_time=datetime.combine(self.sample_date.date(),
                                      datetime.strptime("17:00", "%H:%M").time())
        )

        # Test 3-hour duration
        duration = short_day.end_time - short_day.start_time
        self.assertEqual(duration.total_seconds() / 3600, 3)

    def test_create_day_configs_with_holidays(self):
        """Test create_day_configs with different hours for holidays"""
        # This is a placeholder test for potential future functionality
        # where holidays might have different operating hours
        departure_datetime = "2024-12-25T09:00"  # Christmas Day
        return_datetime = "2024-12-27T17:00"
        daily_depart_time = "09:00"
        daily_return_time = "17:00"

        configs = DayConfig.create_day_configs(
            departure_datetime=departure_datetime,
            return_datetime=return_datetime,
            daily_depart_time=daily_depart_time,
            daily_return_time=daily_return_time
        )

        # Currently, holidays are treated the same as regular days
        self.assertEqual(len(configs), 3)
        self.assertEqual(configs[0].start_time.hour, 9)
        self.assertEqual(configs[0].end_time.hour, 17)


if __name__ == '__main__':
    unittest.main()