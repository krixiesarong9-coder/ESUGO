from django import forms
from django.contrib.auth.forms import AuthenticationForm
from .models import Product, Profile, StoreSettings


class ProductUploadForm(forms.ModelForm):
    """Form store owners use to upload products"""
    class Meta:
        model = Product
        fields = ['name', 'slug', 'category', 'description', 'price', 'stock', 'image', 'is_available']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Product name',
            }),
            'slug': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'product-url-name',
            }),
            'category': forms.Select(attrs={
                'class': 'form-select',
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Describe this product',
                'rows': 4,
            }),
            'price': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0.00',
                'step': '0.01',
            }),
            'stock': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Available quantity',
            }),
            'image': forms.ClearableFileInput(attrs={
                'class': 'form-control',
            }),
            'is_available': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
        }


class StoreSettingsForm(forms.ModelForm):
    """Form for store location and opening hours"""
    class Meta:
        model = StoreSettings
        fields = ['store_name', 'location', 'opening_hours']
        widgets = {
            'store_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Store name',
            }),
            'location': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Store address or delivery coverage area',
                'rows': 3,
            }),
            'opening_hours': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Example: Mon-Sat, 8:00 AM - 8:00 PM',
            }),
        }


class UserProfileForm(forms.ModelForm):
    """Form for user profile"""
    class Meta:
        model = Profile
        fields = ['phone', 'address', 'city', 'postal_code']
        widgets = {
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Phone number',
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Street address',
                'rows': 2,
            }),
            'city': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'City',
            }),
            'postal_code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Postal code',
            }),
        }


BARANGAY_CHOICES = [
    ('', 'Select barangay'),
    ('Bugsukan', 'Bugsukan'),
    ('Buntalid', 'Buntalid'),
    ('Cabangahan', 'Cabangahan'),
    ('Cabas-an', 'Cabas-an'),
    ('Calagdaan', 'Calagdaan'),
    ('Consuelo', 'Consuelo'),
    ('General Island', 'General Island'),
    ('Lininti-an', 'Lininti-an'),
    ('Lobo', 'Lobo'),
    ('Magasang', 'Magasang'),
    ('Magosilom', 'Magosilom'),
    ('Pag-antayan', 'Pag-antayan'),
    ('Palasao', 'Palasao'),
    ('Parang', 'Parang'),
    ('San Pedro', 'San Pedro'),
    ('Tapi', 'Tapi'),
    ('Tigabong', 'Tigabong'),
]


class CheckoutForm(forms.Form):
    """Checkout form for order placement"""
    first_name = forms.CharField(max_length=100, required=True, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'First name',
    }))
    last_name = forms.CharField(max_length=100, required=True, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Last name',
    }))
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={
        'class': 'form-control',
        'placeholder': 'Email address',
    }))
    phone = forms.CharField(max_length=15, required=True, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Phone number',
    }))
    address = forms.ChoiceField(required=True, choices=BARANGAY_CHOICES, widget=forms.Select(attrs={
        'class': 'form-select',
    }))
    postal_code = forms.CharField(max_length=10, required=True, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Postal code',
    }))
    notes = forms.CharField(required=False, widget=forms.Textarea(attrs={
        'class': 'form-control',
        'placeholder': 'Order notes (optional)',
        'rows': 3,
    }))


class LoginForm(AuthenticationForm):
    """Custom login form with styled widgets"""
    username = forms.CharField(max_length=150, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Enter your username',
        'autofocus': True,
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-control',
        'placeholder': 'Enter your password',
    }))
