from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, JobListing, Application, Client, Freelancer, Interview

class CustomUserCreationForm(UserCreationForm):
    is_client = forms.BooleanField(required=False, label="Sign up as Client")
    is_freelancer = forms.BooleanField(required=False, label="Sign up as Freelancer")

    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + ('email', 'is_client', 'is_freelancer')

class JobListingForm(forms.ModelForm):
    class Meta:
        model = JobListing
        fields = ['title', 'description', 'budget', 'category']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }

class ApplicationForm(forms.ModelForm):
    class Meta:
        model = Application
        fields = ['proposal_text', 'expected_payment']
        widgets = {
            'proposal_text': forms.Textarea(attrs={'rows': 3}),
        }

# --- Updated Profile Forms ---
class ClientProfileForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = ['company_name', 'location']
        widgets = {
            'company_name': forms.TextInput(attrs={'class': 'form-control'}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
        }

class FreelancerProfileForm(forms.ModelForm):
    class Meta:
        model = Freelancer
        fields = ['skills', 'portfolio_link']
        widgets = {
            'skills': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'portfolio_link': forms.URLInput(attrs={'class': 'form-control'}),
        }
# -----------------------------

class InterviewForm(forms.ModelForm):
    PLATFORM_CHOICES = [
        ('Google Meet', 'Google Meet'),
        ('Zoom', 'Zoom'),
    ]
    platform = forms.ChoiceField(
        choices=PLATFORM_CHOICES, 
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    meeting_link = forms.URLField(
        widget=forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'Paste full meeting link here...'})
    )

    class Meta:
        model = Interview
        fields = ['date_time', 'platform', 'meeting_link']
        widgets = {
            'date_time': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        platform = cleaned_data.get('platform')
        link = cleaned_data.get('meeting_link')

        if platform == 'Google Meet' and link and 'google.com' not in link:
            self.add_error('meeting_link', 'Please enter a valid Google Meet link (must contain google.com).')
        
        if platform == 'Zoom' and link and 'zoom.us' not in link:
            self.add_error('meeting_link', 'Please enter a valid Zoom link (must contain zoom.us).')

        return cleaned_data