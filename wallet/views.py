from django.core.serializers import serialize
from rest_framework import generics, permissions
from .models import *
from .serializers import *
import django_filters.rest_framework
from django.contrib.auth.forms import AuthenticationForm
from two_factor.views import LoginView
from django.urls import reverse_lazy
from django.views import generic
from .forms import UserCreationForm

class SignUp(generic.CreateView):
    form_class = UserCreationForm
    success_url = reverse_lazy('login')
    template_name = 'templates/signup.html'

class Login(LoginView):
    template_name = 'templates/login.html'
    def get_user(self):
        self.request.user.backend = 'django.contrib.auth.backends.ModelBackend'
        return self.request.user
