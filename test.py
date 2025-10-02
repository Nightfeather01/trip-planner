

a=[]

b = ['a', 'b', 'c']
c=['1', '2', '3']

a.append(b)
a.append(c)

print(a)

a.append(list(b))
print(a)

import random
from datetime import datetime, timedelta

# 定義景點的結構
class Attraction:
    def __init__(self, name, open_time, close_time, stay):
        self.name = name
        self.open_time = open_time
        self.close_time = close_time
        self.stay = stay

    def __repr__(self):
        return f"{self.name} (Stay: {self.stay}h)"

# 將字符串格式的時間轉換為datetime對象
def parse_time(time_str):
    return datetime.strptime(time_str, '%H:%M')

# 檢查景點是否在給定時間範圍內開放
def is_open(attraction, start_time, stay_time):
    stay_end_time = start_time + timedelta(hours=stay_time)
    return (attraction.open_time <= start_time.time() <= attraction.close_time) and \
           (stay_end_time.time() <= attraction.close_time)

# 隨機生成一個行程
def generate_single_itinerary(start_time_str, end_time_str, attractions):
    start_time = parse_time(start_time_str)
    end_time = parse_time(end_time_str)
    current_time = start_time
    itinerary = []
    stay_durations = []

    while current_time < end_time:
        remaining_time = (end_time - current_time).total_seconds() / 3600

        # 過濾可以參觀的景點
        available_attractions = [attr for attr in attractions if attr.stay <= remaining_time and is_open(attr, current_time, attr.stay)]

        if not available_attractions:
            break

        # 隨機選擇一個景點
        chosen_attraction = random.choice(available_attractions)
        itinerary.append(chosen_attraction)
        stay_durations.append(chosen_attraction.stay)
        current_time += timedelta(hours=chosen_attraction.stay)

    return itinerary, stay_durations

# 根據停留時間生成行程
def generate_multiple_itineraries(start_time_str, end_time_str, attractions, num_itineraries, stay_durations):
    itineraries = []
    for _ in range(num_itineraries):
        start_time = parse_time(start_time_str)
        end_time = parse_time(end_time_str)
        current_time = start_time
        itinerary = []

        for stay in stay_durations:
            remaining_time = (end_time - current_time).total_seconds() / 3600

            # 過濾可以參觀的景點
            available_attractions = [attr for attr in attractions if attr.stay == stay and is_open(attr, current_time, attr.stay)]

            if not available_attractions:
                break

            # 隨機選擇一個景點
            chosen_attraction = random.choice(available_attractions)
            itinerary.append(chosen_attraction)
            current_time += timedelta(hours=chosen_attraction.stay)

        itineraries.append(itinerary)

    return itineraries


# 定義景點列表
attractions = [
    Attraction('attractionA', parse_time('08:00').time(), parse_time('20:00').time(), 1.5),
    Attraction('attractionB', parse_time('10:00').time(), parse_time('18:00').time(), 2.0),
    Attraction('attractionC', parse_time('09:00').time(), parse_time('17:00').time(), 1.0),
    Attraction('attractionD', parse_time('13:00').time(), parse_time('22:00').time(), 1.0),
    Attraction('attractionE', parse_time('12:00').time(), parse_time('14:00').time(), 1.5),
    Attraction('attractionF', parse_time('07:00').time(), parse_time('23:00').time(), 0.5),
    Attraction('attractionG', parse_time('15:00').time(), parse_time('19:00').time(), 0.5),
    Attraction('attractionH', parse_time('14:00').time(), parse_time('20:00').time(), 1.5),
    Attraction('attractionI', parse_time('07:00').time(), parse_time('17:00').time(), 2.0),
    Attraction('attractionJ', parse_time('03:00').time(), parse_time('17:00').time(), 1.5),
    Attraction('attractionK', parse_time('09:00').time(), parse_time('17:00').time(), 1.0),
    Attraction('attractionL', parse_time('11:00').time(), parse_time('17:00').time(), 0.5),
    Attraction('attractionM', parse_time('15:00').time(), parse_time('20:00').time(), 1.5),
    Attraction('attractionN', parse_time('18:00').time(), parse_time('23:00').time(), 1.0),
    Attraction('attractionO', parse_time('20:00').time(), parse_time('23:00').time(), 2.0),
    Attraction('attractionP', parse_time('12:00').time(), parse_time('18:00').time(), 1.5),
    Attraction('attractionQ', parse_time('11:00').time(), parse_time('20:00').time(), 1.0),
    Attraction('attractionR', parse_time('09:00').time(), parse_time('17:00').time(), 0.5),
]

# 生成基準行程
base_itinerary, stay_durations = generate_single_itinerary('08:00', '20:00', attractions)
print("Base Itinerary:")
for attraction in base_itinerary:
    print(attraction)

# 生成多個行程，所有行程停留時長組成相同
num_itineraries = 5
itineraries = generate_multiple_itineraries('08:00', '20:00', attractions, num_itineraries, stay_durations)

print("\nGenerated Itineraries:")
for idx, itinerary in enumerate(itineraries, start=1):
    print(f"\nItinerary {idx}:")
    for attraction in itinerary:
        print(attraction)