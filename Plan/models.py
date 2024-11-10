from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.postgres.fields import JSONField  # Use this import if your Django version is <3.1; otherwise use models.JSONField

class Location(models.Model):
    google_id = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=100, default="DEFAULT")
    def __str__(self):
        return self.google_id

    def average_rating(self):
        """Calculate and return the average rating based on related reviews."""
        reviews = self.location_reviews.all()
        if not reviews.exists():
            return None  # No reviews to calculate an average
        return sum(review.rating for review in reviews) / reviews.count()

class Review(models.Model):
    location = models.ForeignKey(Location, on_delete=models.CASCADE, related_name='location_reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    review_text = models.TextField(max_length=1000, blank=True)

    def __str__(self):
        return f"{self.user.username} rated {self.location.name} {self.rating} stars"

class Itinerary(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='itineraries')
    locations = models.JSONField(default=list, blank=True)  # Store a list of Google IDs as JSON
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed = models.BooleanField(default=False)

    def __str__(self):
        return f"Itinerary {self.locations[0]} for {self.user.username} | {self.created_at.strftime('%m-%d')}"