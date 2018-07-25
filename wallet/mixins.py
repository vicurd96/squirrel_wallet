from collections import OrderedDict

import requests
from django.views.generic.base import ContextMixin
from django.http import JsonResponse
from .models import *
from wallet.forms import TransactionForm
from itertools import chain
from bit.network import get_fee


class WalletMixin(ContextMixin):
    def __init__(self):
        self.request = None

    def get_tx(self):
        if (self.request.user and self.request.user.is_authenticated):
            btctx = Transaction.objects.filter(
                wallet__in=Wallet.objects.filter(user=self.request.user, currency__abrev='BTC'))

            def function1(objects):
                return objects.created_at

            transactions = list(sorted(
                chain(btctx),
                key=function1,
                reverse=True
            ))
            return transactions

    def get_wallet(self):
        return Wallet.objects.filter(
            user=self.request.user) if self.request.user and self.request.user.is_authenticated else None

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user and self.request.user.is_authenticated:
            transaction_form = TransactionForm(self.request.GET)
            context['transaction_form'] = transaction_form
            context['avatar'] = self.request.user.profile.avatar

            context['has_wallet'] = True if self.get_wallet() \
                else False
            wallet = self.get_wallet().filter(currency__abrev='BTC')
            wallet = wallet.get() if wallet else None
            if context['has_wallet']:
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

            context['has_btc'] = True if self.get_wallet().filter(currency__abrev='BTC') else False
            context['has_eth'] = True if self.get_wallet().filter(currency__abrev='ETH') else False
            context['has_tx'] = True if self.get_tx() else False
            context['has_operations'] = True if Operation.objects.filter(user=self.request.user).order_by(
                "-created_at") else False

            #            CAMBIAR ESTO A CELERY
            '''try:
                context['has_connection'] = requests.
            except requests.ConnectionError:
                context['has_connection'] = False'''
        return context


class AjaxFormMixin(object):
    data = {
        'message': "Successfully submitted form data.",
    }

    def form_invalid(self, form):
        response = super(AjaxFormMixin, self).form_invalid(form)
        if self.request.is_ajax():
            return JsonResponse(data=form.errors, status=400, safe=False)
        else:
            return response

    def form_valid(self, form):
        response = super(AjaxFormMixin, self).form_valid(form)
        if self.request.is_ajax():
            return JsonResponse(self.data)
        else:
            return response
