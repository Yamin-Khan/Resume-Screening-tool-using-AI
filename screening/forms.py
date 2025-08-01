from django import forms
from .models import ContactMessage, BusinessProfile
from django.contrib.auth.models import User
from django.contrib.auth import password_validation
from django.contrib.auth.forms import PasswordChangeForm, UserCreationForm

class ProfileUpdateForm(forms.ModelForm):
    current_password = forms.CharField(
        label="Current Password",
        strip=False,
        widget=forms.PasswordInput(attrs={'class': 'w-full bg-gray-100 border border-gray-300 rounded-lg px-4 py-2 text-gray-800', 'autocomplete': 'current-password'}),
        required=False,
        help_text="Enter your current password to confirm changes or to change your password"
    )
    
    new_password1 = forms.CharField(
        label="New Password",
        strip=False,
        widget=forms.PasswordInput(attrs={'class': 'w-full bg-gray-100 border border-gray-300 rounded-lg px-4 py-2 text-gray-800', 'autocomplete': 'new-password'}),
        required=False,
        help_text=password_validation.password_validators_help_text_html()
    )
    
    new_password2 = forms.CharField(
        label="Confirm New Password",
        strip=False,
        widget=forms.PasswordInput(attrs={'class': 'w-full bg-gray-100 border border-gray-300 rounded-lg px-4 py-2 text-gray-800', 'autocomplete': 'new-password'}),
        required=False,
        help_text="Enter the same password as before, for verification."
    )
    
    class Meta:
        model = User
        fields = ['username', 'email']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control bg-dark text-white', 'placeholder': 'Username'}),
            'email': forms.EmailInput(attrs={'class': 'form-control bg-dark text-white', 'placeholder': 'Email'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'w-full bg-gray-100 border border-gray-300 rounded-lg px-4 py-2 text-gray-800'})
    
    def clean(self):
        cleaned_data = super().clean()
        current_password = cleaned_data.get('current_password')
        new_password1 = cleaned_data.get('new_password1')
        new_password2 = cleaned_data.get('new_password2')
        
        # Check if the user wants to change their password
        if new_password1 or new_password2:
            if not current_password:
                self.add_error('current_password', 'Current password is required to change your password')
            elif not self.instance.check_password(current_password):
                self.add_error('current_password', 'Current password is incorrect')
            
            if new_password1 != new_password2:
                self.add_error('new_password2', "The two password fields didn't match")
            
            # Validate the new password
            if new_password1:
                try:
                    password_validation.validate_password(new_password1, self.instance)
                except forms.ValidationError as error:
                    self.add_error('new_password1', error)
        
        # Only require password for username changes (email is less sensitive)
        elif 'username' in self.changed_data and not current_password:
            self.add_error('current_password', 'Current password is required to update your username')
        elif 'username' in self.changed_data and not self.instance.check_password(current_password):
            self.add_error('current_password', 'Current password is incorrect')
            
        return cleaned_data
    
    def save(self, commit=True):
        user = super().save(commit=False)
        
        # If new password provided and validated, set it
        if self.cleaned_data.get('new_password1'):
            user.set_password(self.cleaned_data.get('new_password1'))
            
        if commit:
            user.save()
        
        return user

class ContactForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ['name', 'email', 'subject', 'message']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Your Name'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Your Email'}),
            'subject': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Subject'}),
            'message': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Your Message', 'rows': 5}),
        }

class UserTypeForm(forms.Form):
    user_type = forms.ChoiceField(
        choices=[('individual', 'Individual User'), ('business', 'Business User')],
        widget=forms.RadioSelect(attrs={'class': 'user-type-radio'}),
        required=True,
        initial='individual'
    )

class BusinessSignupForm(UserCreationForm):
    email = forms.EmailInput()
    company_name = forms.CharField(max_length=200, required=True, 
                                  widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Company Name'}))
    industry = forms.CharField(max_length=100, required=True,
                              widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Industry'}))
    company_size = forms.ChoiceField(choices=BusinessProfile.company_size.field.choices,
                                    widget=forms.Select(attrs={'class': 'form-control'}))
    company_website = forms.URLField(required=False,
                                    widget=forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'Company Website'}))
    company_address = forms.CharField(required=False,
                                     widget=forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Company Address', 'rows': 3}))
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2', 'company_name', 'industry', 'company_size', 'company_website', 'company_address']

class BusinessProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = BusinessProfile
        fields = ['company_name', 'industry', 'company_size', 'company_website', 'company_address']
        widgets = {
            'company_name': forms.TextInput(attrs={'class': 'form-control bg-dark text-white', 'placeholder': 'Company Name'}),
            'industry': forms.TextInput(attrs={'class': 'form-control bg-dark text-white', 'placeholder': 'Industry'}),
            'company_size': forms.Select(attrs={'class': 'form-control bg-dark text-white'}),
            'company_website': forms.URLInput(attrs={'class': 'form-control bg-dark text-white', 'placeholder': 'Company Website'}),
            'company_address': forms.Textarea(attrs={'class': 'form-control bg-dark text-white', 'placeholder': 'Company Address', 'rows': 3}),
        }

class ChatMessageForm(forms.Form):
    message = forms.CharField(widget=forms.Textarea(attrs={'rows': 3, 'placeholder': 'Type your message here...'}), required=True)
