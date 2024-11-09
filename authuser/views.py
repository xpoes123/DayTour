from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from .forms import CreateUserForm
from django.contrib import messages




def register(request):
    """
    Registration request to make a new account
    """
    form = CreateUserForm()
    if request.method == "POST":
        form = CreateUserForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f"Account was created for {user.username}")
            return redirect('music:login')
    context = {'form': form}
    return render(request, 'authuser/register.html', context)