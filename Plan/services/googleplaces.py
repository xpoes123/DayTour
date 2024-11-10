import requests

def getPlaces(placeID = 'ChIJ1xuVd4qAhYARvGgpdR2uXSc', radius = 4000):
    if placeID == 'ChIJ1xuVd4qAhYARvGgpdR2uXSc':
        # Here for testing purposes; saves api calls
        return ['ChIJ1xuVd4qAhYARvGgpdR2uXSc', 'ChIJQ-U7wYqAhYAReKjwcBt6SGU', 'ChIJE-5gllSBhYARsYVQC_gftuI', 'ChIJl3ZcoouAhYAR1DI821H-LUw', 'ChIJlRvon4yAhYARMw91ij6m610', 'ChIJB0Z9x4uAhYAR2rmxctOAnNA', 'ChIJ1855cG2BhYARSDtIa8RAsQs', 'ChIJ4W9VVouAhYARm7UjFtckzSE', 'ChIJmWz0tuKBhYARmCL4IYfCf0Q', 'ChIJYXDDl4qAhYAReRkaZFbsSzo', 'ChIJY8jq4G2BhYARSkNa7_mZ5eE']

    # Convert placeID into lat/long using a "Place Details" request
    url1 = 'https://places.googleapis.com/v1/places/'+placeID
    headers1 = {'X-Goog-Api-Key': 'AIzaSyDg6UAuCN_289HRIZ1Y3QGLTrTp2T7qu9g',
                'X-Goog-FieldMask': 'location'}
    r1 = requests.get(url1, headers=headers1)
    location = r1.json()['location']
    latitude = location['latitude']
    longitude = location['longitude']

    # Find a maximum of 20 tourist-attractions near the lat/long, return array of placeIDs
    url = 'https://places.googleapis.com/v1/places:searchNearby'
    headers = {'X-Goog-Api-Key': 'AIzaSyDg6UAuCN_289HRIZ1Y3QGLTrTp2T7qu9g',
            'X-Goog-FieldMask': 'places.id'}
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
    placeIDs = [placeID]
    for place in r.json()['places']:
        placeIDs.append(place['id'])
    return placeIDs
