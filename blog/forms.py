# blog/forms.py
from django import forms
from plan.models import Review, Itinerary



class PostForm(forms.Form):
    itinerary = forms.ModelChoiceField(queryset=Itinerary.objects.all(), required=True)
    review = forms.CharField(widget=forms.Textarea, required=False)
    rating = forms.IntegerField(min_value=1, max_value=5, required=False)  # Make sure this is included

    class Meta:
        model = Review
        fields = ['itinerary', 'review', 'rating']