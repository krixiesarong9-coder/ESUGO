from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm
from django.db.models import Q
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


CITY_PROVINCE_CHOICES = [
    ('', 'Select city/province'),
    ('Carrascal, Surigao del Sur', 'Carrascal, Surigao del Sur'),
    ('Cantilan, Surigao del Sur', 'Cantilan, Surigao del Sur'),
    ('Madrid, Surigao del Sur', 'Madrid, Surigao del Sur'),
    ('Carmen, Surigao del Sur', 'Carmen, Surigao del Sur'),
    ('Lanuza, Surigao del Sur', 'Lanuza, Surigao del Sur'),
]


BARANGAYS_BY_CITY = {
    'Carrascal, Surigao del Sur': [
        'Adlay',
        'Babuyan',
        'Bacolod',
        'Baybay',
        'Bon-ot',
        'Caglayag',
        'Dahican',
        'Doyos',
        'Embarcadero',
        'Gamuton',
        'Panikian',
        'Pantukan',
        'Saca',
        'Tag-Anito',
    ],
    'Cantilan, Surigao del Sur': [
        'Bugsukan',
        'Buntalid',
        'Cabangahan',
        'Cabas-an',
        'Calagdaan',
        'Consuelo',
        'General Island',
        'Lininti-an',
        'Lobo',
        'Magasang',
        'Magosilom',
        'Pag-antayan',
        'Palasao',
        'Parang',
        'San Pedro',
        'Tapi',
        'Tigabong',
    ],
    'Madrid, Surigao del Sur': [
        'Bagsac',
        'Bayogo',
        'Linibonan',
        'Magsaysay',
        'Manga',
        'Panayogon',
        'Patong Patong',
        'Quirino',
        'San Antonio',
        'San Juan',
        'San Roque',
        'San Vicente',
        'Songkit',
        'Union',
    ],
    'Carmen, Surigao del Sur': [
        'Antao',
        'Cancavan',
        'Carmen',
        'Esperanza',
        'Hinapoyan',
        'Puyat',
        'San Vicente',
        'Santa Cruz',
    ],
    'Lanuza, Surigao del Sur': [
        'Agsam',
        'Bocawe',
        'Bunga',
        'Gamuton',
        'Habag',
        'Mampi',
        'Nurcia',
        'Pakwan',
        'Sibahay',
        'Zone I',
        'Zone II',
        'Zone III',
        'Zone IV',
    ],
}

BARANGAY_CHOICES = [('', 'Select barangay')]
for city, barangays in BARANGAYS_BY_CITY.items():
    municipality = city.split(',')[0]
    BARANGAY_CHOICES.extend(
        (f'{barangay} ({municipality})', f'{barangay} ({municipality})')
        for barangay in barangays
    )


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
    city = forms.ChoiceField(required=True, choices=CITY_PROVINCE_CHOICES, widget=forms.Select(attrs={
        'class': 'form-select',
    }))
    barangay = forms.ChoiceField(required=True, choices=BARANGAY_CHOICES, widget=forms.Select(attrs={
        'class': 'form-select',
    }))
    address = forms.CharField(max_length=255, required=True, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'House no. / Street / Purok',
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

    def clean(self):
        cleaned_data = super().clean()
        city = cleaned_data.get('city')
        barangay = cleaned_data.get('barangay')

        municipality = city.split(',')[0] if city else ''
        city_barangays = {
            f'{name} ({municipality})'
            for name in BARANGAYS_BY_CITY.get(city, [])
        }

        if city and barangay and barangay not in city_barangays:
            self.add_error('barangay', 'Please select a barangay from the selected city/province.')

        return cleaned_data


class LoginForm(AuthenticationForm):
    """Custom login form with styled widgets"""
    username = forms.CharField(max_length=150, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Enter your username or email',
        'autofocus': True,
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-control',
        'placeholder': 'Enter your password',
    }))

    def clean(self):
        identity = self.cleaned_data.get('username', '').strip()
        if identity:
            user = User.objects.filter(
                Q(username__iexact=identity) | Q(email__iexact=identity)
            ).first()
            if user:
                self.cleaned_data['username'] = user.get_username()
        return super().clean()
