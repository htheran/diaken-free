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

# Create your views here.
