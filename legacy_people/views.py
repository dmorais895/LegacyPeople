from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from .forms import PersonForm
from .models import Person

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

def login_view(request):
    """View for user authentication."""
    if request.user.is_authenticated:
        return redirect('legacy_people:dashboard')

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'Bem-vindo de volta, {user.username}!')
            return redirect('legacy_people:dashboard')

        messages.error(request, 'Usuário ou senha inválidos.')
    else:
        form = AuthenticationForm()

    return render(request, 'legacy_people/login.html', {'form': form})

def logout_view(request):
    """View for logging out users."""
    logout(request)
    messages.info(request, 'Sessão encerrada com sucesso.')
    return redirect('legacy_people:landing')

@login_required
def dashboard_view(request):
    """Authenticated dashboard displaying form data metrics and prayer requests."""
    total_people = Person.objects.count()
    no_gc_count = Person.objects.filter(has_gc=False).count()
    wants_chat_count = Person.objects.filter(wants_chat=True).count()

    feelings_distribution = {
        1: Person.objects.filter(feeling=1).count(),
        2: Person.objects.filter(feeling=2).count(),
        3: Person.objects.filter(feeling=3).count(),
        4: Person.objects.filter(feeling=4).count(),
        5: Person.objects.filter(feeling=5).count(),
    }

    feeling_filter = request.GET.get('feeling')
    if feeling_filter and feeling_filter.isdigit() and int(feeling_filter) in [1, 2, 3, 4, 5]:
        selected_feeling = int(feeling_filter)
        people_list = Person.objects.filter(feeling=selected_feeling)
    else:
        selected_feeling = None
        people_list = Person.objects.all()

    # Paginated prayer requests (max 10 per page)
    prayers_list = Person.objects.exclude(
        prayer_request=''
    ).exclude(
        prayer_request__isnull=True
    ).order_by('-created_at')

    paginator = Paginator(prayers_list, 10)
    page_number = request.GET.get('page', 1)
    prayers_page = paginator.get_page(page_number)

    # Return self-contained AJAX response if requested
    if request.GET.get('ajax') == '1':
        prayers_data = [{
            'name': p.name,
            'created_at': p.created_at.strftime('%d/%m/%Y %H:%M') if p.created_at else '',
            'prayer_request': p.prayer_request
        } for p in prayers_page]

        return JsonResponse({
            'page': prayers_page.number,
            'num_pages': prayers_page.paginator.num_pages,
            'page_range': list(prayers_page.paginator.page_range),
            'prayers': prayers_data,
        })

    context = {
        'total_people': total_people,
        'no_gc_count': no_gc_count,
        'wants_chat_count': wants_chat_count,
        'feelings_distribution': feelings_distribution,
        'selected_feeling': selected_feeling,
        'people_list': people_list,
        'prayers_page': prayers_page,
    }
    return render(request, 'legacy_people/dashboard.html', context)
