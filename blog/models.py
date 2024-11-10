# blog/models.py
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from plan.models import Review


class BlogPost(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='blog_posts')
    date_posted = models.DateTimeField(default=timezone.now)
    location = models.CharField(max_length=255)  # This can also be a ForeignKey if you have a Location model
    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name='blog_posts')  # Link to Review
    rating = models.IntegerField(
        validators=[
            MinValueValidator(1),
            MaxValueValidator(5)
        ]
    )

    def __str__(self):
        return f"{self.user.username}'s post on {self.location}"

    class Meta:
        ordering = ['-date_posted']
