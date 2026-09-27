from django import forms
from .models import Attendance


class ClockInForm(forms.Form):
    notes = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Optional clock-in notes / location...'
        }),
        label='Notes'
    )


class ClockOutForm(forms.Form):
    notes = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Optional clock-out remarks...'
        }),
        label='Notes'
    )
