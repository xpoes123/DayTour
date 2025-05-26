import requests
import json
from django.conf import settings

API_KEY = settings.G_API_KEY

def printj(json_file):
    """Debugging tool"""
    print(json.dumps(json_file, indent=4))

def get_distance_matrix(locations):
    query_locations = '|'.join(f'place_id:{l}' for l in locations)

    r = requests.get(
        'https://maps.googleapis.com/maps/api/distancematrix/json',
        params={
            'origins': query_locations,
            'destinations': query_locations,
            'key': API_KEY
        }
    )
    n = len(locations)
    distance_matrix = [[0] * n for _ in range(n)]
    for i, row in enumerate(r.json().get('rows', [])):
        for j, e in enumerate(row.get('elements', [])):
            distance_matrix[i][j] = e.get('distance', {}).get('value', 0)
    return distance_matrix
