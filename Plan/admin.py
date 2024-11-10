from django.contrib import admin
from .models import Location, Review, Itinerary  # Ensure this path matches where your models are defined

@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ('id', 'google_id', 'name')
    search_fields = ('id', 'google_id', 'name')


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('user', 'location', 'rating', 'review_text')
    search_fields = ('user__username', 'location__google_id', 'review_text')
    list_filter = ('rating',)
    
@admin.register(Itinerary)
class ItineraryAdmin(admin.ModelAdmin):
    list_display = ('id','user', 'created_at', 'reviewed')
    search_fields = ('user__username',)
    list_filter = ('reviewed', 'created_at')
