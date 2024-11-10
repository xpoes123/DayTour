from urllib import parse

def path_to_url(placeIDs):
    output = 'https://www.google.com/maps/embed/v1/directions'
    output += '?'+parse.urlencode({'key': 'AIzaSyDg6UAuCN_289HRIZ1Y3QGLTrTp2T7qu9g', 'origin': 'place_id:'+placeIDs[0], 'destination': 'place_id:'+placeIDs[-1], 'mode': 'walking'})
    if len(placeIDs) > 2:
        output += '&waypoints='
        for i in range(1,len(placeIDs)-1):
            output += parse.quote_plus('place_id:'+placeIDs[i])
            if i < len(placeIDs)-2:
                output += '%7C'
    return output

# test case
# print(path_to_url(['ChIJQ-U7wYqAhYAReKjwcBt6SGU', 'ChIJE-5gllSBhYARsYVQC_gftuI', 'ChIJl3ZcoouAhYAR1DI821H-LUw', 'ChIJlRvon4yAhYARMw91ij6m610', 'ChIJB0Z9x4uAhYAR2rmxctOAnNA', 'ChIJ1855cG2BhYARSDtIa8RAsQs', 'ChIJ4W9VVouAhYARm7UjFtckzSE', 'ChIJmWz0tuKBhYARmCL4IYfCf0Q', 'ChIJYXDDl4qAhYAReRkaZFbsSzo', 'ChIJY8jq4G2BhYARSkNa7_mZ5eE']))