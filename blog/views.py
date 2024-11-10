from django.contrib import messages  # To display form errors in the template
from django.shortcuts import render, redirect
from .forms import PostForm
from .models import BlogPost
from plan.models import Review
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator


@login_required
def create_post(request):
    if request.method == 'POST':
        form = PostForm(request.POST)
        if form.is_valid():
            # Extract data from the form
            location = form.cleaned_data['location']
            review_text = form.cleaned_data['review']
            rating = form.cleaned_data['rating']

            # Create and save the Review instance
            review = Review.objects.create(
                location=location,
                user=request.user,
                rating=rating,
                review_text=review_text
            )

            # Create and save the BlogPost instance using the same data
            BlogPost.objects.create(
                user=request.user,
                location=location.name if hasattr(location, 'name') else location,  # Adjust depending on location model
                review=review_text,
                rating=rating
            )

            # Redirect to the blog list view after successful creation
            return redirect('blog:blog')  # Ensure this URL name exists
        else:
            # If the form is invalid, print errors and display messages
            print(form.errors)
            messages.error(request, "There was an error in your submission. Please check the fields below.")
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