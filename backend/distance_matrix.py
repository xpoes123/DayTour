import requests
import json
from googleplaces import getPlaces

def printj(json_file):
    """Debugging tool"""
    print(json.dumps(json_file, indent=4))

API_KEY = 'AIzaSyDg6UAuCN_289HRIZ1Y3QGLTrTp2T7qu9g'
locations = ['ChIJgUbEo8cfqokR5lP9_Wh_DaM', 'GhIJQWDl0CIeQUARxks3icF8U8A']

def get_distance_matrix(locations):

    # return [[0, 419, 1138, 735, 563, 661, 932, 758, 999, 426], [472, 0, 1170, 553, 536, 479, 848, 732, 1031, 7], [719, 996, 0, 506, 698, 432, 1502, 894, 285, 1003], [889, 759, 1104, 0, 193, 896, 1265, 388, 1113, 766], [907, 777, 924, 988, 0, 936, 1283, 675, 933, 784], [446, 723, 1260, 74, 425, 0, 1229, 621, 555, 730], [572, 926, 1796, 1053, 1034, 979, 0, 1265, 1530, 933], [792, 662, 1490, 874, 856, 799, 1168, 0, 1352, 670], [715, 990, 987, 233, 692, 268, 1495, 888, 0, 997], [465, 480, 1163, 546, 529, 472, 841, 725, 1024, 0]]

    query_locations = ''

    for l in locations:
        query_locations += 'place_id:' + l + '|'


    r = requests.get(
        f'https://maps.googleapis.com/maps/api/distancematrix/json?origins={query_locations}&destinations={query_locations}&key={API_KEY}')

    distance_matrix = [[0] * len(locations) for _ in range(len(locations))] 
    print("r.json: ")
    print(r.json())
    i = 0
    for r in r.json()['rows']:
        j = 0
        for e in r['elements']: 
            distance_matrix[i][j] = e['distance']['value']
            j += 1
        i += 1

    return distance_matrix

# def get_places():
#     return get_distance_matrix(getPlaces()[:10])

# print(len(getPlaces()))