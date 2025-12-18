from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from .forms import CustomUserCreationForm, JobListingForm, ApplicationForm
from .models import Client, Freelancer, JobListing, Application

def home(request):
    return render(request, 'home.html')

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            if user.is_client:
                Client.objects.create(user=user)
            if user.is_freelancer:
                Freelancer.objects.create(user=user)
            login(request, user)
            return redirect('dashboard')
    else:
        form = CustomUserCreationForm()
    return render(request, 'registration/register.html', {'form': form})

@login_required
def dashboard(request):
    if request.user.is_client:
        return redirect('client_dashboard')
    elif request.user.is_freelancer:
        return redirect('freelancer_dashboard')
    elif request.user.is_admin:
        return redirect('/admin/')
    return redirect('home')

@login_required
def client_dashboard(request):
    if not request.user.is_client:
        return redirect('home')
    client = request.user.client_profile
    jobs = JobListing.objects.filter(client=client)
    return render(request, 'dashboard/client_dashboard.html', {'jobs': jobs})

@login_required
def freelancer_dashboard(request):
    if not request.user.is_freelancer:
        return redirect('home')
    freelancer = request.user.freelancer_profile
    applications = Application.objects.filter(freelancer=freelancer)
    return render(request, 'dashboard/freelancer_dashboard.html', {'applications': applications})

@login_required
def post_job(request):
    if not request.user.is_client:
        return redirect('home')
    if request.method == 'POST':
        form = JobListingForm(request.POST)
        if form.is_valid():
            job = form.save(commit=False)
            job.client = request.user.client_profile
            job.save()
            return redirect('client_dashboard')
    else:
        form = JobListingForm()
    return render(request, 'jobs/post_job.html', {'form': form})

def job_list(request):
    jobs = JobListing.objects.filter(is_active=True)
    return render(request, 'jobs/job_list.html', {'jobs': jobs})

@login_required
def job_detail(request, job_id):
    job = get_object_or_404(JobListing, id=job_id)
    has_applied = False
    if request.user.is_freelancer:
        has_applied = Application.objects.filter(job=job, freelancer=request.user.freelancer_profile).exists()
    
    if request.method == 'POST' and request.user.is_freelancer:
        if has_applied:
            return redirect('job_detail', job_id=job.id)
        form = ApplicationForm(request.POST)
        if form.is_valid():
            application = form.save(commit=False)
            application.job = job
            application.freelancer = request.user.freelancer_profile
            application.save()
            return redirect('freelancer_dashboard')
    else:
        form = ApplicationForm()

    return render(request, 'jobs/job_detail.html', {'job': job, 'form': form, 'has_applied': has_applied})
