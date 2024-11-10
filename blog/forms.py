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
    rating = forms.IntegerField(
        label="Rating",
        required=True,
        min_value=1,
        max_value=5,
        widget=forms.Select(choices=[(i, f"{i} Star{'s' if i > 1 else ''}") for i in range(1, 6)])
    )
