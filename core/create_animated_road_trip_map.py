import json
from core.generate_initial_trip import AttractionModify, TimeRange, Attraction


def create_animated_road_trip_map(optimized_routes, output_file_path):
    """
        This function takes a list of optimized road trips and generates
        an animated map of them using the Google Maps API.
    """

    # This line makes the road trips round trips
    optimized_routes = [list(route) + [route[0]] for route in optimized_routes]
    print('optimized routes ')
    print(optimized_routes)

    # TODO: add time range in json

    output = []
    for attr in optimized_routes[-1]:
        output.append(attr.attr.name)

    # print('\n route in create_animated road trip map.py')
    # for route in optimized_routes:
    #     for attr in route:
    #         print(f'name: {attr.attr.name} {attr.time_range.start_time} {attr.time_range.end_time}')
    #     print()
    #     print()

    with open(output_file_path, 'w', encoding='utf-8') as out:
        json.dump(output, out, indent=4)


'''
    Page_1 = """
    <!DOCTYPE html>
    <html lang="en">
      <head>
        <meta charset="utf-8">
        <meta name="viewport" content="initial-scale=1.0, user-scalable=no">
        <meta name="description" content="Randy Olson uses machine learning to find the optimal road trip across the U.S.">
        <meta name="author" content="Randal S. Olson">

        <title>An optimized road trip across the U.S. according to machine learning</title>
        <style>
          html, body, #map-canvas {
              height: 100%;
              margin: 0px;
              padding: 0px
          }
          #panel {
              position: absolute;
              top: 5px;
              left: 50%;
              margin-left: -180px;
              z-index: 5;
              background-color: #fff;
              padding: 10px;
              border: 1px solid #999;
          }
        </style>
        <script src="https://maps.googleapis.com/maps/api/js?v=3"></script>
        <script>
            var routesList = [];
            var markerOptions = {icon: "http://maps.gstatic.com/mapfiles/markers2/marker.png"};
            var directionsDisplayOptions = {preserveViewport: true,
                                            markerOptions: markerOptions};
            var directionsService = new google.maps.DirectionsService();
            var map;
            var mapNum = 0;
            var numRoutesRendered = 0;
            var numRoutes = 0;

            function initialize() {
                var center = new google.maps.LatLng(39, -96);
                var mapOptions = {
                    zoom: 5,
                    center: center
                };
                map = new google.maps.Map(document.getElementById("map-canvas"), mapOptions);
                for (var i = 0; i < routesList.length; i++) {
                    routesList[i].setMap(map);
                }
            }
            function calcRoute(start, end, routes) {
                var directionsDisplay = new google.maps.DirectionsRenderer(directionsDisplayOptions);
                var waypts = [];
                for (var i = 0; i < routes.length; i++) {
                    waypts.push({
                        location:routes[i],
                        stopover:true});
                    }

                var request = {
                    origin: start,
                    destination: end,
                    waypoints: waypts,
                    optimizeWaypoints: false,
                    travelMode: google.maps.TravelMode.DRIVING
                };
                directionsService.route(request, function(response, status) {
                    if (status == google.maps.DirectionsStatus.OK) {
                        directionsDisplay.setDirections(response);
                        directionsDisplay.setMap(map);
                        numRoutesRendered += 1;

                        if (numRoutesRendered == numRoutes) {
                            mapNum += 1;
                            if (mapNum < 47) {
                                setTimeout(function() {
                                    return createRoutes(allRoutes[mapNum]);
                                }, 5000);
                            }
                        }
                    }
                });

                routesList.push(directionsDisplay);
            }
            function createRoutes(route) {
                // Clear the existing routes (if any)
                for (var i = 0; i < routesList.length; i++) {
                    routesList[i].setMap(null);
                }
                routesList = [];
                numRoutes = Math.floor((route.length - 1) / 9 + 1);
                numRoutesRendered = 0;

                // Google's free map API is limited to 10 waypoints so need to break into batches
                var subset = 0;
                while (subset < route.length) {
                    var waypointSubset = route.slice(subset, subset + 10);
                    var startPoint = waypointSubset[0];
                    var midPoints = waypointSubset.slice(1, waypointSubset.length - 1);
                    var endPoint = waypointSubset[waypointSubset.length - 1];
                    calcRoute(startPoint, endPoint, midPoints);
                    subset += 9;
                }
            }

            allRoutes = [];
            """
    Page_2 = """
            createRoutes(allRoutes[mapNum]);
            google.maps.event.addDomListener(window, "load", initialize);
        </script>
      </head>
      <body>
        <div id="map-canvas"></div>
      </body>
    </html>
    """

    with open('us-state-capitols-animated-map.html', 'w') as output_file:
        output_file.write(Page_1)
        for route in optimized_routes:
            output_file.write('allRoutes.push({});'.format(str(route)))
        output_file.write(Page_2)
'''
