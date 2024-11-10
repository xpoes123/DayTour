from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from .forms import CreateUserForm, EditProfileForm, CustomPasswordChangeForm
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, get_user_model, update_session_auth_hash
from django.contrib.auth.decorators import login_required

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
            return redirect('authuser:login')
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

def profile(request, user_id):
    user = get_object_or_404(User, id=user_id)
    return render(request, 'authuser/profile.html', {'profile_user': user})

@login_required
def edit_profile(request, user_id):
    user = get_object_or_404(User, id=user_id)

    if request.method == 'POST':
        profile_form = EditProfileForm(request.POST, request.FILES, instance=user)
        password_form = CustomPasswordChangeForm(user, request.POST)

        if profile_form.is_valid() and password_form.is_valid():
            profile_form.save()
            password_form.save()
            update_session_auth_hash(request, password_form.user)  # Keep user logged in after password change
            return redirect('authuser/profile.html')  # Replace 'profile' with your profile page's URL name

    else:
        profile_form = EditProfileForm(instance=user)
        password_form = CustomPasswordChangeForm(user)

    return render(request, 'authuser/edit_profile.html', {
        'profile_form': profile_form,
        'password_form': password_form
    })