from django.test import TestCase
from django.contrib.auth import get_user_model
from .models import Client, Freelancer, JobListing, Application

User = get_user_model()

class JobMarketTests(TestCase):
    def setUp(self):
        # Create Client
        self.client_user = User.objects.create_user(username='client1', password='password', is_client=True)
        self.client_profile = Client.objects.create(user=self.client_user, company_name='Tech Corp')
        
        # Create Freelancer
        self.freelancer_user = User.objects.create_user(username='freelancer1', password='password', is_freelancer=True)
        self.freelancer_profile = Freelancer.objects.create(user=self.freelancer_user)

    def test_client_job_posting(self):
        self.client.login(username='client1', password='password')
        response = self.client.post('/post-job/', {
            'title': 'Python Developer',
            'description': 'Need a dev',
            'budget': 1000,
            'deadline': '2025-12-31',
            'category': 'IT'
        })
        self.assertEqual(response.status_code, 302) # Redirects to dashboard
        self.assertTrue(JobListing.objects.filter(title='Python Developer').exists())

    def test_freelancer_application(self):
        # Create a job first
        job = JobListing.objects.create(
            client=self.client_profile,
            title='Web Design',
            description='Design a site',
            budget=500,
            deadline='2025-12-31',
            category='Design'
        )
        
        self.client.login(username='freelancer1', password='password')
        response = self.client.post(f'/jobs/{job.id}/', {
            'proposal_text': 'I can do this',
            'expected_payment': 500
        })
        self.assertEqual(response.status_code, 302) # Redirects to dashboard
        self.assertTrue(Application.objects.filter(job=job, freelancer=self.freelancer_profile).exists())

    def test_dashboard_access(self):
        self.client.login(username='client1', password='password')
        response = self.client.get('/dashboard/')
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/dashboard/client/')
        
        self.client.login(username='freelancer1', password='password')
        response = self.client.get('/dashboard/')
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/dashboard/freelancer/')
