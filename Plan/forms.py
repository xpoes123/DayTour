from django import forms

class PlanForm(forms.Form):
    start_loc = forms.CharField(
        label='Starting Location',
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Where will you start?'})
    )
    start_time = forms.TimeField(
        label='Starting Time',
        required=False,
        widget=forms.TimeInput(attrs={'type': 'time', 'placeholder': 'Starting time'})
    )
    end_time = forms.TimeField(
        label='Ending Time',
        required=False,
        widget=forms.TimeInput(attrs={'type': 'time', 'placeholder': 'End time'})
    )
    budget = forms.DecimalField(
        label='Budget',
        max_digits=10,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={'placeholder': 'Enter your budget in dollars'})
    )
    required_stops = forms.CharField(
        label='Required Stops',
        max_length=300,
        required=False,
        widget=forms.Textarea(attrs={'placeholder': 'List required stops, separated by commas', 'rows': 3})
    )
