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
                'type': 'range',
                'min': '1',
                'max': '10',
                'value': '5',
                'step': '1',
                'oninput': 'document.getElementById("locationValue").textContent = this.value'
            }
        )
    )


    # ✅ Advanced Options Below

    start_time = forms.TimeField(
        label='Start Time',
        required=False,
        widget=forms.TimeInput(attrs={'type': 'time'})
    )

    end_time = forms.TimeField(
        label='End Time',
        required=False,
        widget=forms.TimeInput(attrs={'type': 'time'})
    )

    budget = forms.DecimalField(
        label='Max Budget',
        max_digits=6,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={'placeholder': 'Enter max budget'})
    )

    transit_mode = forms.ChoiceField(
        label='Transit Mode',
        choices=[
            ('walking', 'Walking'),
            ('driving', 'Driving'),
            ('biking', 'Biking'),
            ('transit', 'Public Transit')
        ],
        required=False,
        widget=forms.RadioSelect
    )
