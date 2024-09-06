from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import BusPass, Payment

class RegisterForm(UserCreationForm):
    email = forms.EmailField()

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

class BusPassForm(forms.ModelForm):
    class Meta:
        model = BusPass
        fields = ['full_name', 'pass_id', 'user_class', 'college', 'from_place', 'to_place']

class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['transaction_id', 'upi_id']
