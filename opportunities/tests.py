from django.contrib.auth.models import User
from django.test import Client
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Department, Opportunity, UserProfile


class OpportunityAPITests(APITestCase):
    def setUp(self):
        self.department = Department.objects.create(name='Computer Science', code='CS')
        self.other_department = Department.objects.create(name='Biology', code='BIO')
        self.user = User.objects.create_user(username='faculty', password='test-password')
        self.profile = UserProfile.objects.create(
            user=self.user,
            role=UserProfile.TEACHER,
            department=self.department,
            position_title='Assistant Professor',
        )
        self.client.force_authenticate(user=self.user)
        self.opportunity = Opportunity.objects.create(
            title='AI Research Assistant',
            description='Build an AI-powered research assistant.',
            research_area='Artificial Intelligence',
            faculty_name='Dr. Ahmed',
            department='Computer Science',
            required_skills='Python, Machine Learning',
            available_positions=2,
            application_deadline='2026-11-30',
            status='Open',
            owner=self.user,
        )

    def test_list_opportunities(self):
        url = reverse('opportunity-list-create')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)

    def test_list_is_public(self):
        self.client.force_authenticate(user=None)
        response = self.client.get(reverse('opportunity-list-create'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_opportunity(self):
        url = reverse('opportunity-list-create')
        payload = {
            'title': 'Robotics Lab',
            'description': 'Robotics research project focusing on automation.',
            'research_area': 'Robotics',
            'faculty_name': 'Dr. Patel',
            'department': 'Computer Science',
            'required_skills': 'C++, ROS, Sensors',
            'available_positions': 3,
            'application_deadline': '2026-12-10',
            'status': 'Open',
        }
        response = self.client.post(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        created = Opportunity.objects.get(title='Robotics Lab')
        self.assertEqual(created.owner, self.user)
        self.assertEqual(created.faculty_name, self.user.username)
        self.assertEqual(created.department_record, self.department)

    def test_update_opportunity(self):
        url = reverse('opportunity-detail', args=[self.opportunity.id])
        payload = {
            'title': 'Updated AI Research Assistant',
            'description': 'Updated description.',
            'research_area': 'Artificial Intelligence',
            'faculty_name': 'Dr. Ahmed',
            'department': 'Computer Science',
            'required_skills': 'Python, Deep Learning',
            'available_positions': 1,
            'application_deadline': '2026-12-15',
            'status': 'Closed',
        }
        response = self.client.put(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.opportunity.refresh_from_db()
        self.assertEqual(self.opportunity.status, 'Closed')

    def test_delete_opportunity(self):
        url = reverse('opportunity-detail', args=[self.opportunity.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Opportunity.objects.filter(id=self.opportunity.id).exists())
        missing = self.client.get(url)
        self.assertEqual(missing.status_code, status.HTTP_404_NOT_FOUND)

    def test_write_requires_authentication(self):
        self.client.force_authenticate(user=None)
        payload = {'title': 'Unauthorised'}
        response = self.client.post(reverse('opportunity-list-create'), payload, format='json')
        self.assertIn(response.status_code, {
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        })

    def test_open_opportunity_cannot_have_past_deadline(self):
        response = self.client.post(reverse('opportunity-list-create'), {
            'title': 'Past deadline',
            'description': 'Example project',
            'research_area': 'AI',
            'faculty_name': 'Dr. Smith',
            'department': 'Computer Science',
            'required_skills': 'Python',
            'available_positions': 1,
            'application_deadline': '2020-01-01',
            'status': 'Open',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('application_deadline', response.data)

    def test_filter_and_search_opportunities(self):
        response = self.client.get(
            reverse('opportunity-list-create'),
            {'status': 'Open', 'search': 'AI Research'},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['id'], self.opportunity.id)

    def test_teacher_cannot_modify_another_teachers_opportunity(self):
        other_teacher = User.objects.create_user(username='other-faculty', password='test-password')
        UserProfile.objects.create(
            user=other_teacher,
            role=UserProfile.TEACHER,
            department=self.department,
        )
        self.opportunity.owner = other_teacher
        self.opportunity.save()
        response = self.client.delete(reverse('opportunity-detail', args=[self.opportunity.id]))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Opportunity.objects.filter(id=self.opportunity.id).exists())

    def test_teacher_cannot_create_for_another_department(self):
        response = self.client.post(reverse('opportunity-list-create'), {
            'title': 'Biology study',
            'description': 'Research in biology.',
            'research_area': 'Biology',
            'faculty_name': 'Ignored client value',
            'department': 'Biology',
            'required_skills': 'Microscopy',
            'available_positions': 1,
            'application_deadline': '2026-12-10',
            'status': 'Open',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('department', response.data)

    def test_student_can_read_but_cannot_write_opportunities(self):
        student = User.objects.create_user(username='student', password='test-password')
        UserProfile.objects.create(
            user=student,
            role=UserProfile.STUDENT,
            department=self.department,
            student_number='S123',
        )
        self.client.force_authenticate(user=student)
        self.assertEqual(
            self.client.get(reverse('opportunity-list-create')).status_code,
            status.HTTP_200_OK,
        )
        response = self.client.post(reverse('opportunity-list-create'), {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_manage_any_department_opportunity(self):
        admin = User.objects.create_superuser(
            username='admin',
            email='admin@example.test',
            password='admin-password',
        )
        self.client.force_authenticate(user=admin)
        self.opportunity.owner = self.user
        self.opportunity.save()
        response = self.client.delete(reverse('opportunity-detail', args=[self.opportunity.id]))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_registration_creates_student_account_and_profile(self):
        response = self.client.post(reverse('register'), {
            'username': 'new-student',
            'email': 'student@example.test',
            'first_name': 'New',
            'last_name': 'Student',
            'role': 'student',
            'department': str(self.department.id),
            'phone': '',
            'student_number': 'S-901',
            'program': 'Physics',
            'position_title': '',
            'password1': 'Complex-pass-2026!',
            'password2': 'Complex-pass-2026!',
        })
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        registered = User.objects.get(username='new-student')
        self.assertEqual(registered.profile.role, UserProfile.STUDENT)
        self.assertEqual(registered.profile.student_number, 'S-901')

    def test_registration_creates_teacher_account_with_department(self):
        response = self.client.post(reverse('register'), {
            'username': 'new-teacher',
            'email': 'teacher@example.test',
            'first_name': 'New',
            'last_name': 'Teacher',
            'role': 'teacher',
            'department': str(self.department.id),
            'phone': '',
            'student_number': '',
            'program': '',
            'position_title': 'Lecturer',
            'password1': 'Complex-pass-2026!',
            'password2': 'Complex-pass-2026!',
        })
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        registered = User.objects.get(username='new-teacher')
        self.assertEqual(registered.profile.role, UserProfile.TEACHER)
        self.assertEqual(registered.profile.department, self.department)

    def test_registration_rejects_student_without_student_number(self):
        self.client.logout()
        response = self.client.post(reverse('register'), {
            'username': 'missing-student-id',
            'email': 'missing-id@example.test',
            'first_name': 'Missing',
            'last_name': 'ID',
            'role': 'student',
            'department': str(self.department.id),
            'student_number': '',
            'password1': 'Complex-pass-2026!',
            'password2': 'Complex-pass-2026!',
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertContains(response, 'Students must enter their student ID.')
        self.assertFalse(User.objects.filter(username='missing-student-id').exists())

    def test_registration_rejects_teacher_without_department(self):
        self.client.logout()
        response = self.client.post(reverse('register'), {
            'username': 'missing-teacher-dept',
            'email': 'missing-dept@example.test',
            'first_name': 'Missing',
            'last_name': 'Department',
            'role': 'teacher',
            'department': '',
            'student_number': '',
            'password1': 'Complex-pass-2026!',
            'password2': 'Complex-pass-2026!',
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertContains(response, 'Teachers must select their department.')
        self.assertFalse(User.objects.filter(username='missing-teacher-dept').exists())

    def test_registration_rejects_mismatched_passwords(self):
        self.client.logout()
        response = self.client.post(reverse('register'), {
            'username': 'password-mismatch',
            'email': 'mismatch@example.test',
            'first_name': 'Password',
            'last_name': 'Mismatch',
            'role': 'student',
            'department': str(self.department.id),
            'student_number': 'S-902',
            'password1': 'Complex-pass-2026!',
            'password2': 'Different-pass-2026!',
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertContains(response, "The two password fields didn’t match.")
        self.assertFalse(User.objects.filter(username='password-mismatch').exists())

    def test_profile_api_updates_user_details(self):
        response = self.client.patch(reverse('profile-api'), {
            'first_name': 'Updated',
            'position_title': 'Professor',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.profile.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Updated')
        self.assertEqual(self.profile.position_title, 'Professor')

    def test_session_api_writes_require_and_accept_csrf_token(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.user)
        client.get(reverse('opportunity-list-page'))
        csrf_token = client.cookies['csrftoken'].value
        response = client.post(
            reverse('opportunity-list-create'),
            data={
                'title': 'CSRF tested opportunity',
                'description': 'A browser session test.',
                'research_area': 'Computer Science',
                'department': 'Computer Science',
                'required_skills': 'Python',
                'available_positions': 1,
                'application_deadline': '2026-12-30',
                'status': 'Open',
            },
            content_type='application/json',
            HTTP_X_CSRFTOKEN=csrf_token,
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_department_list_is_public(self):
        self.client.force_authenticate(user=None)
        response = self.client.get(reverse('department-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)
        self.assertEqual(response.data['results'][0]['name'], 'Biology')

    def test_portal_and_role_pages_render(self):
        self.client.logout()
        landing_page = self.client.get(reverse('frontend-home'))
        self.assertEqual(landing_page.status_code, status.HTTP_200_OK)
        self.assertContains(landing_page, 'Sign in to continue')
        self.assertEqual(self.client.get(reverse('login')).status_code, status.HTTP_200_OK)
        self.assertEqual(self.client.get(reverse('opportunity-list-page')).status_code, status.HTTP_200_OK)
        self.assertEqual(self.client.get(reverse('register')).status_code, status.HTTP_200_OK)
        self.client.force_login(self.user)
        self.assertRedirects(
            self.client.get(reverse('frontend-home')),
            reverse('dashboard'),
        )
        self.assertEqual(self.client.get(reverse('dashboard')).status_code, status.HTTP_200_OK)
        self.assertEqual(self.client.get(reverse('profile')).status_code, status.HTTP_200_OK)
        self.assertEqual(
            self.client.get(reverse('opportunity-page', args=[self.opportunity.id])).status_code,
            status.HTTP_200_OK,
        )

    def test_admin_dashboard_requires_staff(self):
        self.client.force_login(self.user)
        self.assertEqual(
            self.client.get(reverse('admin-dashboard')).status_code,
            status.HTTP_302_FOUND,
        )
        admin = User.objects.create_superuser(
            username='admin-dashboard-user',
            email='admin-dashboard@example.test',
            password='admin-password',
        )
        self.client.force_login(admin)
        self.assertEqual(self.client.get(reverse('admin-dashboard')).status_code, status.HTTP_200_OK)

    def test_login_rejects_wrong_username_or_password_with_visible_error(self):
        self.client.logout()
        for credentials in (
            {'username': 'unknown-user', 'password': 'test-password'},
            {'username': self.user.username, 'password': 'wrong-password'},
        ):
            response = self.client.post(reverse('frontend-home'), credentials)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertContains(response, 'Please enter a correct username and password')

    def test_login_requires_both_fields(self):
        self.client.logout()
        for credentials in (
            {'username': '', 'password': 'test-password'},
            {'username': self.user.username, 'password': ''},
            {'username': '', 'password': ''},
        ):
            response = self.client.post(reverse('login'), credentials)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertContains(response, 'This field is required.')

    def test_inactive_account_cannot_login(self):
        self.client.logout()
        self.user.is_active = False
        self.user.save()
        response = self.client.post(reverse('login'), {
            'username': self.user.username,
            'password': 'test-password',
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertContains(response, 'Please enter a correct username and password')

    def test_login_rejects_external_next_redirect(self):
        self.client.logout()
        response = self.client.post(reverse('login'), {
            'username': self.user.username,
            'password': 'test-password',
            'next': 'https://attacker.example/',
        })
        self.assertRedirects(response, reverse('dashboard'))

    def test_successful_login_routes_to_dashboard(self):
        self.client.logout()
        response = self.client.post(reverse('login'), {
            'username': self.user.username,
            'password': 'test-password',
        })
        self.assertRedirects(response, reverse('dashboard'))
        self.assertEqual(self.client.get(reverse('dashboard')).status_code, status.HTTP_200_OK)

    def test_student_login_opens_student_dashboard(self):
        student = User.objects.create_user(
            username='login-student',
            password='test-password',
        )
        UserProfile.objects.create(
            user=student,
            role=UserProfile.STUDENT,
            department=self.department,
            student_number='S-LOGIN',
        )
        self.client.logout()
        response = self.client.post(reverse('login'), {
            'username': 'login-student',
            'password': 'test-password',
        })
        self.assertRedirects(response, reverse('dashboard'))
        dashboard_response = self.client.get(reverse('dashboard'))
        self.assertContains(dashboard_response, 'Student Dashboard')

    def test_admin_login_opens_admin_dashboard_without_regular_profile(self):
        admin = User.objects.create_superuser(
            username='login-admin',
            email='login-admin@example.test',
            password='test-password',
        )
        self.client.logout()
        response = self.client.post(reverse('login'), {
            'username': admin.username,
            'password': 'test-password',
        })
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertEqual(response['Location'], reverse('admin-dashboard'))
        self.assertEqual(
            self.client.get(reverse('admin-dashboard')).status_code,
            status.HTTP_200_OK,
        )

    def test_logout_requires_post_and_back_navigation_requires_login(self):
        self.client.force_login(self.user)
        dashboard_response = self.client.get(reverse('dashboard'))
        self.assertEqual(dashboard_response.status_code, status.HTTP_200_OK)
        self.assertIn('no-store', dashboard_response['Cache-Control'])

        get_logout = self.client.get(reverse('logout'))
        self.assertEqual(get_logout.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        logout_response = self.client.post(reverse('logout'))
        self.assertRedirects(logout_response, reverse('frontend-home'))
        self.assertIn('no-store', logout_response['Cache-Control'])

        back_navigation_response = self.client.get(reverse('dashboard'))
        self.assertEqual(back_navigation_response.status_code, status.HTTP_302_FOUND)
        self.assertIn('/login/', back_navigation_response['Location'])

    def test_anonymous_profile_and_admin_dashboard_require_login(self):
        self.client.logout()
        for url in (reverse('dashboard'), reverse('profile'), reverse('admin-dashboard')):
            response = self.client.get(url)
            self.assertEqual(response.status_code, status.HTTP_302_FOUND)
            self.assertIn('/login/', response['Location'])
