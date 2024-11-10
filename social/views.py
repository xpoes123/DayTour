# social/views.py

from django.shortcuts import render, redirect
from .forms import RateLocationForm
from .models import UserRating

def rate_location(request):
    if request.method == 'POST':
        form = RateLocationForm(request.POST, user=request.user)
        if form.is_valid():
            rating = form.save(commit=False)
            rating.user = request.user
            rating.save()
            return redirect('rate')
    else:
        form = RateLocationForm(user=request.user)
    
    return render(request, 'social/rate.html', {'form': form})

def add_location(request):
    if request.method == 'POST':
        form = RateLocationForm(request.POST, user=request.user)
        if form.is_valid():
            rating = form.save(commit=False)
            rating.user = request.user
            rating.save()
            return redirect('rate')
    else:
        form = RateLocationForm(user=request.user)
    
    return render(request, 'social/rate.html', {'form': form})