# blog/forms.py
from django import forms
from plan.models import Location

class PostForm(forms.Form):
    location = forms.ModelChoiceField(
        queryset=Location.objects.all(),
        label="Select Location",
        empty_label="Choose a location",
        required=True
    )
    review = forms.CharField(
        label="Your Review",
        max_length=10000,
        required=False,
        widget=forms.Textarea(attrs={'rows': 5, 'placeholder': 'Share your experience here!'})
    )
    rating = forms.IntegerField(widget=forms.HiddenInput(), label="Rating")  # Hidden widget
