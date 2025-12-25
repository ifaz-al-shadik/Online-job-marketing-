from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.db import connection
from django.utils import timezone  # Required for manual timestamps in Raw SQL

# Models are imported mainly for get_object_or_404 shortcuts in some places, 
# but we primarily use SQL now.
from .models import Client, Freelancer, JobListing, Application, Interview
from .forms import (
    CustomUserCreationForm, 
    JobListingForm, 
    ApplicationForm, 
    ClientProfileForm, 
    FreelancerProfileForm, 
    InterviewForm 
)

# --- Helper Function for Raw SQL ---
def dictfetchall(cursor):
    """Return all rows from a cursor as a dict"""
    columns = [col[0] for col in cursor.description]
    return [
        dict(zip(columns, row))
        for row in cursor.fetchall()
    ]

# --- Views ---

def home(request):
    return render(request, 'home.html')

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            # 1. Create User (We use ORM here for secure Password Hashing)
            user = form.save()
            
            # 2. RAW SQL: Create the specific Profile (Client or Freelancer)
            # We manually INSERT into the profile table linking to the new user_id
            with connection.cursor() as cursor:
                if user.is_client:
                    cursor.execute("INSERT INTO core_client (user_id) VALUES (%s)", [user.id])
                if user.is_freelancer:
                    cursor.execute("INSERT INTO core_freelancer (user_id) VALUES (%s)", [user.id])
            
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
    
    client_id = request.user.client_profile.id
    
    # 1. RAW SQL: Get Interviews (Complex JOIN)
    # Connects: Interview -> Application -> Freelancer -> User -> Job
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT 
                i.id, 
                i.date_time, 
                i.link_or_location,
                u.username AS freelancer_name,
                u.email AS freelancer_email,
                j.title AS job_title
            FROM core_interview i
            JOIN core_application a ON i.application_id = a.id
            JOIN core_freelancer f ON a.freelancer_id = f.id
            JOIN core_user u ON f.user_id = u.id
            JOIN core_joblisting j ON a.job_id = j.id
            WHERE j.client_id = %s
            ORDER BY i.date_time ASC
        """, [client_id])
        interviews = dictfetchall(cursor)

    # 2. RAW SQL: Get Jobs
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT * FROM core_joblisting 
            WHERE client_id = %s 
            ORDER BY created_at DESC
        """, [client_id])
        jobs = dictfetchall(cursor)

    return render(request, 'dashboard/client_dashboard.html', {
        'jobs': jobs, 
        'interviews': interviews
    })

@login_required
def freelancer_dashboard(request):
    if not request.user.is_freelancer:
        return redirect('home')
    
    freelancer_id = request.user.freelancer_profile.id
    
    # 1. RAW SQL: Get Interviews
    # Connects: Interview -> Application -> Job -> Client -> User
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT 
                i.id, 
                i.date_time, 
                i.link_or_location,
                j.title AS job_title,
                c.company_name,
                u.username AS client_username
            FROM core_interview i
            JOIN core_application a ON i.application_id = a.id
            JOIN core_joblisting j ON a.job_id = j.id
            JOIN core_client c ON j.client_id = c.id
            JOIN core_user u ON c.user_id = u.id
            WHERE a.freelancer_id = %s
            ORDER BY i.date_time ASC
        """, [freelancer_id])
        interviews = dictfetchall(cursor)

    # 2. RAW SQL: Get Applications
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT 
                a.*, 
                j.title AS job_title,
                j.id AS job_id
            FROM core_application a
            JOIN core_joblisting j ON a.job_id = j.id
            WHERE a.freelancer_id = %s
            ORDER BY a.created_at DESC
        """, [freelancer_id])
        applications = dictfetchall(cursor)

    return render(request, 'dashboard/freelancer_dashboard.html', {
        'applications': applications,
        'interviews': interviews
    })

@login_required
def post_job(request):
    if not request.user.is_client:
        return redirect('home')
        
    if request.method == 'POST':
        form = JobListingForm(request.POST)
        if form.is_valid():
            # Extract data
            d = form.cleaned_data
            client_id = request.user.client_profile.id
            
            # RAW SQL: Insert Job
            with connection.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO core_joblisting 
                    (title, description, budget, category_id, client_id, is_active, created_at)
                    VALUES (%s, %s, %s, %s, %s, 1, %s)
                """, [
                    d['title'], d['description'], d['budget'], 
                    d['category'].id, client_id, timezone.now()
                ])
            return redirect('client_dashboard')
    else:
        form = JobListingForm()
    return render(request, 'jobs/post_job.html', {'form': form})

def job_list(request):
    category_id = request.GET.get('category')

    # 1. RAW SQL: Fetch Categories
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM core_category")
        categories = dictfetchall(cursor)

    # 2. RAW SQL: Build Job Query with JOINs
    sql_query = """
        SELECT 
            j.*, 
            c.company_name, 
            u.username 
        FROM core_joblisting j
        LEFT JOIN core_client c ON j.client_id = c.id
        LEFT JOIN core_user u ON c.user_id = u.id
        WHERE j.is_active = 1 
    """
    params = []

    if category_id:
        sql_query += " AND j.category_id = %s"
        params.append(category_id)

    sql_query += " ORDER BY j.created_at DESC"

    with connection.cursor() as cursor:
        cursor.execute(sql_query, params)
        jobs = dictfetchall(cursor)

    context = {
        'jobs': jobs,
        'categories': categories,
    }
    return render(request, 'core/job_list.html', context)

@login_required
def job_detail(request, job_id):
    # Retrieve job (we use ORM shortcut for safety/simplicity here, but you could use SQL select)
    job = get_object_or_404(JobListing, id=job_id)
    has_applied = False
    
    # RAW SQL: Check if user already applied
    if request.user.is_freelancer:
        fid = request.user.freelancer_profile.id
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT 1 FROM core_application 
                WHERE job_id = %s AND freelancer_id = %s
            """, [job_id, fid])
            has_applied = cursor.fetchone() is not None
    
    if request.method == 'POST' and request.user.is_freelancer:
        if has_applied:
            return redirect('job_detail', job_id=job.id)
            
        form = ApplicationForm(request.POST)
        if form.is_valid():
            d = form.cleaned_data
            
            # RAW SQL: Insert Application
            with connection.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO core_application 
                    (proposal_text, expected_payment, job_id, freelancer_id, status, created_at)
                    VALUES (%s, %s, %s, %s, 'Pending', %s)
                """, [
                    d['proposal_text'], d['expected_payment'], 
                    job_id, request.user.freelancer_profile.id, timezone.now()
                ])
            return redirect('freelancer_dashboard')
    else:
        form = ApplicationForm()

    return render(request, 'jobs/job_detail.html', {'job': job, 'form': form, 'has_applied': has_applied})

@login_required
def view_applications(request, job_id):
    job = get_object_or_404(JobListing, id=job_id)
    
    if request.user.client_profile != job.client:
        return redirect('home')
        
    # RAW SQL: Fetch Applications + Freelancer Names
    # We join Freelancer -> User to get the name
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT 
                a.*, 
                u.username AS freelancer_name 
            FROM core_application a
            JOIN core_freelancer f ON a.freelancer_id = f.id
            JOIN core_user u ON f.user_id = u.id
            WHERE a.job_id = %s
        """, [job_id])
        applications = dictfetchall(cursor)

    return render(request, 'dashboard/job_applications.html', {
        'job': job, 
        'applications': applications
    })

@login_required
def update_application_status(request, application_id, new_status):
    # 1. Fetch Application ID and Job Owner ID to verify permission
    # We do this via SQL to be strict
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT a.job_id, j.client_id 
            FROM core_application a
            JOIN core_joblisting j ON a.job_id = j.id
            WHERE a.id = %s
        """, [application_id])
        result = cursor.fetchone()
        
    if not result:
        return redirect('home')
        
    job_id, job_client_id = result
    
    # Security: Ensure current user is the owner
    if request.user.client_profile.id != job_client_id:
        return redirect('home')

    # 2. RAW SQL: Update Status
    if new_status in ['Approved', 'Rejected']:
        with connection.cursor() as cursor:
            cursor.execute("""
                UPDATE core_application 
                SET status = %s 
                WHERE id = %s
            """, [new_status, application_id])

        if new_status == 'Approved':
            return redirect('schedule_interview', application_id=application_id)
            
    return redirect('view_applications', job_id=job_id)

@login_required
def schedule_interview(request, application_id):
    application = get_object_or_404(Application, id=application_id)

    if request.user.client_profile != application.job.client:
        return redirect('home')

    if request.method == 'POST':
        form = InterviewForm(request.POST)
        if form.is_valid():
            d = form.cleaned_data
            
            # RAW SQL: Insert Interview
            # Note: We use d['meeting_link'] because your cleaned_data Logic (in forms.py) 
            # might have combined platform+url, or we just grab the link field directly.
            # Assuming your form puts the final URL in 'meeting_link'.
            with connection.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO core_interview (date_time, link_or_location, application_id)
                    VALUES (%s, %s, %s)
                """, [d['date_time'], d['meeting_link'], application_id])
                
            return redirect('view_applications', job_id=application.job.id)
    else:
        form = InterviewForm()

    return render(request, 'dashboard/schedule_interview.html', {
        'form': form, 
        'application': application
    })

@login_required
def reschedule_interview(request, interview_id):
    interview = get_object_or_404(Interview, id=interview_id)

    if request.user.client_profile != interview.application.job.client:
        return redirect('home')

    if request.method == 'POST':
        form = InterviewForm(request.POST, instance=interview)
        if form.is_valid():
            d = form.cleaned_data
            
            # RAW SQL: Update Interview
            with connection.cursor() as cursor:
                cursor.execute("""
                    UPDATE core_interview 
                    SET date_time = %s, link_or_location = %s
                    WHERE id = %s
                """, [d['date_time'], d['meeting_link'], interview_id])
                
            return redirect('client_dashboard')
    else:
        form = InterviewForm(instance=interview)

    return render(request, 'dashboard/schedule_interview.html', {
        'form': form,
        'application': interview.application,
        'is_reschedule': True 
    })

@login_required
def update_profile(request):
    user = request.user
    
    # Determine role and table
    if user.is_client:
        profile = user.client_profile
        FormClass = ClientProfileForm
    elif user.is_freelancer:
        profile = user.freelancer_profile
        FormClass = FreelancerProfileForm
    else:
        return redirect('home')

    if request.method == 'POST':
        form = FormClass(request.POST, instance=profile)
        if form.is_valid():
            d = form.cleaned_data
            
            # RAW SQL: Update Profile
            # We assume standard fields. If your model has different fields, update these columns!
            with connection.cursor() as cursor:
                if user.is_client:
                    # Example columns: company_name, location
                    # Using .get() returns None if the form doesn't have that field
                    cursor.execute("""
                        UPDATE core_client 
                        SET company_name = %s, location = %s 
                        WHERE id = %s
                    """, [d.get('company_name'), d.get('location'), profile.id])
                else:
                    # Example columns: skills, portfolio_link
                    cursor.execute("""
                        UPDATE core_freelancer 
                        SET skills = %s, portfolio_link = %s 
                        WHERE id = %s
                    """, [d.get('skills'), d.get('portfolio_link'), profile.id])
            
            if user.is_client:
                return redirect('client_dashboard')
            else:
                return redirect('freelancer_dashboard')
    else:
        form = FormClass(instance=profile)

    return render(request, 'update_profile.html', {'form': form})