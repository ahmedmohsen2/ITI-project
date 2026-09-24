from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import Category, Order, Product


class RegisterForm(UserCreationForm):
    email = forms.EmailField()

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ("name", "category", "description", "price", "stock_quantity", "image_url", "active")


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ("name", "description", "active")


class OrderStatusForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ("status",)
