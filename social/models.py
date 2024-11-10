# social/models.py

from django.db import models
from django.contrib.auth.models import User
from django.contrib.postgres.fields import ArrayField
from django.core.validators import MinValueValidator, MaxValueValidator

class Location(models.Model):
    google_id = models.CharField(max_length=255, unique=True)  # Unique identifier for each location
    hours = models.CharField(max_length=255)  # Store hours as a string (e.g., "9am - 5pm")
    price = models.DecimalField(max_digits=10, decimal_places=2)  # Store price with two decimal places

    # List of integer reviews with values between 1 and 5
    reviews = ArrayField(
        models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)]),
        blank=True,
        default=list
    )

    def __str__(self):
        return f"Location {self.google_id}"
    
    def average_rating(self):
        """Calculate and return the average rating based on reviews."""
        if not self.reviews:
            return None  # No reviews to calculate an average
        return sum(self.reviews) / len(self.reviews)

    def add_review(self, rating):
        """Add a new review rating to the reviews list."""
        if 1 <= rating <= 5:
            self.reviews.append(rating)
            self.save()
        else:
            raise ValueError("Rating must be an integer between 1 and 5.")

class UserRating(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    location = models.ForeignKey(Location, on_delete=models.CASCADE)  # Direct reference to Location model
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])  # Rating from 1 to 5

    def __str__(self):
        return f"{self.user.username} rated {self.location} {self.rating} stars"
