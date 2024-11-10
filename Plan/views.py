from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from .forms import PlanForm
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, get_user_model



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
