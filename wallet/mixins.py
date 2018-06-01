from django.core.exceptions import ImproperlyConfigured
from django.http import HttpResponseRedirect,HttpResponse
from django.utils.encoding import force_text
from django.views.generic.base import ContextMixin
from two_factor.models import get_available_phone_methods
from two_factor.utils import backup_phones, default_device
from django_otp import devices_for_user, user_has_device
from django.http import JsonResponse
from .models import *
from itertools import chain
from bit.network import get_fee

class WalletMixin(ContextMixin):
    def get_tx(self):
        if(self.request.user and self.request.user.is_authenticated):
            btctx = BTCTransaction.objects.filter(wallet__in=Wallet.objects.filter(user=self.request.user,currency__abrev='BTC'))
            transactions = list(sorted(
                    chain(btctx),
                    key=lambda objects: objects.created_at,
                    reverse=True
            ))
            return transactions

    def get_wallet(self):
        return Wallet.objects.filter(user=self.request.user) if self.request.user and self.request.user.is_authenticated else None

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(**kwargs)
        if(self.request.user and self.request.user.is_authenticated):
            context['has_wallet'] = True if self.get_wallet() else False
            context['has_btc'] = True if self.get_wallet().filter(currency__abrev='BTC') else False
            context['has_eth'] = True if self.get_wallet().filter(currency__abrev='ETH') else False
            context['has_tx'] = True if self.get_tx() else False
            context['has_operations'] = True if Operation.objects.filter(user=self.request.user).order_by('-created_at') else False
            try:
                context['has_connection'] = get_fee()
            except ConnectionError:
                context['has_connection'] = False
        return context

class AjaxFormMixin(object):
    def form_invalid(self, form):
        response = super(AjaxFormMixin, self).form_invalid(form)
        if self.request.is_ajax():
            return JsonResponse(form.errors, status=400)
        else:
            return response

    def form_valid(self, form):
        response = super(AjaxFormMixin, self).form_valid(form)
        if self.request.is_ajax():
            print(form.cleaned_data)
            data = {
                'message': "Successfully submitted form data.",
                'redirect': "wallet/dashboard"
            }
            return HttpResponse(json.dumps("success"),
                mimetype="application/json")

# class MultipleFormsMixin(ContextMixin):
#     initial = {}
#     forms_classes = []
#     success_url = None
#     prefix = None
#     active_form_keyword = "selected_form"
#
#     def get_initial(self):
#         """
#         Returns the initial data to use for forms on this view.
#         """
#         return self.initial.copy()
#
#     def get_prefix(self):
#         """
#         Returns the prefix to use for forms on this view
#         """
#         return self.prefix
#
#     def get_forms_classes(self):
#         """
#         Returns the forms classes to use in this view
#         """
#         return self.forms_classes
#
#     def get_active_form_number(self):
#         """
#         Returns submitted form index in available forms list
#         """
#         if self.request.method in ('POST', 'PUT'):
#             try:
#                 return int(self.request.POST[self.active_form_keyword])
#             except (KeyError, ValueError):
#                 raise ImproperlyConfigured(
#                     "You must include hidden field with field index in every form!")
#
#     def get_forms(self, active_form=None):
#         """
#         Returns instances of the forms to be used in this view.
#         Includes provided `active_form` in forms list.
#         """
#         all_forms_classes = self.get_forms_classes()
#         all_forms = [ form_class(**self.get_form_kwargs()) for form_class in all_forms_classes]
#         if active_form:
#             active_form_number = self.get_active_form_number()
#             all_forms[active_form_number] = active_form
#         return all_forms
#
#     def get_form(self):
#         """
#         Returns active form. Works only on `POST` and `PUT`, otherwise returns None.
#         """
#         active_form_number = self.get_active_form_number()
#         if active_form_number is not None:
#             all_forms_classes = self.get_forms_classes()
#             active_form_class = all_forms_classes[active_form_number]
#             return active_form_class(**self.get_form_kwargs(is_active=True))
#
#     def get_form_kwargs(self, is_active=False):
#         """
#         Returns the keyword arguments for instantiating the form.
#         """
#         kwargs = {
#             'user': self.request.user,
#             'initial': self.get_initial(),
#             'prefix': self.get_prefix(),
#         }
#
#         if is_active:
#             kwargs.update({
#                 'user': self.request.user,
#                 'data': self.request.POST,
#                 'files': self.request.FILES,
#             })
#         return kwargs
#
#     def get_success_url(self):
#         """
#         Returns the supplied success URL.
#         """
#         if self.success_url:
#             # Forcing possible reverse_lazy evaluation
#             url = force_text(self.success_url)
#         else:
#             raise ImproperlyConfigured(
#                 "No URL to redirect to. Provide a success_url.")
#         return url
#
#     def form_valid(self, form):
#         """
#         If the form is valid, redirect to the supplied URL.
#         """
#         form.save()
#         return HttpResponseRedirect(self.get_success_url())
#
#     def form_invalid(self, form):
#         """
#         If the form is invalid, re-render the context data with the
#         data-filled forms and errors.
#         """
#         print(True)
#         return self.render_to_response(self.get_context_data(active_form=form))
#
#     def get_context_data(self, **kwargs):
#         """
#         Insert the forms into the context dict.
#         """
#         try:
#             backup_tokens = self.request.user.staticdevice_set.all()[0].token_set.count()
#         except Exception:
#             backup_tokens = 0
#
#         kwargs = {
#             'default_device': default_device(self.request.user),
#             'default_device_type': default_device(self.request.user).__class__.__name__,
#             'backup_phones': backup_phones(self.request.user),
#             'backup_tokens': backup_tokens,
#             'available_phone_methods': get_available_phone_methods()
#         }
#
#         if 'forms' not in kwargs:
#             kwargs['forms'] = self.get_forms(kwargs.get('active_form'))
#
#         return super(MultipleFormsMixin, self).get_context_data(**kwargs)
