import requests
from django import forms
from django.core.validators import MinValueValidator

from .models import *
from wallet.validators import check_bc
from django.utils.translation import gettext as _
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from bit.network import get_fee, get_fee_cached, NetworkAPI
from django_countries.widgets import CountrySelectWidget
from django.db.models import Q


class PasswordForm(PasswordChangeForm):
    def save(self, commit=True):
        self.user.set_password(self.cleaned_data['new_password1'])
        operation = Operation(user=self.user, type='Pass')
        operation.save()
        if commit:
            self.user.save()
        return self.user


class SearchTXForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ('txid',)


class TransactionForm(forms.ModelForm):
    try:
        normal_fee, fast_fee = get_fee(fast=False), get_fee(fast=True)
    except requests.ConnectionError:
        normal_fee, fast_fee = get_fee_cached(fast=False), get_fee_cached(fast=True)
    CHOICES = ((normal_fee, 'Normal',), (fast_fee, 'Fast',))
    to = forms.CharField(validators=[check_bc],label=_('To address'),
                         widget=forms.TextInput(
                             attrs={'type': 'text', 'data-content': 'Introduce a valid address', 'class': 'btcaddress',
                                    'placeholder': 'Address to transfer'}),
                         max_length=64)
    amount = forms.DecimalField(validators=[MinValueValidator(settings.MIN_BTC_TX)],label=_('Amount'),
                                widget=forms.TextInput(
                                    attrs={'type': 'text', 'data-content': 'Introduce a valid amount',
                                           'class': 'amount', 'placeholder': 'Amount to transfer'}), max_digits=16,
                                decimal_places=8)
    fee = forms.ChoiceField(required=False, choices=CHOICES, label=_('Fee'),
                            widget=forms.Select(attrs={'data-content': 'Introduce a valid amount', 'class': 'fee',
                                                       'placeholder': 'Fee (optional)'}))

    class Meta:
        model = Transaction
        fields = ('to', 'amount', 'fee')

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super(TransactionForm, self).__init__(*args, **kwargs)
        self.fields['to'].error_messages = {'required': 'Destination address is required.'}
        self.fields['amount'].error_messages = {'required': 'Enter a valid amount.'}

    def clean(self):
        cleaned_data = super(TransactionForm, self).clean()
        amount = cleaned_data.get("amount")
        fee = cleaned_data.get("fee")
        wallet = Wallet.objects.filter(user=self.user, currency__abrev='BTC').get()
        if float(wallet.balance) < settings.MIN_BTC_TX or float(wallet.balance) < settings.MIN_BTC_TX + float(fee):
            raise forms.ValidationError(
                _('Balance must be greater than min amount (%(value)s) + fee'), params={'value': settings.MIN_BTC_TX}
            )
        if float(wallet.balance) < float(amount) or float(wallet.balance) < float(amount) + float(fee):
            raise forms.ValidationError(
                _('Balance must be greater than amount or amount + fee')
            )

    def save(self, commit=True):
        transaction = super(TransactionForm, self).save(commit=False)
        wallet = Wallet.objects.filter(user=self.user, currency__abrev='BTC').get()
        if commit:
            Transaction.objects.create(wallet, transaction.to, transaction.amount, transaction.fee)
            op = Operation(user=self.user, type='TXBTC')
            op.save()
        return transaction


class AuthForm(AuthenticationForm):
    username = forms.CharField(label=_("Email"),
                               widget=forms.TextInput(attrs={'placeholder': 'example@domain.com', 'type': 'email',
                                                             'data-validation': 'email',
                                                             'data-content': 'Email format is incorrect',
                                                             'name': 'email', 'id': 'email',
                                                             'class': 'validate white-text'}),
                               help_text=_("Enter your email account"))

    password = forms.CharField(label=_("Password"),
                               widget=forms.PasswordInput(attrs={'placeholder': '1234567890A-z', 'type': 'password',
                                                                 'data-validation': 'password',
                                                                 'data-content': 'Invalid password', 'name': 'pass1',
                                                                 'id': 'pass1', 'class': 'validate white-text'}),
                               help_text=_("Enter your password"))

    error_messages = {
        'invalid_login': _("Invalid email and/or password. "),
        'inactive': _("This account is inactive."),
    }


class UserCreationForm(forms.ModelForm):
    error_messages = {
        'password_mismatch': _("The two password fields didn't match."),
    }
    email = forms.CharField(label=_("Email"),
                            widget=forms.TextInput(
                                attrs={'placeholder': 'example@domain.com', 'type': 'email', 'data-validation': 'email',
                                       'data-content': 'Email format is incorrect', 'name': 'email', 'id': 'email',
                                       'class': 'validate white-text'}),
                            help_text=_("Enter a valid email (we'll send you a validation)"))
    first_name = forms.CharField(label=_("First name"),
                                 widget=forms.TextInput(
                                     attrs={'placeholder': 'José', 'type': 'text', 'data-validation': 'text',
                                            'data-content': 'First name field is empty', 'name': 'first', 'id': 'first',
                                            'class': 'validate white-text'}),
                                 help_text=_("Enter your first name"))
    last_name = forms.CharField(label=_("Last name"),
                                widget=forms.TextInput(
                                    attrs={'placeholder': 'Hernández', 'type': 'text', 'data-validation': 'text',
                                           'data-content': 'Last name field is empty', 'name': 'last', 'id': 'last',
                                           'class': 'validate white-text'}),
                                help_text=_("Enter your last name"))
    password1 = forms.CharField(label=_("Password"),
                                widget=forms.PasswordInput(attrs={'placeholder': '123456789A-z', 'type': 'password',
                                                                  'data-validation': 'password',
                                                                  'data-content': 'Invalid password', 'name': 'pass1',
                                                                  'id': 'pass1', 'class': 'validate white-text'}),
                                help_text=_(
                                    "At least 8 digits. Must contain numbers, an uppercase and lower case letter"))
    password2 = forms.CharField(label=_("Password confirmation"),
                                widget=forms.PasswordInput(attrs={'placeholder': 'Same as before', 'type': 'password',
                                                                  'data-validation': 'password',
                                                                  'data-content': 'Invalid password', 'name': 'pass2',
                                                                  'id': 'pass2', 'class': 'validate white-text'}),
                                help_text=_("Enter the same password, for verification."))

    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name', 'password1', 'password2')

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError(
                self.error_messages['password_mismatch'],
                code='password_mismatch',
            )
        return password2

    def save(self, commit=True):
        user = super(UserCreationForm, self).save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('first_name', 'last_name',)

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super(UserForm, self).__init__(*args, **kwargs)

    def save(self, commit=True):
        self.user.first_name = self.cleaned_data['first_name']
        self.user.last_name = self.cleaned_data['last_name']
        if commit:
            self.user.save()
        return self.user

class AddContactForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('contacts',)

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super(AddContactForm,self).__init__(*args, **kwargs)

    def save(self, commit=True):
        search = self.cleaned_data['contacts']
        self.user.contacts.add(search)
        if commit:
            self.user.save()
        return self.user


class ProfileForm(forms.ModelForm):
    HOMBRE = 'Male'
    MUJER = 'Female'
    OTRO = 'Unknown'
    GENDER_CHOICES = (
        (HOMBRE, 'Male'),
        (MUJER, 'Female'),
        (OTRO, 'Unknown')
    )
    avatar = forms.ImageField(label=_('Avatar'),
                              required=False,
                              widget=forms.FileInput())
    gender = forms.ChoiceField(label=_('Gender'), required=False, choices=GENDER_CHOICES,
                               widget=forms.Select(attrs={'class': ''}))
    birthdate = forms.DateField(label=_('Birthdate'), required=False, input_formats=settings.DATE_INPUT_FORMATS,
                                widget=forms.TextInput(attrs=
                                {
                                    'class': 'datepicker'
                                }))
    address = forms.CharField(label=_('Address'), required=False, max_length=52)
    phone = forms.CharField(label=_('Number phone'), required=False, max_length=11)

    class Meta:
        model = Profile
        fields = ('avatar', 'gender', 'birthdate', 'address', 'country', 'phone')
        widgets = {'country': CountrySelectWidget(layout='{widget}')}

    def __init__(self,user, *args, **kwargs):
        self.user = user
        super(ProfileForm, self).__init__(*args, **kwargs)
        self.fields['country'].required = False
        self.fields['country'].initial = self.user.profile.country
        self.fields['gender'].initial = self.user.profile.gender
        self.fields['birthdate'].initial = self.user.profile.birthdate
        self.fields['address'].initial = self.user.profile.address
        self.fields['phone'].initial = self.user.profile.phone
        self.fields['avatar'].initial = self.user.profile.avatar

    def save(self, commit=True):
        for clean in self.cleaned_data:
            if self.cleaned_data[clean]:
                if clean == 'gender':
                    self.user.profile.gender = self.cleaned_data['gender']
                elif clean == 'birthdate':
                    self.user.profile.birthdate = self.cleaned_data['birthdate']
                elif clean == 'address':
                    self.user.profile.address = self.cleaned_data['address']
                elif clean == 'phone':
                    self.user.profile.phone = self.cleaned_data['phone']
                elif clean == 'country':
                    self.user.profile.country = self.cleaned_data['country']
                elif clean == 'avatar':
                    self.user.profile.avatar = self.cleaned_data['avatar']

        '''self.user.profile.gender = self.cleaned_data['gender']
        self.user.profile.birthdate = self.cleaned_data['birthdate']
        self.user.profile.address = self.cleaned_data['address']
        self.user.profile.phone = self.cleaned_data['phone']
        self.user.profile.country = self.cleaned_data['country']'''
        if commit:
            op = Operation.objects.create(type='Update')
            op.user.add(self.user)
            op.save()
            self.user.profile.save()
        return self.user.profile
