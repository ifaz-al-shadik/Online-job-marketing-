from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    is_client = models.BooleanField(default=False)
    is_freelancer = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)

class Client(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='client_profile')
    # New fields for Profile Update
    company_name = models.CharField(max_length=255, blank=True, null=True)
    location = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.company_name or self.user.username

class Freelancer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='freelancer_profile')
    # New fields for Profile Update
    skills = models.TextField(blank=True, null=True)
    portfolio_link = models.URLField(blank=True, null=True)

    def __str__(self):
        return self.user.username

class Category(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class JobListing(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='jobs')
    title = models.CharField(max_length=200)
    description = models.TextField()
    budget = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class Application(models.Model):
    job = models.ForeignKey(JobListing, on_delete=models.CASCADE, related_name='applications')
    freelancer = models.ForeignKey(Freelancer, on_delete=models.CASCADE, related_name='applications')
    proposal_text = models.TextField()
    expected_payment = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, default='Pending') # Pending, Approved, Rejected
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.freelancer} applied for {self.job}"

class Interview(models.Model):
    application = models.OneToOneField(Application, on_delete=models.CASCADE, related_name='interview')
    date_time = models.DateTimeField()
    # Stores either a link (https://zoom.us...) or a location (Office Room 4)
    link_or_location = models.CharField(max_length=500)
    
    def __str__(self):
        return f"Interview for {self.application.job.title}"