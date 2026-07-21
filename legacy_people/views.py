from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import PersonForm

def landing_page(request):
    """View for the landing page."""
    return render(request, 'legacy_people/landing.html')

def main_form(request):
    """View for the main form."""
    if request.method == 'POST':
        form = PersonForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Formulário enviado com sucesso! Entraremos em contato em breve.')
            return redirect('legacy_people:landing')

        for error in form.errors.values():
            messages.error(request, error)
    return render(request, 'legacy_people/main_form.html')
