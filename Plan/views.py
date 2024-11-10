from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from .forms import PlanForm
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, get_user_model
from .static.plan.js.place_list_to_map_url import path_to_url
from .services.googleplaces import getPlaces
from .services.two_opt import get_best_path
from .models import Location  # Import the Location model
import json

def plan(request):
    """
    Process a planning request to get travel locations and optimize the route.
    """
    form = PlanForm()
    if request.method == "POST":
        form = PlanForm(request.POST)
        if form.is_valid():
            start_loc = form.cleaned_data['start_loc']
            radius = float(form.cleaned_data['radius'])
            locations = int(form.cleaned_data['locations'])
            
            # Fetch places using the start location and radius
            place_array = getPlaces(start_loc, radius)
            
            # Create or get each location in the database with name set to "DEFAULT"
            locations_list = []
            for place in place_array[:locations]:  # Limit to specified number of locations
                # Extract google_id based on the data format returned by getPlaces
                google_id = place['id'] if isinstance(place, dict) else place

                # Use get_or_create to ensure location is in the database
                location, created = Location.objects.get_or_create(
                    google_id=google_id,
                    defaults={'name': "DEFAULT"}  # Setting name to "DEFAULT"
                )
                locations_list.append(location)

            # Calculate the optimal route using the verified/created locations
            route = get_best_path([loc.google_id for loc in locations_list])
            
            # Store the result in the session
            request.session['route'] = route
            return redirect('plan:itinerary')
        else:
            messages.error(request, "Invalid form submission.")
    return render(request, 'plan/start.html', {'form': form})

def itinerary(request):
    # Sample data for travel_plan
    # travel_plan = [
    #     ["Location A", "Location B", "15 mins", "8:00 AM", "1 hour"],
    #     ["Location B", "Location C", "10 mins", "9:15 AM", "30 mins"],
    #     ["Location C", "Location D", "20 mins", "10:00 AM", "1.5 hours"],
    # ]
    travel_plan = []
    partial_routes = []
    route = request.session.get('route', 'No route found')
    for i in range(len(route)-1):
        travel_plan.append([route[i],route[i+1],"0","0","0"])
        partial_routes.append(path_to_url([route[i],route[i+1]]))
    path_map = path_to_url(route)
    context = {
        "travel_plan": travel_plan,
        "path_map": path_map,
        "partial_routes": json.dumps(partial_routes)
    }
    return render(request, 'plan/itinerary.html', context)
