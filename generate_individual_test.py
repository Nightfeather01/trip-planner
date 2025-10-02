from datetime import datetime, timedelta
from core.generate_initial_trip import InitIndividual, Attraction


def generateByDfs():
    attractions = [
        Attraction("景點A", datetime.strptime("09:00", "%H:%M"),
                   datetime.strptime("17:00", "%H:%M"), 1.5),
        Attraction("景點B", datetime.strptime("10:00", "%H:%M"),
                   datetime.strptime("18:00", "%H:%M"), 1.0),
        Attraction("景點C", datetime.strptime("08:00", "%H:%M"),
                   datetime.strptime("16:00", "%H:%M"), 2.5),
        Attraction("景點D", datetime.strptime("07:30", "%H:%M"),
                   datetime.strptime("12:00", "%H:%M"), 1.5),
        Attraction("景點J", datetime.strptime("09:30", "%H:%M"),
                   datetime.strptime("12:00", "%H:%M"), 1.5),
        Attraction("景點K", datetime.strptime("10:30", "%H:%M"),
                   datetime.strptime("13:00", "%H:%M"), 3.5),
        Attraction("景點L", datetime.strptime("11:30", "%H:%M"),
                   datetime.strptime("14:00", "%H:%M"), 1.5),
        Attraction("景點M", datetime.strptime("12:30", "%H:%M"),
                   datetime.strptime("14:00", "%H:%M"), 1.5),
        Attraction("景點N", datetime.strptime("12:00", "%H:%M"),
                   datetime.strptime("22:00", "%H:%M"), 2.0),
        Attraction("景點E", datetime.strptime("13:00", "%H:%M"),
                   datetime.strptime("17:00", "%H:%M"), 1.5),
        Attraction("景點F", datetime.strptime("15:00", "%H:%M"),
                   datetime.strptime("21:00", "%H:%M"), 1.5),
        Attraction("景點G", datetime.strptime("18:00", "%H:%M"),
                   datetime.strptime("21:00", "%H:%M"), 1.5),
        Attraction("景點H", datetime.strptime("18:30", "%H:%M"),
                   datetime.strptime("22:00", "%H:%M"), 1.5),
        Attraction("景點I", datetime.strptime("08:30", "%H:%M"),
                   datetime.strptime("16:00", "%H:%M"), 1.5),
    ]

    startTime = datetime.strptime("08:00", "%H:%M")
    endTime = datetime.strptime("22:00", "%H:%M")
    print(startTime)
    print(endTime)

    generate = InitIndividual(attractions, startTime, endTime, 3)
    return generate.getInitIndi()


attractions = [
    Attraction("景點A", datetime.strptime("09:00", "%H:%M"),
               datetime.strptime("17:00", "%H:%M"), 1.5),
    Attraction("景點B", datetime.strptime("10:00", "%H:%M"),
               datetime.strptime("18:00", "%H:%M"), 1.0),
    Attraction("景點C", datetime.strptime("08:00", "%H:%M"),
               datetime.strptime("16:00", "%H:%M"), 2.5),
    Attraction("景點D", datetime.strptime("07:30", "%H:%M"),
               datetime.strptime("12:00", "%H:%M"), 1.5),
    Attraction("景點J", datetime.strptime("09:30", "%H:%M"),
               datetime.strptime("12:00", "%H:%M"), 1.5),
    Attraction("景點K", datetime.strptime("10:30", "%H:%M"),
               datetime.strptime("13:00", "%H:%M"), 3.5),
    Attraction("景點L", datetime.strptime("11:30", "%H:%M"),
               datetime.strptime("14:00", "%H:%M"), 1.5),
    Attraction("景點M", datetime.strptime("12:30", "%H:%M"),
               datetime.strptime("14:00", "%H:%M"), 1.5),
    Attraction("景點N", datetime.strptime("12:00", "%H:%M"),
               datetime.strptime("22:00", "%H:%M"), 2.0),
    Attraction("景點E", datetime.strptime("13:00", "%H:%M"),
               datetime.strptime("17:00", "%H:%M"), 1.5),
    Attraction("景點F", datetime.strptime("15:00", "%H:%M"),
               datetime.strptime("21:00", "%H:%M"), 1.5),
    Attraction("景點G", datetime.strptime("18:00", "%H:%M"),
               datetime.strptime("21:00", "%H:%M"), 1.5),
    Attraction("景點H", datetime.strptime("18:30", "%H:%M"),
               datetime.strptime("22:00", "%H:%M"), 1.5),
    Attraction("景點I", datetime.strptime("08:30", "%H:%M"),
               datetime.strptime("16:00", "%H:%M"), 1.5),
]

startTime = datetime.strptime("08:00", "%H:%M")
endTime = datetime.strptime("22:00", "%H:%M")
print(startTime)
print(endTime)

generate = InitIndividual(attractions, startTime, endTime, 3)
generate.getInitIndi()

print('\n attractions after sorting')
for i in generate.attractions:
    print(i.name, i.open_time, i.close_time)
allSchedules = generate.allSchedules

print('result')
# print(allSchedules)
print(f'result size: {len(allSchedules)}')
print('---------')

for schedule in allSchedules:
    for attr in schedule:
        print(
            f'{attr.attr.name} start time: {attr.time_range.start_time} end time: {attr.time_range.end_time}, stay time: {attr.attr.stay_time}'
        )
    print('---------')
