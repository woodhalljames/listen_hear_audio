from django import forms
from django.core.validators import RegexValidator


class CheckoutForm(forms.Form):
    """Form for collecting customer information at checkout"""
    
    contact_person = forms.CharField(
        max_length=200,
        label='Contact Person',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Full Name'
        })
    )
    
    email = forms.EmailField(
        label='Email Address',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'your.email@example.com'
        })
    )
    
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
    )
    phone = forms.CharField(
        validators=[phone_regex],
        max_length=20,
        label='Phone Number',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '(123) 456-7890'
        })
    )
    
    street = forms.CharField(
        label='Street Address (Optional)',
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '123 Main Street'
        })
    )

    city = forms.CharField(
        max_length=100,
        label='City',
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'City'
        })
    )

    state = forms.CharField(
        max_length=2,
        label='State (Optional)',
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'PA',
            'maxlength': '2',
            'style': 'text-transform: uppercase;'
        }),
        help_text='2-letter state abbreviation'
    )

    zip_code = forms.CharField(
        max_length=10,
        label='ZIP Code',
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '12345'
        })
    )
    
    website = forms.URLField(
        required=False,
        label='Website (Optional)',
        widget=forms.URLInput(attrs={
            'class': 'form-control',
            'placeholder': 'https://yourwebsite.com'
        }),
        help_text='For builders/contractors'
    )
    
    notes = forms.CharField(
        required=False,
        label='Additional Notes',
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Tell us about your project, timeline, or any special requirements...'
        })
    )
    
    def clean_phone(self):
        """Clean and format phone number"""
        phone = self.cleaned_data.get('phone')
        # Remove common formatting characters
        phone = phone.replace('(', '').replace(')', '').replace('-', '').replace(' ', '').replace('+', '')
        return phone

    def clean_state(self):
        """Convert state to uppercase"""
        state = self.cleaned_data.get('state', '')
        return state.upper()