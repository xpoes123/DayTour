from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from .forms import CreateUserForm, EditProfileForm, CustomPasswordChangeForm
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, get_user_model, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponseForbidden
from plan.models import Location, Itinerary




def users_list(request):
    query = request.GET.get('q', '')  # Get the search query from the request
    users = User.objects.filter(Q(username__icontains=query) | Q(email__icontains=query)).order_by('username')

    paginator = Paginator(users, 10)  # Show 10 users per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'authuser/users_list.html', {'users': users, 'page_obj': page_obj})


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
    form = AuthenticationForm()  # Initialize the form
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)  # Populate with POST data
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('home:home')
        else:
            messages.info(request, "Username or Password is incorrect")

    context = {'form': form}
    return render(request, 'authuser/login.html', context)

def logout_user(request):
    logout(request)
    return redirect('authuser:login')

def profile(request, user_id):
    user = get_object_or_404(User, id=user_id)
    return render(request, 'authuser/profile.html', {'profile_user': user})

@login_required
def edit_profile(request, user_id):
    # Ensure the logged-in user is the one being edited
    if request.user.id != user_id:
        return HttpResponseForbidden("You do not have permission to edit this profile.")

    user = get_object_or_404(User, id=user_id)

    if request.method == 'POST':
        profile_form = EditProfileForm(request.POST, request.FILES, instance=user)
        password_form = CustomPasswordChangeForm(user, request.POST)

        if profile_form.is_valid() and password_form.is_valid():
            profile_form.save()
            password_form.save()
            update_session_auth_hash(request, password_form.user)  # Keep user logged in after password change
            return redirect('authuser:profile', user_id=user.id)

    else:
        profile_form = EditProfileForm(instance=user)
        password_form = CustomPasswordChangeForm(user)

    return render(request, 'authuser/edit_profile.html', {
        'profile_form': profile_form,
        'password_form': password_form
    })
    
@login_required
def visits(request, user_id):
   
    return render(request, 'plan:user_visits.html', {})