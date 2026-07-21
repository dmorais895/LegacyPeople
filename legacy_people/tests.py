from django.test import TestCase
from django.urls import reverse

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
