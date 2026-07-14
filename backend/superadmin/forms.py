from django import forms
from django.core.exceptions import ValidationError
from superadmin.models import User

class LoginForm(forms.Form):
    username = forms.CharField(max_length=150, widget=forms.TextInput(attrs={'placeholder': 'Username or Email'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Password'}))
    remember_me = forms.BooleanField(required=False, label="Remember Me")

class CustomUserCreationForm(forms.Form):
    # Additional custom fields
    username = forms.CharField(max_length=30, required=True, widget=forms.TextInput(attrs={'placeholder': 'Username'}))
    first_name = forms.CharField(max_length=30, required=True, widget=forms.TextInput(attrs={'placeholder': 'First Name'}))
    last_name = forms.CharField(max_length=30, required=True, widget=forms.TextInput(attrs={'placeholder': 'Last Name'}))
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'placeholder': 'Email'}))
    phone = forms.CharField(max_length=30, required=True, widget=forms.TextInput(attrs={'placeholder': 'Phone No'}))
    
    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Password'}),
        label="Password"
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Confirm Password'}),
        label="Confirm Password"
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password', 'phone']

    def clean_username(self):
        username = self.cleaned_data.get('username')
        user = User.objects(username=username)
        if user:
            raise ValidationError("This username is already taken.")
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        user = User.objects(email=email)
        if user:
            raise ValidationError("This email is already taken.")
        return email

    def clean(self):
        cleaned_data = super().clean()

        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")

        if password1 and password2 and password1 != password2:
            raise ValidationError("The two password fields must match.")

        return cleaned_data

    def save(self, commit=True):
        cleaned_data = self.cleaned_data
        
        # Create a new User instance
        user = User(
            username=cleaned_data['username'],
            first_name=cleaned_data['first_name'],
            last_name=cleaned_data['last_name'],
            email=cleaned_data['email'],
            phone=cleaned_data['phone'],
        )
        
        # Set the password after hashing it
        user.set_password(cleaned_data['password1'])
        
        # Save the user instance
        user.save()

        return user