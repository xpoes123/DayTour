from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator

class Location(models.Model):
    name = models.CharField(max_length=100, default="Unnamed Location", unique=True)

    def __str__(self):
        return self.name

    def average_rating(self):
        """Calculate and return the average rating based on related reviews."""
        reviews = self.location_reviews.all()  # Updated to match the new related_name
        if not reviews:
            return None  # No reviews to calculate an average
        return sum(review.rating for review in reviews) / reviews.count()

class Review(models.Model):
    location = models.ForeignKey(Location, on_delete=models.CASCADE, related_name='location_reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    review_text = models.TextField(max_length=1000, blank=True)

    def __str__(self):
        return f"{self.user.username} rated {self.location.name} {self.rating} stars"
