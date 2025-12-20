from django.contrib import admin
from .models import User, Client, Freelancer, JobListing, Application, Skill, Verification, Category, Interview

admin.site.register(User)
admin.site.register(Client)
admin.site.register(Freelancer)
admin.site.register(Skill)
admin.site.register(Verification)
admin.site.register(JobListing)
admin.site.register(Application)
admin.site.register(Interview)

# IMPORTANT: This line makes the Category table visible!
admin.site.register(Category)