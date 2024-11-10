# blog/forms.py
from django import forms
from plan.models import Review, Itinerary


class PostForm(forms.ModelForm):
    itinerary = forms.ModelChoiceField(
        queryset=Itinerary.objects.filter(reviewed=False),
        label="Select Itinerary",
        empty_label="Choose an itinerary to review",
        required=True
    )
    review = forms.CharField(
        label="Your Review",
        max_length=1000,
        required=True,
        widget=forms.Textarea(attrs={'rows': 5, 'placeholder': 'Share your experience here!'})
    )
    rating = forms.IntegerField(
        label="Rating",
        required=True,
        min_value=1,
        max_value=5,
        widget=forms.HiddenInput()
    )

    class Meta:
        model = Review
        fields = ['itinerary', 'review', 'rating']