from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from .forms import PlanForm
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, get_user_model
from .static.plan.js.place_list_to_map_url import path_to_url
from .services.googleplaces import getPlaces, get_place_photo
from .services.two_opt import get_best_path
from .models import Location, Itinerary
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
import random
import json

def locations_list(request):
    search_query = request.GET.get('search', '')
    if search_query:
        locations = Location.objects.filter(name__icontains=search_query).order_by('-num_visits')
    else:
        locations = Location.objects.all().order_by('-num_visits')

    paginator = Paginator(locations, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'plan/locations_list.html', {
        'page_obj': page_obj,
        'search_query': search_query,
    })

def plan(request):
    form = PlanForm()
    if request.method == "POST":
        action = request.POST.get('action')
        form = PlanForm(request.POST)
        if form.is_valid():
            start_loc = form.cleaned_data['start_loc']
            radius = float(form.cleaned_data['radius'])
            locations = int(form.cleaned_data['locations'])

            if action == 'plan':
                name_lookup = {}
                seen = set()
                unique_routes = []

                for _ in range(10):
                    place_array = getPlaces(start_loc, radius)
                    selected_places = place_array[:locations]
                    id_array = [place[0] for place in selected_places]

                    for place_id, name in selected_places:
                        name_lookup[place_id] = name

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

            elif action == "pick":
                places = getPlaces(start_loc, radius)
                start = places[0]
                places = places[1:]
                places_with_images = [
                    {
                        "id": place[0],
                        "name": place[1],
                        "image_url": get_place_photo(place[0]) or "/static/images/daytour.png"
                    }
                    for place in places
                ]
                print(start_loc, start)
                return render(request, 'plan/pick.html', {
                    'places': places_with_images,
                    'start_loc': start_loc,
                    'start_loc_google': start,
                    'radius': radius,
                    'original_count': locations
                })
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

@csrf_exempt
def confirm_pick(request):
    if request.method == "POST":
        start_loc = request.POST.get('start_loc')
        radius = float(request.POST.get('radius'))
        selected_ids = request.POST.getlist('selected_places')
        original_count = int(request.POST.get('original_count', len(selected_ids)))

        all_places = getPlaces(start_loc, radius)
        name_lookup = {place[0]: place[1] for place in all_places}

        selected_set = set(selected_ids)
        selected_places = [(pid, name_lookup[pid]) for pid in selected_ids if pid in name_lookup]

        # Fill in with more unique places if not enough were selected
        if len(selected_places) < original_count:
            for pid, name in all_places:
                if pid not in selected_set:
                    selected_places.append((pid, name))
                    selected_set.add(pid)
                if len(selected_places) >= original_count:
                    break
        cap = max(0, original_count - 1)
        if len(selected_places) > cap:
            random.shuffle(selected_places)
            selected_places = selected_places[:cap]

        # Then prepend the start location
        start_loc_google = request.POST.get('start_loc_google', 'start')
        selected_places.insert(0, tuple(start_loc_google))
        # The issue is that this is a string of a list instead of alist, we need to convert it back
        print(start_loc_google[0], start_loc_google[1])
        # for i in selected_places:
        #     print(i)
        id_array = [pid for pid, _ in selected_places]
        route = get_best_path(id_array)
        name_lookup = {pid: name for pid, name in selected_places}

        travel_plan = []
        partial_routes = []
        for i in range(len(route) - 1):
            from_id = route[i]
            to_id = route[i + 1]
            travel_plan.append([name_lookup[from_id], name_lookup[to_id], 0, 0, 0])
            partial_routes.append(path_to_url([from_id, to_id]))
        path_map = path_to_url(route)

        return render(request, 'plan/itinerary.html', {
            'travel_plan': travel_plan,
            'partial_routes': json.dumps(partial_routes),
            'path_map': path_map,
            'current_page': 1,
            'total_pages': [1]
        })

    return redirect('plan:plan')