# social/forms.py
from django import forms
from .models import UserRating, Location

class RateLocationForm(forms.ModelForm):
    location = forms.ModelChoiceField(queryset=Location.objects.none(), label="Choose a location")

    class Meta:
        model = UserRating
        fields = ['location', 'rating']
        widgets = {
            'rating': forms.HiddenInput()
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            rated_locations = UserRating.objects.filter(user=user).values_list('location', flat=True)
            self.fields['location'].queryset = Location.objects.filter(id__in=rated_locations)

class AddLocationForm(forms.ModelForm):
    loc = forms.CharField(
        label='Location',
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Location'})
    )

    class Meta:
        model = UserRating
        fields = ['location', 'rating']
        widgets = {
            'rating': forms.HiddenInput()
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            rated_locations = UserRating.objects.filter(user=user).values_list('location', flat=True)
            self.fields['location'].queryset = Location.objects.filter(id__in=rated_locations)
