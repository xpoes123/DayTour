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

    # Placeholder fields for required stops
    stop_1_location = forms.CharField(label="Location", max_length=100, required=False)
    stop_1_start_time = forms.TimeField(label="Start Time", required=False, widget=forms.TimeInput(attrs={'type': 'time'}))
    stop_1_duration = forms.DurationField(label="Duration (min)", required=False)

    stop_2_location = forms.CharField(label="Location", max_length=100, required=False)
    stop_2_start_time = forms.TimeField(label="Start Time", required=False, widget=forms.TimeInput(attrs={'type': 'time'}))
    stop_2_duration = forms.DurationField(label="Duration (min)", required=False)

    stop_3_location = forms.CharField(label="Location", max_length=100, required=False)
    stop_3_start_time = forms.TimeField(label="Start Time", required=False, widget=forms.TimeInput(attrs={'type': 'time'}))
    stop_3_duration = forms.DurationField(label="Duration (min)", required=False)
