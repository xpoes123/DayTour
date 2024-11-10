from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from .forms import PlanForm
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, get_user_model
from .services.place_list_to_map_url import path_to_url



def plan(request):
    """
    Registration request to make a new account
    """
    form = PlanForm()
    if request.method == "POST":
        form = PlanForm(request.POST)
        if form.is_valid():
            artists = [form.cleaned_data[f'artist_{i}'].strip() for i in range(1, 6) if form.cleaned_data.get(f'artist_{i}')]
            if not artists:
                messages.error(request, "Please enter at least one artist.")
                return redirect('plan:start')
            # Store the artists in the session
            request.session['seed_artists'] = artists
              # Redirect to recommend view after setting seed artists
            return redirect('plan:itinerary')
        else:
            messages.error(request, "Invalid form submission.")
    return render(request, 'plan/start.html', {'form': form})

def itinerary(request):
    # Sample data for travel_plan
    travel_plan = [
        ["Location A", "Location B", "15 mins", "8:00 AM", "1 hour"],
        ["Location B", "Location C", "10 mins", "9:15 AM", "30 mins"],
        ["Location C", "Location D", "20 mins", "10:00 AM", "1.5 hours"],
    ]
    path_map = path_to_url(['ChIJQ-U7wYqAhYAReKjwcBt6SGU', 'ChIJE-5gllSBhYARsYVQC_gftuI', 'ChIJl3ZcoouAhYAR1DI821H-LUw', 'ChIJlRvon4yAhYARMw91ij6m610', 'ChIJB0Z9x4uAhYAR2rmxctOAnNA', 'ChIJ1855cG2BhYARSDtIa8RAsQs', 'ChIJ4W9VVouAhYARm7UjFtckzSE', 'ChIJmWz0tuKBhYARmCL4IYfCf0Q', 'ChIJYXDDl4qAhYAReRkaZFbsSzo', 'ChIJY8jq4G2BhYARSkNa7_mZ5eE'])
    context = {
        "travel_plan": travel_plan,
        "path_map": path_map,
    }
    return render(request, 'plan/itinerary.html', context)
