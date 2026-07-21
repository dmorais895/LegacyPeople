from django.test import TestCase
from django.urls import reverse
from .forms import PersonForm
from .models import Person

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
            'time_lagoinha': '1 ano',
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
            'whatsapp': '1234567890', # Missing +55
            'time_lagoinha': '1 ano',
            'feeling': 1,
            'frequents_legacy': True,
        }
        form = PersonForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('whatsapp', form.errors)

class LegacyPeopleSubmissionTests(TestCase):
    def test_main_form_post_success(self):
        """Test that a valid POST request creates a Person and redirects."""
        form_data = {
            'name': 'Test User',
            'email': 'test@example.com',
            'whatsapp': '+5511999999999',
            'time_lagoinha': '1 ano',
            'feeling': 1,
            'frequents_legacy': True,
        }
        response = self.client.post(reverse('legacy_people:main_form'), data=form_data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Person.objects.count(), 1)
