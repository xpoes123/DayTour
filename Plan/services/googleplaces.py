import requests
from django.conf import settings
import random

API_KEY = settings.G_API_KEY

def getPlaces(textQuery='Wisconsin State Capitol', radius=4000):
    # Step 1: Convert textQuery into lat/long using a "Text Search" request
    url1 = 'https://places.googleapis.com/v1/places:searchText'
    headers1 = {
        'X-Goog-Api-Key': API_KEY,
        'X-Goog-FieldMask': 'places.displayName,places.id,places.location',
        'Content-Type': 'application/json'
    }
    response1 = requests.post(url1, headers=headers1, json={'textQuery': textQuery})
    
    try:
        place_info = response1.json()['places'][0]
        location = place_info['location']
        name = place_info['displayName']['text']
        place_id = place_info['id']
        latitude = location['latitude']
        longitude = location['longitude']
    except (KeyError, IndexError) as e:
        print("Error in searchText response:", e)
        return []

    # Step 2: Search nearby tourist attractions
    url2 = 'https://places.googleapis.com/v1/places:searchNearby'
    headers2 = {
        'X-Goog-Api-Key': API_KEY,
        'X-Goog-FieldMask': '*',  # Temporarily use full response for debugging
        'Content-Type': 'application/json'
    }
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
    response2 = requests.post(url2, headers=headers2, json=params)

    placeIDs = [[place_id, name]]

    try:
        for place in response2.json()['places']:
            placeIDs.append([place['id'], place['displayName']['text']])
    except KeyError:
        print("No 'places' in searchNearby response.")

    # Shuffle the list to introduce variation (excluding the starting point)
    fixed_start = placeIDs[0]
    rest = placeIDs[1:]

    # Optional: Only keep up to max_locations total
    max_locations = 11
    if len(rest) > max_locations - 1:
        rest = random.sample(rest, max_locations - 1)

    return [fixed_start] + rest


def get_place_photo(place_id, maxwidth=400):
    """
    Given a place_id, return the photo URL from Google Places Details API.
    """
    details_url = f"https://maps.googleapis.com/maps/api/place/details/json"
    params = {
        "place_id": place_id,
        "fields": "photo",
        "key": API_KEY
    }

    response = requests.get(details_url, params=params)
    result = response.json().get("result", {})
    photos = result.get("photos", [])

    if not photos:
        return None  # or a fallback image

    photo_reference = photos[0]['photo_reference']
    return (
        f"https://maps.googleapis.com/maps/api/place/photo?"
        f"maxwidth={maxwidth}&photo_reference={photo_reference}&key={API_KEY}"
    )