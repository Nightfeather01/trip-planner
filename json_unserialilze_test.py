import json

with open('fetchGoogleAPI/allPlacesData.json', 'r') as file:
    data = json.load(file)

    for place in data:
        name = place['name']
        print(name)
        if 'opening_hours' in place and 'close' in place['opening_hours'][
                'periods'][0]:
            open_time: str = str(
                place['opening_hours']['periods'][0]['open']['time'])
            close_time: str = str(
                place['opening_hours']['periods'][0]['close']['time'])
            open_time = open_time[0:2] + ":" + open_time[2:4]
            close_time = close_time[0:2] + ":" + close_time[2:4]
        else:
            open_time = None
        print(open_time)

time = '1234'
time = time[0:2] + ":" + time[2:4]
print(time)
