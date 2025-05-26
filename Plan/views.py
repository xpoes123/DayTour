from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from .forms import PlanForm
from .services.googleplaces import getPlaces, get_place_photo, path_to_url, get_restaurants, trim_address
from .services.two_opt import get_best_path
from .models import Location, Itinerary
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import random
import json
from math import ceil
import ast

def get_unique_restaurants(place_id, seen_ids, max_count=3):
    """Return up to `max_count` unique restaurants around a place."""
    raw = get_restaurants(place_id)
    unique = []
    for r in raw:
        rid = r["place_id"]
        if rid not in seen_ids:
            seen_ids.add(rid)

            rating = r.get("rating")
            rounded_rating = int(ceil(rating)) if rating is not None else 0

            unique.append({
                "name": r["name"],
                "address": trim_address(r.get("address", "")),
                "place_id": rid,
                "rating": rounded_rating,
                "price_level": r.get("price_level"),
                "image_url": get_place_photo(rid) or "/static/images/daytour.png"
            })
        if len(unique) == max_count:
            break
    return unique

def locations_list(request):
    search_query = request.GET.get('search', '')
    locations = Location.objects.filter(name__icontains=search_query).order_by('-num_visits') if search_query else Location.objects.all().order_by('-num_visits')
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
            transit_mode = form.cleaned_data.get('transit_mode')
            if action == 'plan':
                name_lookup = {}
                seen = set()
                unique_routes = []

                for _ in range(10):
                    place_array = getPlaces(start_loc, radius, transit_mode=transit_mode)
                    selected_places = place_array[:locations + 1]
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

                route = unique_routes[0]
                travel_plan = []
                partial_routes = []
                seen_restaurant_ids = set()

                for i in range(len(route) - 1):
                    from_id = route[i]
                    to_id = route[i + 1]
                    travel_plan.append({
                        'origin_name': name_lookup[from_id],
                        'destination_name': name_lookup[to_id],
                        'destination_id': to_id,
                        'restaurants': get_unique_restaurants(to_id, seen_restaurant_ids)
                    })
                    partial_routes.append(path_to_url([from_id, to_id], transit_mode))

                path_map = path_to_url(route, transit_mode)
                total_pages = list(range(1, len(unique_routes) + 1))

                request.session['routes'] = unique_routes
                request.session['name_lookup'] = name_lookup
                request.session['transit_mode'] = transit_mode

                return render(request, 'plan/itinerary.html', {
                    'travel_plan': travel_plan,
                    'partial_routes': json.dumps(partial_routes),
                    'path_map': path_map,
                    'current_page': 1,
                    'total_pages': total_pages,
                })

            elif action == "pick":
                request.session['transit_mode'] = transit_mode
                places = getPlaces(start_loc, radius, transit_mode=transit_mode)
                start = places[0]
                places = places[1:]
                places_with_images = [{
                    "id": place[0],
                    "name": place[1],
                    "image_url": get_place_photo(place[0]) or "/static/images/daytour.png"
                } for place in places]
                return render(request, 'plan/pick.html', {
                    'places': places_with_images,
                    'start_loc': start_loc,
                    'start_loc_google': start,
                    'radius': radius,
                    'original_count': locations,
                    'transit_mode': transit_mode
                })
    return render(request, 'plan/start.html', {'form': form})

def create_itinerary(user, place_array):
    location_names = []
    for place_id, place_name in place_array:
        location, _ = Location.objects.get_or_create(
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
    mode = request.session.get('transit_mode')
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
        travel_plan.append({
            'origin_name': name_lookup[from_id],
            'destination_name': name_lookup[to_id],
            'destination_id': to_id
        })
        partial_routes.append(path_to_url([from_id, to_id], mode))

    path_map = path_to_url(route, mode)
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
        transit_mode = request.POST.get('transit_mode', 'walking')

        all_places = getPlaces(start_loc, radius, transit_mode=transit_mode)
        name_lookup = {place[0]: place[1] for place in all_places}
        selected_set = set(selected_ids)

        selected_places = [(pid, name_lookup[pid]) for pid in selected_ids if pid in name_lookup]
        if len(selected_places) < original_count:
            for pid, name in all_places:
                if pid not in selected_set:
                    selected_places.append((pid, name))
                    selected_set.add(pid)
                if len(selected_places) > original_count:
                    break

        cap = max(0, original_count)
        if len(selected_places) > cap:
            random.shuffle(selected_places)
            selected_places = selected_places[:cap+1]

        start_loc_google = ast.literal_eval(request.POST.get('start_loc_google', 'start'))
        selected_places.insert(0, tuple(start_loc_google))

        id_array = [pid for pid, _ in selected_places]
        route = get_best_path(id_array)
        name_lookup = {pid: name for pid, name in selected_places}

        travel_plan = []
        partial_routes = []
        seen_restaurant_ids = set()

        for i in range(len(route) - 1):
            from_id = route[i]
            to_id = route[i + 1]
            travel_plan.append({
                'origin_name': name_lookup[from_id],
                'destination_name': name_lookup[to_id],
                'destination_id': to_id,
                'restaurants': get_unique_restaurants(to_id, seen_restaurant_ids)
            })
            partial_routes.append(path_to_url([from_id, to_id], transit_mode))

        path_map = path_to_url(route, transit_mode)
        request.session['transit_mode'] = transit_mode
        return render(request, 'plan/itinerary.html', {
            'travel_plan': travel_plan,
            'partial_routes': json.dumps(partial_routes),
            'path_map': path_map,
            'current_page': 1,
            'total_pages': [1],
        })

    return redirect('plan:plan')
