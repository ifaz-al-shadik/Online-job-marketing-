from django.contrib import admin
from .models import User, Skill, Verification, Client, Freelancer, JobListing, Application, Interview

admin.site.register(User)
admin.site.register(Skill)
admin.site.register(Verification)
admin.site.register(Client)
admin.site.register(Freelancer)
admin.site.register(JobListing)
admin.site.register(Application)
admin.site.register(Interview)
