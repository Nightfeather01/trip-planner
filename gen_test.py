
from datetime import datetime, timedelta
from typing_extensions import Annotated

class Attraction:
    def __init__(self, name, open_time, close_time, stay_time):
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

Hours = Annotated[float, "hours"]

class InitIndividual:
    def __init__(self, attractions: list[Attraction], start_time, end_time) -> None:
        self.attractions = attractions
        self.start_time = start_time
        self.trip_end_time = end_time

        self.visited = []
        self.allSchedules: list[list[AttractionModify]] = []

    def sortAttractions(self):
        self.attractions = sorted(self.attractions,
            key=lambda x: (x.open_time, x.close_time))

    def is_valid_schedule(self, currentTime, attraction: Attraction):
        end_time = self.next_time(currentTime, attraction.stay_time)
        if currentTime >= attraction.open_time and end_time <= attraction.close_time:
            return True
        return False

    def isValid(self, start_idx, currentTime):
        for i in range(start_idx, len(self.attractions)):
            if self.is_valid_schedule(currentTime, self.attractions[i]):
                return True
        return False

    @staticmethod
    def next_time(current_time: datetime, stay_time: Hours):
        return current_time + timedelta(hours=stay_time)

    def getInitIndi(self):
        self.sortAttractions()
        self.dfs(0, self.start_time, [])

        return self.allSchedules

    def dfs(self, start_idx, currentTime, currentSchedule: list[AttractionModify]):
        if currentTime > self.trip_end_time or (self.isValid(start_idx, currentTime) == False):
            if len(currentSchedule) >= 1:
                self.allSchedules.append(list(currentSchedule))
            return True

        for i in range(start_idx, len(self.attractions)):
            if self.is_valid_schedule(currentTime, self.attractions[i]):
                end_time = self.next_time(currentTime, self.attractions[i].stay_time)
                current_attraction_modify = AttractionModify(
                    attr=self.attractions[i], time_range=TimeRange(currentTime, end_time))
                currentSchedule.append(current_attraction_modify)

                self.dfs(i + 1, end_time, currentSchedule)
                currentSchedule.pop()


attractions = [
    Attraction("景點A", datetime.strptime("09:00", "%H:%M"), datetime.strptime("17:00", "%H:%M"), 1.5),
    Attraction("景點B", datetime.strptime("10:00", "%H:%M"), datetime.strptime("18:00", "%H:%M"), 1.0),
    Attraction("景點C", datetime.strptime("08:00", "%H:%M"), datetime.strptime("16:00", "%H:%M"), 2.5),
    Attraction("景點D", datetime.strptime("07:30", "%H:%M"), datetime.strptime("12:00", "%H:%M"), 1.5),
    Attraction("景點J", datetime.strptime("09:30", "%H:%M"), datetime.strptime("12:00", "%H:%M"), 1.5),
    Attraction("景點K", datetime.strptime("10:30", "%H:%M"), datetime.strptime("13:00", "%H:%M"), 3.5),
    Attraction("景點L", datetime.strptime("11:30", "%H:%M"), datetime.strptime("14:00", "%H:%M"), 1.5),
    Attraction("景點M", datetime.strptime("12:30", "%H:%M"), datetime.strptime("14:00", "%H:%M"), 1.5),
    Attraction("景點N", datetime.strptime("12:00", "%H:%M"), datetime.strptime("22:00", "%H:%M"), 2.0),
    Attraction("景點E", datetime.strptime("13:00", "%H:%M"), datetime.strptime("17:00", "%H:%M"), 1.5),
    Attraction("景點F", datetime.strptime("15:00", "%H:%M"), datetime.strptime("21:00", "%H:%M"), 1.5),
    Attraction("景點G", datetime.strptime("18:00", "%H:%M"), datetime.strptime("21:00", "%H:%M"), 1.5),
    Attraction("景點H", datetime.strptime("18:30", "%H:%M"), datetime.strptime("22:00", "%H:%M"), 1.5),
    Attraction("景點I", datetime.strptime("08:30", "%H:%M"), datetime.strptime("16:00", "%H:%M"), 1.5),
]


# 三天的行程規劃
startTime = datetime.strptime("08:00", "%H:%M")
endTime = datetime.strptime("22:00", "%H:%M")
three_days_later = endTime + timedelta(days=2)

generate = InitIndividual(attractions, startTime, three_days_later)
generate.getInitIndi()

allSchedules = generate.allSchedules

print(f'result size: {len(allSchedules)}')
print('---------')

for schedule in allSchedules:
    for attr in schedule:
        print(f'{attr.attr.name} start time: {attr.time_range.start_time} end time: {attr.time_range.end_time}, stay time: {attr.attr.stay_time}')
    print('---------')