from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.db import connection
from django.utils import timezone

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
            user = form.save()
            # RAW SQL: Create Profile
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
    
    # 1. RAW SQL: Get Client Profile Data
    with connection.cursor() as cursor:
        cursor.execute("SELECT company_name, location FROM core_client WHERE id = %s", [client_id])
        rows = dictfetchall(cursor)
        profile_data = rows[0] if rows else {}

    # 2. RAW SQL: Get Interviews
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT 
                i.id, i.date_time, i.link_or_location,
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

    # 3. RAW SQL: Get Jobs WITH Pending Count
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT 
                j.*,
                (SELECT COUNT(*) FROM core_application a 
                 WHERE a.job_id = j.id AND a.status = 'Pending') AS pending_count
            FROM core_joblisting j
            WHERE j.client_id = %s 
            ORDER BY j.created_at DESC
        """, [client_id])
        jobs = dictfetchall(cursor)

    return render(request, 'dashboard/client_dashboard.html', {
        'jobs': jobs, 
        'interviews': interviews,
        'profile': profile_data
    })

@login_required
def freelancer_dashboard(request):
    if not request.user.is_freelancer:
        return redirect('home')
    
    freelancer_id = request.user.freelancer_profile.id
    
    # 1. RAW SQL: Get Freelancer Profile Data
    with connection.cursor() as cursor:
        cursor.execute("SELECT skills, portfolio_link FROM core_freelancer WHERE id = %s", [freelancer_id])
        rows = dictfetchall(cursor)
        profile_data = rows[0] if rows else {}

    # 2. RAW SQL: Get Interviews
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT 
                i.id, i.date_time, i.link_or_location,
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

    # 3. RAW SQL: Get Applications
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT 
                a.*, 
                j.title AS job_title,
                j.id AS job_id,
                c.company_name,
                u.username AS client_username
            FROM core_application a
            JOIN core_joblisting j ON a.job_id = j.id
            JOIN core_client c ON j.client_id = c.id
            JOIN core_user u ON c.user_id = u.id
            WHERE a.freelancer_id = %s
            ORDER BY a.created_at DESC
        """, [freelancer_id])
        applications = dictfetchall(cursor)

    return render(request, 'dashboard/freelancer_dashboard.html', {
        'applications': applications,
        'interviews': interviews,
        'profile': profile_data
    })

@login_required
def post_job(request):
    if not request.user.is_client:
        return redirect('home')
        
    if request.method == 'POST':
        form = JobListingForm(request.POST)
        if form.is_valid():
            d = form.cleaned_data
            client_id = request.user.client_profile.id
            
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

    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM core_category")
        categories = dictfetchall(cursor)

    sql_query = """
        SELECT 
            j.*, 
            c.company_name, 
            u.username AS client_username 
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
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT 
                j.*, 
                c.company_name, 
                c.location,
                u.username AS client_username
            FROM core_joblisting j
            LEFT JOIN core_client c ON j.client_id = c.id
            LEFT JOIN core_user u ON c.user_id = u.id
            WHERE j.id = %s
        """, [job_id])
        rows = dictfetchall(cursor)
        
    if not rows:
        return redirect('job_list')
    
    job = rows[0]

    has_applied = False
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
            return redirect('job_detail', job_id=job['id'])
            
        form = ApplicationForm(request.POST)
        if form.is_valid():
            d = form.cleaned_data
            
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
    
    if request.user.client_profile.id != job_client_id:
        return redirect('home')

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
            
            with connection.cursor() as cursor:
                if user.is_client:
                    cursor.execute("""
                        UPDATE core_client 
                        SET company_name = %s, location = %s 
                        WHERE id = %s
                    """, [d.get('company_name'), d.get('location'), profile.id])
                else:
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

# --- NEW VIEW FOR FREELANCER PUBLIC PROFILE ---
@login_required
def freelancer_public_profile(request, freelancer_id):
    if not request.user.is_client:
        return redirect('home')

    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT 
                f.id, 
                f.skills, 
                f.portfolio_link,
                u.username, 
                u.email,
                u.date_joined
            FROM core_freelancer f
            JOIN core_user u ON f.user_id = u.id
            WHERE f.id = %s
        """, [freelancer_id])
        rows = dictfetchall(cursor)

    if not rows:
        return redirect('dashboard')
    
    profile = rows[0]
    return render(request, 'dashboard/freelancer_public_profile.html', {'profile': profile})