import requests

def getPlaces(textQuery = 'Wisconsin State Capitol', radius = 4000):
    # Convert textQuery into lat/long using a "Text Search" request
    url1 = 'https://places.googleapis.com/v1/places:searchText'
    headers1 = {'X-Goog-Api-Key': 'AIzaSyDg6UAuCN_289HRIZ1Y3QGLTrTp2T7qu9g',
                'X-Goog-FieldMask': 'places.displayName,places.id,places.location'}
    r1 = requests.post(url1, headers=headers1, data={'textQuery': textQuery}).json()['places'][0]
    location = r1['location']
    name = r1['displayName']['text']
    id = r1['id']
    latitude = location['latitude']
    longitude = location['longitude']

    # Find a maximum of 20 tourist-attractions near the lat/long, return array of placeIDs
    url = 'https://places.googleapis.com/v1/places:searchNearby'
    headers = {'X-Goog-Api-Key': 'AIzaSyDg6UAuCN_289HRIZ1Y3QGLTrTp2T7qu9g',
            'X-Goog-FieldMask': 'places.id,places.displayName'}
    params = {
        'locationRestriction': {
            'circle': {
                'center': {
                    'latitude': latitude,
                    'longitude': longitude
                },
                'radius': radius
            }
        },
        'includedTypes': ['tourist_attraction']
    }
    r = requests.post(url, headers=headers, json=params)
    placeIDs = [[id, name]]
    for place in r.json()['places']:
        placeIDs.append([place['id'],place['displayName']['text']])
    return placeIDs
