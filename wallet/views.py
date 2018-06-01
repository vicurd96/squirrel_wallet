from wallet.models import *
from wallet.forms import *
from wallet.mixins import *
from wallet.tasks import *
from django.views import generic
from django.contrib.auth.mixins import LoginRequiredMixin
from django.conf import settings
from django.http import HttpResponseRedirect
from django.views.generic.edit import ProcessFormView,FormMixin
from collections import OrderedDict
from django.shortcuts import redirect
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from currency_converter import CurrencyConverter

from bit import PrivateKeyTestnet
from chartit import DataPool, Chart
from bit.network import get_fee, get_fee_cached, NetworkAPI

# CAMBIAR ESTO
class LoginView(LoginView):
    template_name = 'registration/login.html'
    success_url = 'dashboard'

class Index(generic.TemplateView):
    template_name = "index.html"

class TransactionView(LoginRequiredMixin,generic.CreateView):
    redirect_field_name = None
    template_name = 'tx.html'
    form_class = BTCTXForm
    success_url = '/wallet/dashboard'

    def get_form_kwargs(self):
        kwargs = super(BTCTXView, self).get_form_kwargs()
        kwargs['user_pk'] = self.request.pk
        return kwargs

class CreateBTC(LoginRequiredMixin,generic.CreateView):
    redirect_field_name = None

    def get(self, *args, **kwargs):
         has_wallet = True if Wallet.objects.filter(user=self.request.user,currency__abrev='BTC') else False
         if not has_wallet:
            currency = Currency.objects.filter(abrev='BTC').get()
            Wallet.objects.create(user=self.request.user,currency=currency)
         return HttpResponseRedirect('/wallet/dashboard')

class TransactionView(WalletMixin, generic.DetailView):
    template_name = 'detailtx.html'
    model = Transaction
    form_class = SearchTXForm

    def get_success_url(self):
        return reverse('detail_bitcoin', kwargs={'pk': self.object.id})

    def get_context_data(self, **kwargs):
        context = super(TransactionView, self).get_context_data(**kwargs)
        context['tx'] = self.object
        #context['form'] = SearchTXForm(initial={'txid': self.object})
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def form_valid(self, form):
        form.save()
        return super(TransactionView, self).form_valid(form)

class ActivityView(WalletMixin,LoginRequiredMixin):
    redirect_field = None
    template_name = 'activity.html'
    success_url = '/wallet/dashboard'

    def get_context_data(self, *args, **kwargs):
        context = super(ActivityView,self).get_context_data(**kwargs)
        context['has_wallet'] = True if self.get_wallet() else False
        context['has_tx'] = True if self.get_tx() else False
        context['has_operations'] = True if Operation.objects.filter(user=self.request.user) else False
        activity = Operation.objects.filter(user=self.request.user).order_by('-created_at')
        paginator = Paginator(activity, 7)
        page = self.request.GET.get('page1')
        try:
            activity = paginator.page(page)
        except PageNotAnInteger:
            activity = paginator.page(1)
        except EmptyPage:
            activity = paginator.page(paginator.num_pages)
        txs = self.get_tx()
        paginator = Paginator(txs, 7)
        try:
            txs = paginator.page(page)
        except PageNotAnInteger:
            txs = paginator.page(1)
        except EmptyPage:
            txs = paginator.page(paginator.num_pages)
        context['Activity'] = activity
        context['Tranx'] = txs
        return context

class SettingsView(WalletMixin,LoginRequiredMixin,MultipleFormsView):
    redirect_field = None
    template_name = 'settings.html'
    context_object_name = 'settings'
    success_url = '/wallet/dashboard'

    # CAMBIAR ESTO

    forms_classes = [
        UserForm,
        ProfileForm,
        PasswordChangeForm,
    ]

    def get_forms_classes(self):
        forms_classes = super(SettingsView, self).get_forms_classes()
        user = self.request.user
        return forms_classes

    def form_valid(self, form):
        return super(SettingsView, self).form_valid(form)

class WalletView(WalletMixin,LoginRequiredMixin):
    redirect_field = None
    template_name = 'wallet.html'
    context_object_name = 'wallet'
    success_url = '/wallet'

    def get_context_data(self, *args, **kwargs):
        context = super(WalletView,self).get_context_data(**kwargs)
        if self.get_wallet():
            context['has_wallet'] = True
            wallet = self.get_wallet().filter(currency__abrev='BTC')
            wallet = wallet.get() if wallet else None
            if wallet:
                context['wallet'] = OrderedDict({
                    ('address', wallet.address),
                    ('balance', wallet.balance),
                    ('tx_count', Transaction.objects.filter(wallet=wallet,type='OUT').count()),
                    ('last_tx', Transaction.objects.filter(wallet=wallet,type='OUT').order_by('-created_at').values_list('txid',flat=True).first()),
                    ('last_to', Transaction.objects.filter(wallet=wallet,type='IN').order_by('-created_at').values_list('txid',flat=True).first()),
                })

                # CAMBIAR ESTO
                context['wallet'].move_to_end('address')
                context['wallet'].move_to_end('balance')
                context['wallet'].move_to_end('tx_count')
                context['wallet'].move_to_end('last_tx')
                context['wallet'].move_to_end('last_to')
                context['wallet'] = context['wallet'].items()
        else:
            context['has_wallet'] = False
        return context

class Dashboard(WalletMixin,LoginRequiredMixin):
    redirect_field_name = None
    template_name = 'dashboard.html'
    success_url = '/wallet/dashboard'

    def btc_currency_value_chart(self):
        currencydata = \
        DataPool(
           series=
            [{'options': {
               'source': Value.objects.all().order_by('-date')[:10]
               },
              'terms': [
                {'Bitcoin value': 'value'},
                'date',]}
             ])
        cht = Chart(
            datasource = currencydata,
            series_options =
              [{'options':{
                  'type': 'line',
                  'stacking': False,
                 },
                'terms':{
                  'date': [
                    'Bitcoin value',
                    ]
                  }}],
            chart_options =
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
                'source': BTCTransaction.objects.raw(
                            " SELECT a.hr as created, count(b.id) as id "
                            " FROM generate_series(0, 23) as a(hr) left join "
                            " wallet_transaction as b on a.hr = extract(hour from b.created_at) "
                            " GROUP BY 1 "
                            " ORDER BY 1 desc ")
            },
            'terms': [
                {'Bitcoin transactions': 'id'},
                'created',
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
                'created': [
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
        return cht

    def get_queryset(self):
        return Wallet.objects.filter(user=self.request.user)

    def get_context_data(self, *args, **kwargs):
        context = super(Dashboard,self).get_context_data(**kwargs)
        context['has_tx'] = True if self.get_tx() else False
        if self.get_queryset():
            context['has_wallet'] = True
            wallet = Wallet.objects.filter(user=self.request.user,currency__abrev='BTC')
            if wallet:
                context['balance'] = wallet.get().balance
                try:
                    context['fee'] = get_fee_cached(fast=False)
                except ConnectionError:
                    context['fee'] = 'Unknown'
                context['last_transactions'] = Transaction.objects.filter(wallet=self.get_queryset().filter(currency__abrev='BTC').get())
        else:
            context['has_wallet'] = False
        context['latest_operations'] = Operation.objects.filter(user=self.request.user).values_list()[:5]
        if Value.objects.all():
            c = CurrencyConverter()
            context['value_to_usd'] = Value.objects.filter().order_by('-date').values_list('value',flat=True).first()
            context['value_to_eur'] = c.convert(context['value_to_usd'], 'USD', 'EUR')
        context['linechart'] = [self.btc_currency_value_chart(),self.btc_tx_count()]
        return context
