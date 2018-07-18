from django.urls import reverse

from wallet.models import *
from wallet.forms import *
from wallet.mixins import *
from django.views import generic
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, PasswordChangeView
from registration.backends.default.views import RegistrationView
from django.conf import settings
from django.http import HttpResponseRedirect
from collections import OrderedDict
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from currency_converter import CurrencyConverter
from django.utils.module_loading import import_string

from chartit import DataPool, Chart
from bit.network import get_fee, get_fee_cached

REGISTRATION_FORM_PATH = getattr(settings, 'REGISTRATION_FORM',
                                 'registration.forms.RegistrationForm')
REGISTRATION_FORM = import_string(REGISTRATION_FORM_PATH)

class PasswordChangeView(LoginRequiredMixin,PasswordChangeView):
    template_name = 'change_password.html'
    success_url = None

    def form_valid(self, form):
        response = super(PasswordChangeView, self).form_valid(form)
        form.save()
        if self.request.is_ajax():
            data = {
                'message': "Successfully submitted form data.",
            }
            return JsonResponse(data)
        else:
            return response

    def form_invalid(self, form):
        response = super(PasswordChangeView, self).form_invalid(form)
        if self.request.is_ajax():
            return JsonResponse(form.errors, status=400)
        else:
            return response


class LoginView(AjaxFormMixin, LoginView):
    template_name = 'registration/login.html'
    success_url = 'dashboard'
    authentication_form = AuthForm
    data = {
                'message': "Successfully logged in.",
            }


class RegistrationView(AjaxFormMixin, RegistrationView):
    data = {
        'message': "Your account has been registered successfully.",
    }


class Index(generic.TemplateView):
    template_name = "index.html"


class TransactionCreateView(LoginRequiredMixin, generic.CreateView):
    redirect_field_name = None
    template_name = 'tx.html'
    form_class = TransactionForm
    success_url = '/wallet/dashboard'

    def get_form_kwargs(self):
        kwargs = super(TransactionCreateView, self).get_form_kwargs()
        kwargs['user_pk'] = self.request.pk
        return kwargs


class CreateWalletView(LoginRequiredMixin, generic.View):
    redirect_field_name = None

    def get_queryset(self):
        return Wallet.objects.filter(user=self.request.user, currency__abrev='BTC')


    def get(self, *args, **kwargs):
        has_wallet = True if self.get_queryset() else False
        currency = Currency.objects.filter(abrev='BTC').get()
        Wallet.objects.create(user=self.request.user, currency=currency)
        if self.request.is_ajax():
            if not has_wallet:
                data = {
                    'message': "Successfully created new wallet.",
                }
                return JsonResponse(data)
            data = {
                'message': 'You\'ve created a wallet already.'
            }
            return JsonResponse(data, status=400)
        return HttpResponseRedirect("/wallet/dashboard/")


class TransactionView(WalletMixin, generic.DetailView):
    template_name = 'detailtx.html'
    model = Transaction
    form_class = SearchTXForm

    def __init__(self):
        super().__init__()
        self.object = self.get_object()

    def get_success_url(self):
        return reverse('detail_bitcoin', kwargs={'pk': self.object.id})

    def get_context_data(self, **kwargs):
        context = super(TransactionView, self).get_context_data(**kwargs)
        context['tx'] = self.object
        return context

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def form_valid(self, form):
        form.save()
        return super(TransactionView, self).form_valid(form)


class ActivityView(WalletMixin, LoginRequiredMixin, generic.ListView):
    redirect_field = None
    template_name = 'activity.html'
    success_url = '/wallet/dashboard'

    def get_queryset(self):
        return Operation.objects.filter(user=self.request.user).order_by('-created_at')

    def get_context_data(self, *args, **kwargs):
        context = super(ActivityView, self).get_context_data(**kwargs)
        context["has_wallet"] = True if self.get_wallet() else False
        context['has_tx'] = True if self.get_tx() else False
        context['has_operations'] = True if Operation.objects.filter(user=self.request.user) else False
        activity = self.get_queryset()
        paginator = Paginator(activity, 6)
        page = self.request.GET.get('page1')
        try:
            activity = paginator.page(page)
        except PageNotAnInteger:
            activity = paginator.page(1)
        except EmptyPage:
            activity = paginator.page(paginator.num_pages)
        txs = self.get_tx()
        paginator = Paginator(txs, 6)
        try:
            txs = paginator.page(page)
        except PageNotAnInteger:
            txs = paginator.page(1)
        except EmptyPage:
            txs = paginator.page(paginator.num_pages)
        context['Activity'] = activity
        context['Tranx'] = txs
        return context


class ProfileView(WalletMixin, LoginRequiredMixin, generic.FormView):
    redirect_field = None
    template_name = 'profile.html'
    context_object_name = 'profile'
    success_url = '/wallet/dashboard/'
    form_class = ProfileForm

    def get_form_kwargs(self):
        """This method is what injects forms with their keyword
            arguments."""
        # grab the current set of form #kwargs
        kwargs = super(ProfileView, self).get_form_kwargs()
        # Update the kwargs with the user_id
        kwargs['user'] = self.request.user
        return kwargs

    def post(self, request, *args, **kwargs):
        form = self.get_form(self.form_class)
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def form_valid(self, form):
        response = super(ProfileView, self).form_valid(form)
        form.save()
        if self.request.is_ajax():
            data = {
                'message': "Profile updated successfully",
            }
            return JsonResponse(data)
        else:
            return response

    def form_invalid(self, form):
        response = super(AjaxFormMixin, self).form_invalid(form)
        if self.request.is_ajax():
            return JsonResponse(form.errors, status=400)
        else:
            return response



class SettingsView(WalletMixin, LoginRequiredMixin, generic.TemplateView):
    redirect_field = None
    template_name = 'settings.html'
    context_object_name = 'settings'
    success_url = '/wallet/dashboard'

    def get_form_kwargs(self):
        kwargs = super(SettingsView, self).get_form_kwargs()
        # Update the kwargs with the user_id
        kwargs['user'] = self.request.user
        return kwargs

    def get(self, request, *args, **kwargs):
        changepass_form = PasswordChangeForm(self.request.GET)
        profile_form = ProfileForm(user=self.request.user)
        context = self.get_context_data(**kwargs)
        context['changepass_form'] = changepass_form
        context['profile_form'] = profile_form
        return self.render_to_response(context)

class WalletView(WalletMixin, LoginRequiredMixin, generic.ListView):
    redirect_field = None
    template_name = 'wallet.html'
    context_object_name = 'wallet'
    success_url = '/wallet'

    def get_queryset(self):
        return Wallet.objects.filter(user=self.request.user)

    def get_context_data(self, *args, **kwargs):
        context = super(WalletView, self).get_context_data(**kwargs)
        if self.get_wallet():
            context['has_wallet'] = True
            wallet = self.get_wallet().filter(currency__abrev='BTC')
            wallet = wallet.get() if wallet else None
            if wallet:
                context['wallet'] = OrderedDict({
                    ('qrcode', wallet.qrcode),
                    ('address', wallet.address),
                    ('balance', wallet.balance),
                    ('tx_count', Transaction.objects.filter(wallet=wallet, type='OUT').count()),
                    ('last_tx',
                     Transaction.objects.filter(wallet=wallet, type='OUT').order_by('-created_at').values_list('txid',
                                                                                                               flat=True).first()),
                    ('last_to',
                     Transaction.objects.filter(wallet=wallet, type='IN').order_by('-created_at').values_list('txid',
                                                                                                              flat=True).first()),
                })

                # CAMBIAR ESTO
                context['wallet'].move_to_end('qrcode')
                context['wallet'].move_to_end('address')
                context['wallet'].move_to_end('balance')
                context['wallet'].move_to_end('tx_count')
                context['wallet'].move_to_end('last_tx')
                context['wallet'].move_to_end('last_to')
                context['wallet'] = context['wallet'].items()
        else:
            context['has_wallet'] = False
        return context


class Dashboard(WalletMixin, LoginRequiredMixin, generic.ListView):
    redirect_field_name = None
    template_name = 'dashboard.html'
    success_url = '/wallet/dashboard'

    '''def btc_currency_value_chart(self):
        currencydata = \
            DataPool(
                series=
                [{'options': {
                    'source': Value.objects.all().order_by('-date')[:10]
                },
                    'terms': [
                        {'Bitcoin value': 'value'},
                        'date', ]}
                ])
        cht = Chart(
            datasource=currencydata,
            series_options=
            [{'options': {
                'type': 'line',
                'stacking': False,
            },
                'terms': {
                    'date': [
                        'Bitcoin value',
                    ]
                }}],
            chart_options=
            {'title': {
                'text': ' '},
                'xAxis': {
                    'title': {
                        'text': 'Date'}}})
        return cht

    def btc_tx_count(self):
        ds = DataPool(
            series=[{
                'options': {
                    'source': Transaction.objects.all().order_by('-created_at')[:10]
                },
                'terms': [
                    {'Bitcoin transactions': 'id'},
                    'created_at',
                ]
            }]
        )

        cht = Chart(
            datasource=ds,
            series_options=[{
                'options': {
                    'type': 'line',
                    'xAxis': 0,
                    'yAxis': 0,
                    'stack': 0,
                },
                'terms': {
                    'created_at': [
                        'Bitcoin transactions',
                    ]
                }
            }],
            chart_options={
                'title': {
                    'text': ' '
                },
                'xAxis': {
                    'min': 0,
                    'title': {
                        'text': 'History of all transactions per hour'
                    }
                }
            }
        )
        return cht'''

    def get_queryset(self):
        return Wallet.objects.filter(user=self.request.user)

    def get_context_data(self, *args, **kwargs):
        context = super(Dashboard, self).get_context_data(**kwargs)
        context['has_tx'] = True if self.get_tx() else False
        if self.get_queryset():
            context['has_wallet'] = True
            wallet = Wallet.objects.filter(user=self.request.user, currency__abrev='BTC')
            if wallet:
                context['balance'] = wallet.get().balance
                # CAMBIAR POR CELERY
                #context['fee'] = get_fee_cached(fast=False)
                context['last_transactions'] = Transaction.objects.filter(
                    wallet=self.get_queryset().filter(currency__abrev='BTC').get())
        else:
            context['has_wallet'] = False
        context['latest_operations'] = Operation.objects.filter(user=self.request.user).values_list()[:5]
        if Value.objects.all():
            c = CurrencyConverter()
            context['value_to_usd'] = Value.objects.filter().order_by('-date').values_list('value', flat=True).first()
            context['value_to_eur'] = c.convert(context['value_to_usd'], 'USD', 'EUR')
        #context['linechart'] = [self.btc_currency_value_chart(), self.btc_tx_count()]
        return context
