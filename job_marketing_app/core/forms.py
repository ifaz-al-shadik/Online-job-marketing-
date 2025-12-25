from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, JobListing, Application
from .models import Interview # <--- Make sure to import Interview at the top

class CustomUserCreationForm(UserCreationForm):
    is_client = forms.BooleanField(required=False, label="I want to hire (Client)")
    is_freelancer = forms.BooleanField(required=False, label="I want to work (Freelancer)")

    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + ('email', 'is_client', 'is_freelancer')

    def clean(self):
        cleaned_data = super().clean()
        is_client = cleaned_data.get('is_client')
        is_freelancer = cleaned_data.get('is_freelancer')

        if not is_client and not is_freelancer:
            raise forms.ValidationError("Please select at least one role (Client or Freelancer).")
        return cleaned_data

class JobListingForm(forms.ModelForm):
    class Meta:
        model = JobListing
        fields = ['title', 'description', 'budget', 'deadline', 'category']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Python Developer Needed'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Describe the job details...'}),
            'budget': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '$'}),
            'deadline': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
        }

class ApplicationForm(forms.ModelForm):
    class Meta:
        model = Application
        fields = ['proposal_text', 'expected_payment']
from .models import Client, Freelancer, Skill # Ensure Skill is imported

class ClientProfileForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = ['company_name', 'description']
        widgets = {
            'company_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Tech Solutions Ltd.'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Tell us about your company...'}),
        }

class FreelancerProfileForm(forms.ModelForm):
    class Meta:
        model = Freelancer
        fields = ['experience_level', 'portfolio_url', 'skills']
        widgets = {
            'experience_level': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Senior Python Developer'}),
            'portfolio_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://github.com/...'}),
            'skills': forms.CheckboxSelectMultiple(), # This lets them pick multiple skills
        }
# In core/forms.py

class InterviewForm(forms.ModelForm):
    # 1. Add a dropdown for the user to pick the platform
    PLATFORM_CHOICES = [
        ('Google Meet', 'Google Meet'),
        ('Zoom', 'Zoom'),
    ]
    platform = forms.ChoiceField(
        choices=PLATFORM_CHOICES, 
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    # 2. A strict URL field to ensure they paste a real link
    meeting_link = forms.URLField(
        widget=forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'Paste the full meeting link here...'})
    )

    class Meta:
        model = Interview
        # We only show Date, Platform, and Link. 
        # We will save 'platform' + 'meeting_link' into 'link_or_location' automatically.
        fields = ['date_time', 'platform', 'meeting_link']
        widgets = {
            'date_time': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        platform = cleaned_data.get('platform')
        link = cleaned_data.get('meeting_link')

        # 3. Validation: Ensure the link matches the platform
        if platform == 'Google Meet' and 'google.com' not in link:
            self.add_error('meeting_link', 'Please enter a valid Google Meet link (must contain google.com).')
        
        if platform == 'Zoom' and 'zoom.us' not in link:
            self.add_error('meeting_link', 'Please enter a valid Zoom link (must contain zoom.us).')

        return cleaned_data

    def save(self, commit=True):
        # 4. Save Logic: Take the link and put it into the model's 'link_or_location' field
        instance = super().save(commit=False)
        instance.link_or_location = self.cleaned_data['meeting_link']
        if commit:
            instance.save()
        return instance      