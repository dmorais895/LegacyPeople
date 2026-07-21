from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import JsonResponse
from .forms import PersonForm
from .models import Person

FEELING_MAP = {
    1: ('Ótimo', 'bi-emoji-laughing'),
    2: ('Bem', 'bi-emoji-smile'),
    3: ('Neutro', 'bi-emoji-neutral'),
    4: ('Não muito bem', 'bi-emoji-frown'),
    5: ('Mal', 'bi-emoji-angry'),
}

def landing_page(request):
    """Render the public landing page."""
    return render(request, 'legacy_people/landing.html')

def main_form(request):
    """Render and process the main questionnaire form."""
    if request.method == 'POST':
        form = PersonForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Obrigado por responder nosso formulário!')
            return redirect('legacy_people:landing')
        messages.error(request, 'Por favor, corrija os erros no formulário.')
    else:
        form = PersonForm()
    return render(request, 'legacy_people/main_form.html', {'form': form})

def login_view(request):
    """Render and process administrative login."""
    if request.user.is_authenticated:
        return redirect('legacy_people:dashboard')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, 'Login realizado com sucesso.')
            return redirect('legacy_people:dashboard')
        messages.error(request, 'Usuário ou senha inválidos.')

    return render(request, 'legacy_people/login.html')

def logout_view(request):
    """Log out the current user and redirect to landing page."""
    logout(request)
    messages.info(request, 'Sessão encerrada com sucesso.')
    return redirect('legacy_people:landing')

def _get_filtered_people(feeling_param):
    """Filter Person queryset based on feeling parameter."""
    if feeling_param and feeling_param.isdigit() and int(feeling_param) in [1, 2, 3, 4, 5]:
        selected_feeling = int(feeling_param)
        return selected_feeling, Person.objects.filter(feeling=selected_feeling)
    return None, Person.objects.all()

def _handle_feeling_ajax(feeling_param):
    """Return JsonResponse for feeling_ajax request."""
    selected_feeling, people_qs = _get_filtered_people(feeling_param)
    people_data = [{
        'id': p.id,
        'name': p.name,
        'email': p.email,
        'whatsapp_clean': p.whatsapp_clean,
        'feeling': p.feeling,
        'feeling_label': FEELING_MAP.get(p.feeling, ('', ''))[0],
        'feeling_icon': FEELING_MAP.get(p.feeling, ('', ''))[1],
    } for p in people_qs]

    return JsonResponse({
        'selected_feeling': selected_feeling,
        'people': people_data,
    })

@login_required
def dashboard_view(request):
    """Authenticated dashboard displaying form data metrics and prayer requests."""
    if request.GET.get('feeling_ajax') == '1':
        return _handle_feeling_ajax(request.GET.get('feeling'))

    feelings_distribution = {
        key: Person.objects.filter(feeling=key).count() for key in range(1, 6)
    }

    selected_feeling, people_list = _get_filtered_people(request.GET.get('feeling'))

    # Paginated prayer requests (max 10 per page)
    prayers_list = Person.objects.exclude(
        prayer_request=''
    ).exclude(
        prayer_request__isnull=True
    ).order_by('-created_at')

    prayers_page = Paginator(prayers_list, 10).get_page(request.GET.get('page', 1))

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
        'total_people': Person.objects.count(),
        'no_gc_count': Person.objects.filter(has_gc=False).count(),
        'wants_chat_count': Person.objects.filter(wants_chat=True).count(),
        'feelings_distribution': feelings_distribution,
        'selected_feeling': selected_feeling,
        'people_list': people_list,
        'prayers_page': prayers_page,
    }

    return render(request, 'legacy_people/dashboard.html', context)
