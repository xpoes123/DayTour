import random
import matplotlib.pyplot as plt
import math
from .distance_matrix import get_distance_matrix
#from googleplaces import getPlaces

def generate_distance_matrix(points):
    n = len(points)
    distance_matrix = [[0] * n for _ in range(n)]

    for i in range(n):
        for j in range(i + 1, n):
            lat_diff = points[i].lat - points[j].lat
            long_diff = points[i].long - points[j].long
            euclidean_dist = math.sqrt(lat_diff ** 2 + long_diff ** 2)


            distance_matrix[i][j] = distance_matrix[j][i] = euclidean_dist

    return distance_matrix


class Point:
    def __init__(self, lat=0.0, long=0.0):
        self.lat = lat
        self.long = long

def path_length(path, distance_matrix):
    n = len(path)
    length = distance_matrix[path[-1]][path[0]]  # distance from last to first point (to close the loop)
    for i in range(n - 1):
        length += distance_matrix[path[i]][path[i + 1]]
    return length

def swap_edges(path, i, j):
    path[i + 1:j + 1] = reversed(path[i + 1:j + 1])

def create_random_path(n):
    # generate points with random latitudes and longitudes
    path = []
    for _ in range(n):
        lat = random.uniform(-90, 90)   # random latitude between -90 and 90 degrees
        long = random.uniform(-180, 180)  # random longitude between -180 and 180 degrees
        path.append(Point(lat, long))
    return path

def two_opt(path, distance_matrix):
    n = len(path)
    path_indices = list(range(n))
    cur_length = path_length(path_indices, distance_matrix)
    found_improvement = True
    count = 0

    while found_improvement and count < 1000:
        found_improvement = False
        for i in range(n - 1):
            for j in range(i + 2, n):
                length_delta = (
                    -distance_matrix[path_indices[i]][path_indices[i + 1]]
                    - distance_matrix[path_indices[j]][path_indices[(j + 1) % n]]
                    + distance_matrix[path_indices[i]][path_indices[j]]
                    + distance_matrix[path_indices[i + 1]][path_indices[(j + 1) % n]]
                )
                
                if length_delta < 0:
                    swap_edges(path_indices, i, j)
                    cur_length += length_delta
                    found_improvement = True
        
        count += 1
    return path_indices

# visualization functions
def plot_path(points, path_indices, title):
    lat_vals = [points[i].lat for i in path_indices] + [points[path_indices[0]].lat]  # Latitude values
    long_vals = [points[i].long for i in path_indices] + [points[path_indices[0]].long]  # Longitude values
    plt.plot(long_vals, lat_vals, marker='o', markersize=5)
    plt.title(title)
    plt.xlabel("Longitude")
    plt.ylabel("Latitude")
    plt.show()

# locations = place IDs
# returns the best path going to all the given locations
def get_best_path(locations):
    # get the distance matrix for the given locations
    dist_matrix = get_distance_matrix(locations)

    # # temporarily generate the distance matrix otherwise to avoid API calls
    # n = 20
    # points = create_random_path(n)
    # dist_matrix = generate_distance_matrix(points)

    # generate a random starting path from the list of locations
    initial_path_indices = random.sample(list(range(len(locations))), len(locations))
    # initial_path_indices = random.sample(list(range(len(points))), len(points))

    # print(initial_path_indices)

    # run 2-opt algorithm to optimize the path
    optimized_path_indices = two_opt(initial_path_indices, dist_matrix)

    # print(optimized_path_indices)
    # create a new list of place IDs, ending with the start node to create a full loop
    optimized_locations = [locations[index] for index in optimized_path_indices]
    optimized_locations.append(locations[0])

    return tuple(optimized_locations)

# Main code
# n = 20  # Increase the number of points for a larger matrix
# points = create_random_path(n)  # Generate random points with latitudes and longitudes
# points = [Point(43.069882,-89.412842), Point(43.072923,-89.380627), Point(43.077756,-89.391686), Point(43.069608,-89.423888), Point(43.076629,-89.404037),
#           Point(43.082543,-89.450942), Point(43.071132,-89.418270), Point(43.047929,-89.406417), Point(43.086605,-89.325197), Point(43.050563,-89.373156)]

# Generate distance matrix
# dist_matrix = generate_distance_matrix(points)
# places = distance_matrix.get_places()
# print(places)

# dist_matrix = distance_matrix.get_distance_matrix(distance_matrix.get_places()[:10])
# dist_matrix = [[for j in range(n)] for i in range(n)]

# print("distance matrix")
# print(len(dist_matrix))
# print(len(dist_matrix[0]))
# print(dist_matrix)

# get_best_path([])

# # Plot the initial random path
# initial_path_indices = list(range(len(dist_matrix)))  # Initial order of indices
# plot_path(points, initial_path_indices, "Initial Path")

# # Run 2-opt algorithm to optimize the path
# optimized_path_indices = two_opt(initial_path_indices, dist_matrix)

# # Plot the optimized path
# plot_path(points, optimized_path_indices, "Optimized Path with 2-opt")

# print(optimized_path_indices)

# places = getPlaces()[:-1]

# print(places)
# print(len(places))

# matrix = distance_matrix.get_distance_matrix(places)

# print(matrix)

# optimal_locations = get_best_path(places)

# print(optimal_locations)
# print(len(optimal_locations))





