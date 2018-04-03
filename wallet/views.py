from wallet.models import *
from .forms import *
from django.utils.decorators import method_decorator
from django.views import generic
from django.contrib.auth.mixins import LoginRequiredMixin

from bit import PrivateKeyTestnet,PrivateKey
from web3 import Web3, HTTPProvider

class UpdateProfile(LoginRequiredMixin,generic.UpdateView):
    login_url = 'auth_login'
    redirect_field_name = None
    form_class = ProfileForm
    model = Profile
    template_name_suffix = '_update'

class WalletSection(LoginRequiredMixin,generic.TemplateView):
    login_url = 'auth_login'
    redirect_field_name = None
    template_name = 'wallet.html'
    form_class = CreateWalletForm

    def get_queryset(self):
        return Wallet.objects.filter(user=self.request.user)

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(**kwargs)
        self.w = self.get_queryset()
        if self.w.exists():
            context['has_wallet'] = True
            context['balance'] = self.w.values_list('balance',flat=True)
            context['latest_operations'] = Operation.objects.filter(wallet=self.get_queryset())
            context['currencies_used'] = Currency.objects.filter(pk=self.w.values_list('currency_id'))
            context['currencies_used_values'] = Value.objects.filter(currency=context['currencies_used'])
        else:
            context['has_wallet'] = False
        return context

class Dashboard(LoginRequiredMixin,generic.TemplateView):
    login_url = 'auth_login'
    redirect_field_name = None
    template_name = 'dashboard.html'

    def get_queryset(self):
        return Wallet.objects.filter(user=self.request.user)

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(**kwargs)
        self.w = self.get_queryset()
        if self.w.exists():
            context['has_wallet'] = True
            context['balance'] = self.w.values_list('balance',flat=True)
            context['latest_operations'] = Operation.objects.filter(wallet=self.get_queryset)
            context['currencies_used'] = Currency.objects.filter(pk=self.w.values_list('currency_id'))
            context['currencies_used_values'] = Value.objects.filter(currency=context['currencies_used'])
        else:
            context['has_wallet'] = False
        return context
