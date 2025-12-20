from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Homepage
    path('', views.dashboard, name='home'),

    # Auth
    path('register/', views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='home'), name='logout'),

    # Dashboards
    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard/client/', views.client_dashboard, name='client_dashboard'),
    path('dashboard/freelancer/', views.freelancer_dashboard, name='freelancer_dashboard'),
    
    # Placeholders
    path('post-job/', views.post_job, name='post_job'),
    path('jobs/', views.job_list, name='job_list'),
    path('jobs/<int:job_id>/', views.job_detail, name='job_detail'),
# ... inside urlpatterns ...
    path('job/<int:job_id>/applications/', views.view_applications, name='view_applications'),
    path('application/<int:application_id>/update/<str:new_status>/', views.update_application_status, name='update_status'),
    path('profile/update/', views.update_profile, name='update_profile'),   
]

