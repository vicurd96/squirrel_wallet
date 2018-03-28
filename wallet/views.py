from .models import *
import django_filters.rest_framework
from two_factor.views import LoginView
from django.urls import reverse_lazy
from django.views import generic
from .forms import UserCreationForm
from django.shortcuts import get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin

class SignUp(generic.CreateView):
    form_class = UserCreationForm
    success_url = '/wallet/login'
    template_name = 'templates/signup.html'

class Login(LoginView):
    template_name = 'templates/login.html'
    def get_user(self):
        self.request.user.backend = 'django.contrib.auth.backends.ModelBackend'
        return self.request.user

class Dashboard(LoginRequiredMixin,generic.TemplateView):
    login_url = '/wallet/login'
    redirect_field_name = None
    template_name = 'templates/dashboard.html'

    def get_queryset(self):
        return Wallet.objects.filter(user=self.request.user)

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(**kwargs)
        context['balance'] = Wallet.objects.filter(user=self.request.user).values_list('balance',flat=True)
        context['latest_operations'] = Operation.objects.filter(wallet=self.get_queryset)
        context['currencies_used'] = Currency.objects.filter(currency=self.get_queryset.currency)
        context['currencies_used_values'] = Value.objects.filter(currency=context['currencies_used'])
        return context
