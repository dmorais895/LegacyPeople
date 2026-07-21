from django.shortcuts import render

def landing_page(request):
    """View for the landing page."""
    return render(request, 'legacy_people/landing.html')

def main_form(request):
    """View for the main form."""
    return render(request, 'legacy_people/main_form.html')
