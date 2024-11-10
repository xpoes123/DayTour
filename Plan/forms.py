from django import forms

class PlanForm(forms.Form):
    start_loc = forms.CharField(
        label='Starting Location',
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Where will you start?'})
    )
    radius = forms.DecimalField(
        label='Radius (m)',
        max_digits=5,
        decimal_places=0,
        required=False,
        widget=forms.NumberInput(attrs={'placeholder': 'Enter your radius in meters'})
    )
    
    locations = forms.IntegerField(
        label='Locations',
        required=False,
        widget=forms.NumberInput(
            attrs={
                'type': 'range',  # This creates a slider
                'min': '1',       # Minimum value of the slider
                'max': '9',      # Maximum value of the slider
                'value': '5',     # Default value (you can adjust this)
                'step': '1',      # Step size for the slider
                'placeholder': 'Enter how many locations you want to visit',
            }
        )
    )