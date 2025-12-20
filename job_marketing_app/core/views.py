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
@login_required
def view_applications(request, job_id):
    job = get_object_or_404(JobListing, id=job_id)
    
    # Security: Ensure only the owner of the job can see applications
    if request.user.client_profile != job.client:
        return redirect('home')
        
    applications = Application.objects.filter(job=job)
    return render(request, 'dashboard/job_applications.html', {
        'job': job, 
        'applications': applications
    })

@login_required
@login_required
def update_application_status(request, application_id, new_status):
    application = get_object_or_404(Application, id=application_id)
    
    # Security: Ensure the person clicking is the job owner
    # Note: We use .client_profile because of your related_name
    if request.user.client_profile != application.job.client:
        return redirect('home')

    # FIX: We accept 'Approved' and 'Rejected' (Title Case)
    # We also print to the terminal so you can see if it works
    print(f"DEBUG: Attempting to change status to {new_status}")
    
    if new_status in ['Approved', 'Rejected']:
        application.status = new_status
        application.save()
        print("DEBUG: Saved successfully!")
    else:
        print("DEBUG: Failed! Status mismatch.")
        
    # Go back to the list
    return redirect('view_applications', job_id=application.job.id)
from .forms import ClientProfileForm, FreelancerProfileForm # Import the new forms

@login_required
def update_profile(request):
    user = request.user
    
    # 1. Determine which role the user has
    if user.is_client:
        profile = user.client_profile
        FormClass = ClientProfileForm
    elif user.is_freelancer:
        profile = user.freelancer_profile
        FormClass = FreelancerProfileForm
    else:
        return redirect('home')

    # 2. Handle the Save Action
    if request.method == 'POST':
        form = FormClass(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            # Redirect to the correct dashboard
            if user.is_client:
                return redirect('client_dashboard')
            else:
                return redirect('freelancer_dashboard')
    else:
        # 3. Pre-fill the form with existing data
        form = FormClass(instance=profile)

    return render(request, 'update_profile.html', {'form': form})