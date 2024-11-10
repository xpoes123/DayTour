from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from .forms import CreateUserForm
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, get_user_model



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

def login_page(request):
    """
    Login request to login to an existing account
    """
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('home:home')
        else:
            messages.info(request, "Username or Password is incorrect")
    context = {}
    return render(request, 'authuser/login.html', context)

def logout_user(request):
    logout(request)
    return redirect('authuser:login')