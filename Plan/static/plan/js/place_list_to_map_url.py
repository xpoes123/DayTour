from urllib import parse
from django.conf import settings

API_KEY = settings.G_API_KEY
def path_to_url(placeIDs):
    output = 'https://www.google.com/maps/embed/v1/directions'
    output += '?'+parse.urlencode({'key': API_KEY, 'origin': 'place_id:'+placeIDs[0], 'destination': 'place_id:'+placeIDs[-1], 'mode': 'walking'})
    if len(placeIDs) > 2:
        output += '&waypoints='
        for i in range(1,len(placeIDs)-1):
            output += parse.quote_plus('place_id:'+placeIDs[i])
            if i < len(placeIDs)-2:
                output += '%7C'
    return output