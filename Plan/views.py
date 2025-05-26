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
from django.contrib.auth.decorators import login_required


import json

def locations_list(request):
    search_query = request.GET.get('search', '')
    
    # Filter locations by search query and order by num_visits in descending order
    if search_query:
        locations = Location.objects.filter(name__icontains=search_query).order_by('-num_visits')
    else:
        locations = Location.objects.all().order_by('-num_visits')
    
    paginator = Paginator(locations, 10)  # Paginate with 10 locations per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'plan/locations_list.html', {
        'page_obj': page_obj,
        'search_query': search_query,
    })


def plan(request):
    form = PlanForm()
    if request.method == "POST":
        form = PlanForm(request.POST)
        if form.is_valid():
            start_loc = form.cleaned_data['start_loc']
            radius = float(form.cleaned_data['radius'])
            locations = int(form.cleaned_data['locations'])

            name_lookup = {}

            seen = set()
            unique_routes = []

            for _ in range(10):
                place_array = getPlaces(start_loc, radius)
                selected_places = place_array[:locations]
                id_array = [place[0] for place in selected_places]

                for place_id, name in selected_places:
                    name_lookup[place_id] = name  # ensure no missing keys

                create_itinerary(request.user, selected_places)
                route = get_best_path(id_array)
                route_tuple = tuple(route)
                if route_tuple not in seen:
                    seen.add(route_tuple)
                    unique_routes.append(route)
                if len(unique_routes) == 5:
                    break

            request.session['routes'] = unique_routes
            request.session['name_lookup'] = name_lookup

            return redirect('plan:itinerary_page', page_num=1)
        else:
            messages.error(request, "Invalid form submission.")

    return render(request, 'plan/start.html', {'form': form})


def create_itinerary(user, place_array):
    location_names = []
    for place_id, place_name in place_array:
        location, created = Location.objects.get_or_create(
            google_id=place_id,
            defaults={'name': place_name}
        )
        location.num_visits += 1
        location.save()
        location_names.append(place_name)

    return Itinerary.objects.create(user=user, locations=location_names)


@login_required
def itinerary_page(request, page_num):
    all_routes = request.session.get('routes', [])
    name_lookup = request.session.get('name_lookup', {})

    try:
        page_number = int(page_num)
        route = all_routes[page_number - 1]
    except (ValueError, IndexError):
        return redirect('plan:itinerary_page', 1)

    travel_plan = []
    partial_routes = []
    for i in range(len(route) - 1):
        from_id = route[i]
        to_id = route[i + 1]
        travel_plan.append([name_lookup[from_id], name_lookup[to_id], 0, 0, 0])
        partial_routes.append(path_to_url([from_id, to_id]))
    path_map = path_to_url(route)

    total_pages = list(range(1, len(all_routes) + 1))

    return render(request, 'plan/itinerary.html', {
        'travel_plan': travel_plan,
        'partial_routes': json.dumps(partial_routes),
        'path_map': path_map,
        'current_page': page_number,
        'total_pages': total_pages,
    })
