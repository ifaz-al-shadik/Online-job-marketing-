from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Client, Freelancer, JobListing, Application, Category, Interview

# Register your models here
admin.site.register(User, UserAdmin)
admin.site.register(Client)
admin.site.register(Freelancer)
admin.site.register(Category)
admin.site.register(JobListing)
admin.site.register(Application)
admin.site.register(Interview)