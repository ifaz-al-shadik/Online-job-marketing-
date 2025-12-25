from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Homepage (Redirects to dashboard if logged in)
    path('', views.dashboard, name='home'),

    # Auth
    path('register/', views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='home'), name='logout'),

    # Dashboards
    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard/client/', views.client_dashboard, name='client_dashboard'),
    path('dashboard/freelancer/', views.freelancer_dashboard, name='freelancer_dashboard'),
    path('profile/update/', views.update_profile, name='update_profile'),

    # Job Listings
    path('post-job/', views.post_job, name='post_job'),
    path('jobs/', views.job_list, name='job_list'),
    path('jobs/<int:job_id>/', views.job_detail, name='job_detail'),

    # Application Management
    path('job/<int:job_id>/applications/', views.view_applications, name='view_applications'),
    
    # FIX: Renamed 'update_status' to 'update_application_status' to match your template
    path('application/<int:application_id>/update/<str:new_status>/', views.update_application_status, name='update_application_status'),

    # NEW: The Schedule Interview Page
    path('application/<int:application_id>/schedule/', views.schedule_interview, name='schedule_interview'),
    path('interview/<int:interview_id>/reschedule/', views.reschedule_interview, name='reschedule_interview'),
]