from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, JobListing, Application

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
            'deadline': forms.DateInput(attrs={'type': 'date'}),
        }

class ApplicationForm(forms.ModelForm):
    class Meta:
        model = Application
        fields = ['proposal_text', 'expected_payment']
