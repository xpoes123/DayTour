from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from .forms import PlanForm
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, get_user_model
from .static.plan.js.place_list_to_map_url import path_to_url
from .services.googleplaces import getPlaces
from .services.two_opt import get_best_path
from .models import Location, Itinerary
from django.core.paginator import Paginator

import json

def locations_list(request):
    search_query = request.GET.get('search', '')
    locations = Location.objects.all()

    if search_query:
        locations = locations.filter(name__icontains=search_query)

    # Paginate the locations
    paginator = Paginator(locations, 10)  # Show 10 locations per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Pass the page object and search query to the template
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
    }
    return render(request, 'plan/locations_list.html', context)

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
            
            # Fetch places and limit to the specified number of locations
            place_array = getPlaces(start_loc, radius)
            
            # Extract IDs and names from the place_array
            id_array = []
            name_lookup = {}
            for place in place_array[:locations]:  # Limit to 'locations' items
                place_id, place_name = place[0], place[1]
                id_array.append(place_id)
                name_lookup[place_id] = place_name
            
            # Create an itinerary using id_array (Google IDs) and store names
            itinerary = create_itinerary(request.user, place_array[:locations])
            
            # Calculate the optimal route using the list of Google IDs in id_array
            route = get_best_path(id_array)
            
            # Store the route and name lookup in the session
            request.session['route'] = route
            request.session['name_lookup'] = name_lookup

            return redirect('plan:itinerary')
        else:
            messages.error(request, "Invalid form submission.")
    return render(request, 'plan/start.html', {'form': form})


def create_itinerary(user, place_array):
    """
    Create a new itinerary for the user, storing locations as a list of Google IDs and names.
    """
    # Prepare lists to store Google IDs and names
    location_ids = []
    location_names = []

    for place in place_array:
        place_id, place_name = place[0], place[1]

        # Check if the location already exists; if not, create it
        location, created = Location.objects.get_or_create(
            google_id=place_id,
            defaults={'name': place_name}
        )

        # Increment num_visits each time the location is accessed or created
        location.num_visits += 1
        location.save()

        # Log creation or access
        if created:
            print(f"Created new location: {place_name} with ID: {place_id}")
        else:
            print(f"Location already exists: {location.name} with ID: {place_id}")

        # Add the Google ID and name to the lists for the itinerary
        location_ids.append(place_id)
        location_names.append(place_name)

    # Create the itinerary, storing the list of Google IDs in the JSON field
    itinerary = Itinerary.objects.create(user=user, locations=location_names)
    return itinerary


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
    name_lookup = request.session.get('name_lookup', 'Name lookup not found')
    for i in range(len(route)-1):
        travel_plan.append([name_lookup[route[i]],name_lookup[route[i+1]],0,0,0])
        partial_routes.append(path_to_url([route[i],route[i+1]]))
    path_map = path_to_url(route)
    context = {
        "travel_plan": travel_plan,
        "path_map": path_map,
        "partial_routes": json.dumps(partial_routes)
    }
    return render(request, 'plan/itinerary.html', context)
