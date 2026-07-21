from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.cache import cache
from .forms import PersonForm
from .models import Person

User = get_user_model()

class LegacyPeopleViewTests(TestCase):
    def test_landing_page_status_code(self):
        """Test that the landing page returns a 200 OK status."""
        response = self.client.get(reverse('legacy_people:landing'))
        self.assertEqual(response.status_code, 200)

    def test_landing_page_uses_correct_template(self):
        """Test that the landing page uses the landing.html template."""
        response = self.client.get(reverse('legacy_people:landing'))
        self.assertTemplateUsed(response, 'legacy_people/landing.html')
        self.assertTemplateUsed(response, 'legacy_people/base.html')

    def test_landing_page_contains_link_to_form(self):
        """Test that the landing page contains a link to the main form."""
        response = self.client.get(reverse('legacy_people:landing'))
        form_url = reverse('legacy_people:main_form')
        self.assertContains(response, form_url)

    def test_footer_renders_social_links_and_schedule(self):
        """Test that the footer contains Instagram, YouTube links and service schedules."""
        response = self.client.get(reverse('legacy_people:landing'))
        self.assertContains(response, 'https://www.instagram.com/legacynatal.zn/')
        self.assertContains(response, 'https://www.youtube.com/@Lagoinha-ZonaNorte')
        self.assertContains(response, '18h30: Legacy Pray')
        self.assertContains(response, '19h30: Culto Legacy')
        self.assertContains(response, 'bi-instagram')
        self.assertContains(response, 'bi-youtube')

    def test_main_form_status_code(self):
        """Test that the main form page returns a 200 OK status."""
        response = self.client.get(reverse('legacy_people:main_form'))
        self.assertEqual(response.status_code, 200)

    def test_main_form_uses_correct_template(self):
        """Test that the main form uses the main_form.html template."""
        response = self.client.get(reverse('legacy_people:main_form'))
        self.assertTemplateUsed(response, 'legacy_people/main_form.html')
        self.assertTemplateUsed(response, 'legacy_people/base.html')

    def test_main_form_contains_csrf_token(self):
        """Test that the main form contains a CSRF token for security."""
        response = self.client.get(reverse('legacy_people:main_form'))
        self.assertContains(response, 'csrfmiddlewaretoken')

    def test_responsiveness_classes_in_templates(self):
        """Test that Bootstrap responsive classes are used in the templates."""
        response_landing = self.client.get(reverse('legacy_people:landing'))
        self.assertContains(response_landing, 'col-md-')

        response_form = self.client.get(reverse('legacy_people:main_form'))
        self.assertContains(response_form, 'col-md-')
        self.assertContains(response_form, 'col-lg-')

class LegacyPeopleFormTests(TestCase):
    def test_whatsapp_validation_valid(self):
        """Test that a valid whatsapp number passes validation."""
        form_data = {
            'name': 'Test User',
            'email': 'test@example.com',
            'whatsapp': '+55 (11) 99999-9999',
            'time_lagoinha': 'menos_6_meses',
            'feeling': 1,
            'frequents_legacy': True,
        }
        form = PersonForm(data=form_data)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['whatsapp'], '+5511999999999')

    def test_whatsapp_validation_invalid(self):
        """Test that an invalid whatsapp number fails validation."""
        form_data = {
            'name': 'Test User',
            'email': 'test@example.com',
            'whatsapp': '1234567890',
            'time_lagoinha': 'menos_6_meses',
            'feeling': 1,
            'frequents_legacy': True,
        }
        form = PersonForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('whatsapp', form.errors)

    def test_xss_sanitization_in_form_fields(self):
        """Test that HTML/script tags are stripped from input fields to prevent XSS."""
        form_data = {
            'name': '<script>alert("xss")</script> Test User',
            'email': 'TEST@EXAMPLE.COM',
            'whatsapp': '+5511999999999',
            'time_lagoinha': 'menos_6_meses',
            'feeling': 1,
            'prayer_request': '<b>Abençoe</b> <img src=x onerror=alert(1)>',
            'frequents_legacy': True,
        }
        form = PersonForm(data=form_data)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['name'], 'alert("xss") Test User')
        self.assertEqual(form.cleaned_data['email'], 'test@example.com')
        self.assertEqual(form.cleaned_data['prayer_request'], 'Abençoe')

    def test_excessive_length_validation(self):
        """Test that prayer requests exceeding 2000 characters fail validation to prevent DoS."""
        form_data = {
            'name': 'Test User',
            'email': 'test@example.com',
            'whatsapp': '+5511999999999',
            'time_lagoinha': 'menos_6_meses',
            'feeling': 1,
            'prayer_request': 'a' * 2001,
            'frequents_legacy': True,
        }
        form = PersonForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('prayer_request', form.errors)

    def test_conditional_dependency_cleanup(self):
        """Test that orphan data is cleared when conditional fields are false."""
        form_data = {
            'name': 'Test User',
            'email': 'test@example.com',
            'whatsapp': '+5511999999999',
            'has_gc': False,
            'gc_name': 'Tampered GC Name',
            'time_lagoinha': 'menos_6_meses',
            'feeling': 1,
            'frequents_legacy': True,
            'legacy_reason': 'Tampered Reason',
        }
        form = PersonForm(data=form_data)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['gc_name'], '')
        self.assertEqual(form.cleaned_data['legacy_reason'], '')

class LegacyPeopleSubmissionTests(TestCase):
    def test_main_form_post_success(self):
        """Test that a valid POST request creates a Person and redirects."""
        form_data = {
            'name': 'Test User',
            'email': 'test@example.com',
            'whatsapp': '+5511999999999',
            'time_lagoinha': 'menos_6_meses',
            'feeling': 1,
            'frequents_legacy': True,
        }
        response = self.client.post(reverse('legacy_people:main_form'), data=form_data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Person.objects.count(), 1)

class LegacyPeopleAuthAndDashboardTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testadmin', password='password123')
        self.p1 = Person.objects.create(
            name='Person 1', email='p1@ex.com', whatsapp='+5511999991111',
            has_gc=False, time_lagoinha='menos_6_meses', feeling=1, wants_chat=True
        )
        self.p2 = Person.objects.create(
            name='Person 2', email='p2@ex.com', whatsapp='+5511999992222',
            has_gc=True, gc_name='GC 1', time_lagoinha='1_3_anos', feeling=5, wants_chat=False
        )

    def test_person_whatsapp_clean_property(self):
        """Test that whatsapp_clean property returns digits only."""
        self.assertEqual(self.p1.whatsapp_clean, '5511999991111')

    def test_dashboard_requires_login(self):
        """Test that dashboard redirects unauthenticated users to login."""
        response = self.client.get(reverse('legacy_people:dashboard'))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('legacy_people:login'), response.url)

    def test_login_page_renders(self):
        """Test that login page returns 200 OK."""
        response = self.client.get(reverse('legacy_people:login'))
        self.assertEqual(response.status_code, 200)

    def test_login_success_redirects_to_dashboard(self):
        """Test that logging in with valid credentials redirects to dashboard."""
        response = self.client.post(reverse('legacy_people:login'), {
            'username': 'testadmin',
            'password': 'password123'
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('legacy_people:dashboard'))

    def test_dashboard_displays_correct_metrics(self):
        """Test that dashboard calculates metrics correctly."""
        self.client.login(username='testadmin', password='password123')
        response = self.client.get(reverse('legacy_people:dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['total_people'], 2)
        self.assertEqual(response.context['no_gc_count'], 1)
        self.assertEqual(response.context['wants_chat_count'], 1)
        self.assertEqual(response.context['feelings_distribution'][1], 1)
        self.assertEqual(response.context['feelings_distribution'][5], 1)

    def test_dashboard_no_gc_count_color_coding(self):
        """Test dynamic color coding for Sem Grupo de Crescimento stat card."""
        self.client.login(username='testadmin', password='password123')

        # Test no_gc_count == 1 (1-4 -> text-warning)
        response_warning = self.client.get(reverse('legacy_people:dashboard'))
        self.assertContains(response_warning, 'text-warning')

        # Test no_gc_count == 0 (0 -> text-success)
        Person.objects.filter(has_gc=False).update(has_gc=True)
        response_success = self.client.get(reverse('legacy_people:dashboard'))
        self.assertContains(response_success, 'text-success')

        # Test no_gc_count >= 5 (5+ -> text-danger)
        for i in range(10, 16):
            Person.objects.create(
                name=f"No GC User {i}", email=f"nogc{i}@ex.com", whatsapp=f"+551199999{i:04d}",
                has_gc=False, time_lagoinha="menos_6_meses", feeling=1
            )
        response_danger = self.client.get(reverse('legacy_people:dashboard'))
        self.assertContains(response_danger, 'text-danger')

    def test_dashboard_feeling_filter(self):
        """Test filtering dashboard people list by feeling."""
        self.client.login(username='testadmin', password='password123')
        response = self.client.get(reverse('legacy_people:dashboard') + '?feeling=1')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['selected_feeling'], 1)
        self.assertEqual(len(response.context['people_list']), 1)
        self.assertEqual(response.context['people_list'][0].name, 'Person 1')

    def test_dashboard_renders_profile_cards_and_whatsapp_api_link(self):
        """Test that profile cards are rendered with direct wa.me WhatsApp links."""
        self.client.login(username='testadmin', password='password123')
        response = self.client.get(reverse('legacy_people:dashboard'))
        self.assertContains(response, 'https://wa.me/5511999991111')
        self.assertContains(response, 'https://wa.me/5511999992222')
        self.assertContains(response, 'bi-whatsapp')

    def test_dashboard_prayer_requests_pagination(self):
        """Test that prayer requests are paginated max 10 per page."""
        for i in range(1, 16):
            Person.objects.create(
                name=f"Prayer User {i}",
                email=f"pu{i}@ex.com",
                whatsapp=f"+551199999{i:04d}",
                time_lagoinha="menos_6_meses",
                feeling=1,
                prayer_request=f"Pedido {i}"
            )

        self.client.login(username='testadmin', password='password123')

        response_page1 = self.client.get(reverse('legacy_people:dashboard') + '?page=1')
        self.assertEqual(response_page1.status_code, 200)
        self.assertEqual(len(response_page1.context['prayers_page']), 10)

        response_page2 = self.client.get(reverse('legacy_people:dashboard') + '?page=2')
        self.assertEqual(response_page2.status_code, 200)
        self.assertEqual(len(response_page2.context['prayers_page']), 5)

    def test_dashboard_prayer_requests_ajax_pagination(self):
        """Test that AJAX request for prayer requests pagination returns JsonResponse without full page reload."""
        for i in range(1, 16):
            Person.objects.create(
                name=f"Prayer User {i}",
                email=f"pu{i}@ex.com",
                whatsapp=f"+551199999{i:04d}",
                time_lagoinha="menos_6_meses",
                feeling=1,
                prayer_request=f"Pedido {i}"
            )

        self.client.login(username='testadmin', password='password123')

        response = self.client.get(reverse('legacy_people:dashboard') + '?page=2&ajax=1')
        self.assertEqual(response.status_code, 200)
        json_data = response.json()
        self.assertEqual(json_data['page'], 2)
        self.assertEqual(json_data['num_pages'], 2)
        self.assertEqual(len(json_data['prayers']), 5)

    def test_dashboard_feeling_ajax_filter(self):
        """Test that feeling_ajax=1 returns JsonResponse with filtered people list."""
        self.client.login(username='testadmin', password='password123')
        response = self.client.get(reverse('legacy_people:dashboard') + '?feeling_ajax=1&feeling=1')
        self.assertEqual(response.status_code, 200)
        json_data = response.json()
        self.assertEqual(json_data['selected_feeling'], 1)
        self.assertEqual(len(json_data['people']), 1)
        self.assertEqual(json_data['people'][0]['name'], 'Person 1')


class LoginRateLimitTests(TestCase):
    """Tests for brute-force / rate-limit protection on the login view."""

    def setUp(self):
        cache.clear()
        self.login_url = reverse('legacy_people:login')
        self.user = User.objects.create_user(username='admin', password='correctpass')

    def _post_bad_login(self, n=1):
        """Submit n failed login attempts."""
        for _ in range(n):
            self.client.post(
                self.login_url,
                {'username': 'admin', 'password': 'wrongpassword'},
                REMOTE_ADDR='10.0.0.1',
            )

    def test_failed_attempts_show_remaining_count(self):
        """After a failed login, the response should mention remaining attempts."""
        response = self.client.post(
            self.login_url,
            {'username': 'admin', 'password': 'bad'},
            REMOTE_ADDR='10.0.0.1',
        )
        self.assertContains(response, 'Tentativas restantes')

    def test_lockout_after_max_attempts(self):
        """After MAX_LOGIN_ATTEMPTS failures, the IP is locked out."""
        self._post_bad_login(n=5)
        response = self.client.get(self.login_url, REMOTE_ADDR='10.0.0.1')
        self.assertContains(response, 'Bloqueado')

    def test_locked_out_ip_cannot_submit_form(self):
        """A locked-out IP posting correct credentials is still rejected."""
        self._post_bad_login(n=5)
        response = self.client.post(
            self.login_url,
            {'username': 'admin', 'password': 'correctpass'},
            REMOTE_ADDR='10.0.0.1',
        )
        self.assertContains(response, 'Bloqueado')
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_different_ips_have_independent_counters(self):
        """Failed attempts on one IP should not affect another IP."""
        self._post_bad_login(n=5)  # Lock 10.0.0.1
        response = self.client.get(self.login_url, REMOTE_ADDR='10.0.0.2')
        self.assertNotContains(response, 'Bloqueado')

    def test_successful_login_clears_failed_attempts(self):
        """A successful login resets the failed-attempt counter for the IP."""
        self._post_bad_login(n=3)
        self.client.post(
            self.login_url,
            {'username': 'admin', 'password': 'correctpass'},
            REMOTE_ADDR='10.0.0.1',
        )
        # Logout so the login view is rendered on next request
        self.client.logout()
        # After successful login, further bad attempts should start from 0 again
        response = self.client.post(
            self.login_url,
            {'username': 'admin', 'password': 'bad'},
            REMOTE_ADDR='10.0.0.1',
        )
        self.assertContains(response, 'Tentativas restantes: 4')
