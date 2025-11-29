from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login as auth_login, logout
from django.contrib.auth.decorators import login_required
from django import forms

class LoginForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)

def login_view(request):
    error = None
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            user = authenticate(request, username=form.cleaned_data['username'], password=form.cleaned_data['password'])
            if user is not None:
                auth_login(request, user)
                return redirect('index')
            else:
                error = 'Usuario o contraseña incorrectos.'
    else:
        form = LoginForm()
    return render(request, 'login/login.html', {'form': form, 'error': error})

@login_required
def index(request):
    return render(request, 'login/index.html')

def logout_view(request):
    logout(request)
    return redirect('login')

from django.utils import translation
from django.views.decorators.http import require_http_methods
from urllib.parse import urlparse
import logging

logger = logging.getLogger(__name__)

@require_http_methods(["POST"])
def set_language(request):
    """
    Set user language preference
    CSRF protection is enabled (csrf_exempt removed for security)
    """
    if request.method == 'POST':
        lang = request.POST.get('language', 'en')
        
        # Validate language
        if lang not in ['en', 'es']:
            logger.warning(f"Invalid language attempt: {lang} from user {request.user}")
            lang = 'en'
        
        # Set session language
        request.session['django_language'] = lang
        translation.activate(lang)
    
    # Secure redirect - validate referer is from our domain
    referer = request.META.get('HTTP_REFERER', '/')
    try:
        parsed = urlparse(referer)
        # Only redirect to relative URLs or our own domain
        if parsed.netloc and parsed.netloc not in request.get_host().split(':')[0]:
            referer = '/'
    except Exception:
        referer = '/'
    
    return redirect(referer)

# Create your views here.
