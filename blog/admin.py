# blog/admin.py
from django.contrib import admin
from .models import BlogPost

@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = ('user', 'location', 'rating', 'date_posted')
    list_filter = ('user', 'rating', 'date_posted')
    search_fields = ('user__username', 'location', 'review__review_text')  # Assuming review has a review_text field
    ordering = ('-date_posted',)

    # Optional: Display inline fields for the related Review
    readonly_fields = ('date_posted',)
