from django.contrib import messages  # To display form errors in the template
from django.shortcuts import render, redirect
from .forms import PostForm
from .models import BlogPost
from plan.models import Review, Itinerary,Location
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from django.http import JsonResponse
from .models import BlogPost

def location_blogs(request, location_id):
    # Get the location object by ID
    location = get_object_or_404(Location, id=location_id)
    
    # Get all blog posts related to this location
    blogs = BlogPost.objects.filter(location=location.name).order_by('-date_posted')
    
    # Set up pagination for the blog posts
    paginator = Paginator(blogs, 5)  # Show 5 blog posts per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'location': location,
        'page_obj': page_obj,
    }
    return render(request, 'blog/location_blogs.html', context)


@login_required
def create_post(request):
    if request.method == 'POST':
        form = PostForm(request.POST)
        if form.is_valid():
            itinerary = form.cleaned_data['itinerary']
            overall_review_text = form.cleaned_data['review']
            overall_rating = form.cleaned_data['rating']
            user = request.user

            if itinerary.locations:
                # Loop through each location in itinerary.locations to handle individual reviews and create a BlogPost
                for place_name in itinerary.locations:
                    # Fetch the Location object by name
                    location = get_object_or_404(Location, name=place_name)
                    
                    # Fetch individual review and rating for each location from POST data
                    location_review_text = request.POST.get(f'location_review_{place_name}', overall_review_text)
                    location_rating = request.POST.get(f'location_rating_{place_name}', overall_rating)
                    
                    try:
                        # Convert rating to integer and validate within range
                        location_rating = int(location_rating)
                        if location_rating < 1 or location_rating > 5:
                            raise ValueError("Invalid rating value")
                    except ValueError:
                        location_rating = overall_rating  # Fall back to overall rating if conversion fails

                    # Create a Review instance for each location
                    review = Review.objects.create(
                        location=location,
                        user=user,
                        rating=location_rating,
                        review_text=location_review_text
                    )

                    # Create a BlogPost for each Review and associated Location
                    BlogPost.objects.create(
                        user=user,
                        location=location.name,  # Associate the location name for this BlogPost
                        review=review,  # Associate this review as the main review for the BlogPost
                        rating=location_rating
                    )

                # Mark itinerary as reviewed if reviews have been created
                itinerary.reviewed = True
                itinerary.save()

                return redirect('blog:blog')
            else:
                messages.error(request, "No valid location found for this itinerary.")
        else:
            messages.error(request, "There was an error in your submission. Please check the fields below.")
            print("Form errors:", form.errors)

    else:
        form = PostForm()

    return render(request, 'blog/create_post.html', {'form': form})




def blog(request):
    # Fetch all blog posts ordered by date posted, most recent first
    blog_posts = BlogPost.objects.all().order_by('-date_posted')
    
    # Set up pagination: 10 blog posts per page
    paginator = Paginator(blog_posts, 5)  # Show 10 blog posts per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
    }
    return render(request, 'blog/blog_list.html', context)

def user_blogs(request, user_id):
    # Get the user
    user = get_object_or_404(User, id=user_id)

    # Get all blog posts by the user, ordered by date posted
    blog_posts = BlogPost.objects.filter(user=user).order_by('-date_posted')
    
    # Set up pagination: 10 blog posts per page
    paginator = Paginator(blog_posts, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'user': user,
        'page_obj': page_obj,
    }
    return render(request, 'blog/user_blogs.html', context)


def blog_detail(request, blog_id):
    blog_post = get_object_or_404(BlogPost, id=blog_id)
    return render(request, 'blog/blog_detail.html', {'blog_post': blog_post})


def get_location_ids(request, itinerary_id):
    print(f"Fetching locations for itinerary ID: {itinerary_id}")  # Debugging log
    itinerary = get_object_or_404(Itinerary, id=itinerary_id)
    
    # Since locations is now a JSON field, we can directly access the list of Google IDs
    location_ids = itinerary.locations
    print(f"Location IDs: {location_ids}")  # Debugging log
    
    return JsonResponse({'location_ids': location_ids})
