from django import forms
from .models import User, DonationRequest, BloodRequest, EmergencyPost

BLOOD_GROUP_CHOICES = (
    ('', '-- Select Blood Group --'),
    ('A+', 'A+'),
    ('A-', 'A-'),
    ('B+', 'B+'),
    ('B-', 'B-'),
    ('AB+', 'AB+'),
    ('AB-', 'AB-'),
    ('O+', 'O+'),
    ('O-', 'O-'),
)

class DonorProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'phone', 'blood_group', 'location', 'is_available']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control rounded-pill'}),
            'email': forms.EmailInput(attrs={'class': 'form-control rounded-pill'}),
            'phone': forms.TextInput(attrs={'class': 'form-control rounded-pill'}),
            'blood_group': forms.Select(attrs={'class': 'form-select rounded-pill'}),
            'location': forms.TextInput(attrs={'class': 'form-control rounded-pill'}),
            'is_available': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class DonationRequestForm(forms.ModelForm):
    blood_group = forms.ChoiceField(choices=BLOOD_GROUP_CHOICES, widget=forms.Select(attrs={'class': 'form-select'}))
    
    class Meta:
        model = DonationRequest
        fields = ['blood_bank', 'date', 'blood_group', 'units']
        widgets = {
            'blood_bank': forms.Select(attrs={'class': 'form-select'}),
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'units': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'})
        }

class BloodRequestForm(forms.ModelForm):
    blood_group = forms.ChoiceField(choices=BLOOD_GROUP_CHOICES, widget=forms.Select(attrs={'class': 'form-select'}))
    
    class Meta:
        model = BloodRequest
        fields = ['blood_bank', 'blood_group', 'units_needed', 'urgency']
        widgets = {
            'blood_bank': forms.Select(attrs={'class': 'form-select'}),
            'units_needed': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'urgency': forms.Select(attrs={'class': 'form-select'})
        }

class DonorRegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    blood_group = forms.ChoiceField(choices=BLOOD_GROUP_CHOICES, widget=forms.Select(attrs={'class': 'form-select'}))
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'blood_group', 'location', 'phone']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
        }
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        user.role = 'donor'
        if commit: user.save()
        return user

class HospitalRegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'location', 'phone']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
        }
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        user.role = 'hospital'
        if commit: user.save()
        return user
 
class EmergencyPostForm(forms.ModelForm):
    class Meta:
        model = EmergencyPost
        fields = ['patient_name', 'blood_group', 'disease_name', 'location', 'needed_by', 'description']
        widgets = {
            'patient_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Patient name'}),
            'blood_group': forms.Select(attrs={'class': 'form-select'}),
            'disease_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Disease/Condition'}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Location'}),
            'needed_by': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
        }    