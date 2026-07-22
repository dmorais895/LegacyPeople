from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.cache import cache
from django.core.paginator import Paginator
from django.http import JsonResponse
from .forms import PersonForm
from .models import Person

# Brute-force / rate-limit configuration
_MAX_LOGIN_ATTEMPTS = 5      # Maximum failed attempts before lockout
_LOCKOUT_WINDOW = 15 * 60    # Lockout duration in seconds (15 minutes)


def _get_client_ip(request):
    """Extract the real client IP, respecting reverse-proxy X-Forwarded-For."""
    x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded:
        return x_forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '0.0.0.0')


def _is_ip_locked(ip):
    """Return True if the IP has exceeded the maximum failed login attempts."""
    attempts = cache.get(f'login_attempts_{ip}', 0)
    return attempts >= _MAX_LOGIN_ATTEMPTS


def _register_failed_attempt(ip):
    """Increment the failed-attempt counter for an IP within the lockout window."""
    cache_key = f'login_attempts_{ip}'
    attempts = cache.get(cache_key, 0)
    cache.set(cache_key, attempts + 1, timeout=_LOCKOUT_WINDOW)


def _clear_failed_attempts(ip):
    """Reset the failed-attempt counter for an IP after a successful login."""
    cache.delete(f'login_attempts_{ip}')

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
    """Render and process administrative login with brute-force protection."""
    if request.user.is_authenticated:
        return redirect('legacy_people:dashboard')

    client_ip = _get_client_ip(request)

    if _is_ip_locked(client_ip):
        return render(request, 'legacy_people/login.html', {
            'locked': True,
            'lockout_minutes': _LOCKOUT_WINDOW // 60,
        })

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            _clear_failed_attempts(client_ip)
            login(request, user)
            messages.success(request, 'Login realizado com sucesso.')
            return redirect('legacy_people:dashboard')

        _register_failed_attempt(client_ip)
        remaining = _MAX_LOGIN_ATTEMPTS - cache.get(f'login_attempts_{client_ip}', 0)
        if remaining <= 0:
            return render(request, 'legacy_people/login.html', {
                'locked': True,
                'lockout_minutes': _LOCKOUT_WINDOW // 60,
            })
        messages.error(
            request,
            f'Usuário ou senha inválidos. Tentativas restantes: {remaining}.'
        )

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

def _handle_stat_ajax(type_param, page_param):
    """Return JsonResponse for reusable stat modal pagination (max 10 items per page)."""
    if type_param == 'no_gc':
        qs = Person.objects.filter(has_gc=False).order_by('-created_at')
        title = 'Pessoas sem Grupo de Crescimento'
        icon = 'bi-people'
    elif type_param == 'wants_chat':
        qs = Person.objects.filter(wants_chat=True).order_by('-created_at')
        title = 'Pessoas que Gostariam de Conversar'
        icon = 'bi-chat-dots'
    else:
        type_param = 'all'
        qs = Person.objects.all().order_by('-created_at')
        title = 'Todas as Pessoas Cadastradas'
        icon = 'bi-people-fill'

    paginator = Paginator(qs, 10)
    try:
        page_num = int(page_param)
    except (ValueError, TypeError):
        page_num = 1

    stat_page = paginator.get_page(page_num)

    people_data = [{
        'id': p.id,
        'name': p.name,
        'email': p.email,
        'whatsapp_clean': p.whatsapp_clean,
        'feeling': p.feeling,
        'feeling_label': FEELING_MAP.get(p.feeling, ('', ''))[0],
        'feeling_icon': FEELING_MAP.get(p.feeling, ('', ''))[1],
        'time_lagoinha_display': p.get_time_lagoinha_display(),
        'has_gc': p.has_gc,
        'gc_name': p.gc_name or '',
        'frequents_legacy': p.frequents_legacy,
        'legacy_reason': p.legacy_reason or '',
        'wants_chat': p.wants_chat,
    } for p in stat_page]

    return JsonResponse({
        'type': type_param,
        'title': title,
        'icon': icon,
        'total_count': paginator.count,
        'page': stat_page.number,
        'num_pages': paginator.num_pages,
        'page_range': list(paginator.page_range),
        'people': people_data,
    })

@login_required
def dashboard_view(request):
    """Authenticated dashboard displaying form data metrics and prayer requests."""
    if request.GET.get('stat_ajax') == '1':
        return _handle_stat_ajax(request.GET.get('type'), request.GET.get('page'))

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

    all_people = Person.objects.all()
    no_gc_people = Person.objects.filter(has_gc=False)
    wants_chat_people = Person.objects.filter(wants_chat=True)

    context = {
        'total_people': all_people.count(),
        'all_people': all_people,
        'no_gc_count': no_gc_people.count(),
        'no_gc_people': no_gc_people,
        'wants_chat_count': wants_chat_people.count(),
        'wants_chat_people': wants_chat_people,
        'feelings_distribution': feelings_distribution,
        'selected_feeling': selected_feeling,
        'people_list': people_list,
        'prayers_page': prayers_page,
    }

    return render(request, 'legacy_people/dashboard.html', context)
