from django.db import models
from django.contrib.auth.models import AbstractUser

# 1. We put Category at the top so other models can use it
class Category(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class User(AbstractUser):
    is_client = models.BooleanField(default=False)
    is_freelancer = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)

    def __str__(self):
        return self.username

class Skill(models.Model):
    PROFICIENCY_CHOICES = [
        ('Beginner', 'Beginner'),
        ('Intermediate', 'Intermediate'),
        ('Expert', 'Expert'),
    ]
    name = models.CharField(max_length=100)
    proficiency_level = models.CharField(max_length=20, choices=PROFICIENCY_CHOICES)

    def __str__(self):
        return f"{self.name} ({self.proficiency_level})"

class Verification(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='verification')
    document_url = models.URLField(max_length=500, blank=True, null=True)
    is_verified = models.BooleanField(default=False)

    def __str__(self):
        return f"Verification for {self.user.username}"

class Client(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='client_profile')
    company_name = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.company_name or self.user.username

class Freelancer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='freelancer_profile')
    skills = models.ManyToManyField(Skill, blank=True)
    portfolio_url = models.URLField(blank=True)
    experience_level = models.CharField(max_length=50, blank=True)

    def __str__(self):
        return self.user.username

class JobListing(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='jobs')
    title = models.CharField(max_length=200)
    description = models.TextField()
    budget = models.DecimalField(max_digits=10, decimal_places=2)
    deadline = models.DateField()
    
    # 2. THIS IS THE FIX: Link to the Category model
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='jobs')
    
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title

class Application(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
    ]
    job = models.ForeignKey(JobListing, on_delete=models.CASCADE, related_name='applications')
    freelancer = models.ForeignKey(Freelancer, on_delete=models.CASCADE, related_name='applications')
    proposal_text = models.TextField()
    expected_payment = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"App by {self.freelancer} for {self.job}"

class Interview(models.Model):
    application = models.OneToOneField(Application, on_delete=models.CASCADE, related_name='interview')
    date_time = models.DateTimeField()
    link_or_location = models.CharField(max_length=500)
    status = models.CharField(max_length=50, default='Scheduled')

    def __str__(self):
        return f"Interview for {self.application}"