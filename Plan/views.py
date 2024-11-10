from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from .forms import PlanForm
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, get_user_model
from .static.plan.js.place_list_to_map_url import path_to_url
from .services.googleplaces import getPlaces
from .services.two_opt import get_best_path
import json



def plan(request):
    """
    Registration request to make a new account
    """
    form = PlanForm()
    if request.method == "POST":
        form = PlanForm(request.POST)
        if form.is_valid():
            start_loc = form.cleaned_data['start_loc']
            radius = float(form.cleaned_data['radius'])
            locations = int(form.cleaned_data['locations'])
            place_array = getPlaces(start_loc, radius)
            route = get_best_path(place_array[0:locations])
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
