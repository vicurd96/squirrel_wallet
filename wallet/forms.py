from django import forms
from wallet.models import *
from wallet.mixins import *
from wallet.validators import *
from django.utils.translation import gettext as _
from bit import PrivateKeyTestnet
from Ethereum import *
from eth_utils import from_wei
from django.contrib.auth.forms import AuthenticationForm,PasswordChangeForm
from bit.network import get_fee, get_fee_cached, NetworkAPI
from django_countries.widgets import CountrySelectWidget
from web3 import Web3,HTTPProvider
from ethereum.transactions import Transaction as Tranx
import rlp

class PasswordChangeForm(PasswordChangeForm):
    def save(self, commit=True):
        self.user.set_password(self.cleaned_data['new_password1'])
        operation = Operation(user=self.user,type='Pass')
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
        normal_fee = get_fee(fast=False)
        fast_fee = get_fee(fast=True)
    except ConnectionError:
        normal_fee = 0
        fast_fee = 0
    CHOICES = ((normal_fee, 'Normal',), (fast_fee, 'Fast',))
    to = forms.CharField(label=_('To address'),
    widget=forms.TextInput(attrs={'type':'text','data-content':'Introduce a valid address','class':'btcaddress','placeholder':'Address to transfer'}),
    max_length=64,validators=[check_bc])
    amount = forms.DecimalField(label=_('Amount'),
    widget=forms.TextInput(attrs={'type':'text','data-content':'Introduce a valid amount','class':'amount','placeholder':'Amount to transfer'}), max_digits=16,decimal_places=8)
    fee = forms.ChoiceField(required=False,choices=CHOICES,label=_('Fee'),
    widget=forms.Select(attrs={'data-content':'Introduce a valid amount','class':'fee','placeholder':'Fee (optional)'}))

    class Meta:
        model = Transaction
        fields = ('to','amount','fee')

    def __init__(self,user,*args, **kwargs):
        self.user = user
        super(BTCTXForm, self).__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        to = cleaned_data.get("to")
        amount = cleaned_data.get("amount")
        fee = cleaned_data.get("fee")
        wallet = Wallet.objects.filter(user=self.user,currency__abrev='BTC').get()
        try:
            wallet.balance = NetworkAPI.get_balance_testnet(wallet.address)
        except:
            pass
        wallet.save()
        if float(wallet.balance) < settings.MIN_BTC_TX or float(wallet.balance) < settings.MIN_BTC_TX + float(fee):
            raise forms.ValidationError(
                _('Balance must be greater than min amount (%(value)s) + fee'),params={'value': settings.MIN_BTC_TX}
            )
        if float(wallet.balance) < amount or float(wallet.balance) < float(amount) + float(fee):
            raise forms.ValidationError(
                _('Balance must be greater than amount or amount + fee')
            )


    def save(self, commit=True):
        transaction = super(BTCTXForm,self).save(commit=False)
        wallet = Wallet.objects.filter(user=self.user,currency__abrev='BTC').get()
        if commit:
            Transaction.objects.create(wallet,transaction.to,transaction.amount,transaction.fee)
            op = Operation(user=self.user,type='TXBTC')
            op.save()
        return transaction

class UsernameField(forms.CharField):
    def to_python(self, value):
        return unicodedata.normalize('NFKC', super().to_python(value))

class AuthenticationForm(AuthenticationForm):
    username = forms.CharField(label=_("User email"),widget=forms.TextInput(attrs={'type': 'email','data-validation':'email','data-content':'Email format is invalid','id':'icon_prefix','class':'validate'}))
    password = forms.CharField(label=_("Password"),widget=forms.PasswordInput(attrs={'type':'password','data-validation':'password','data-content':'Password is invalid','class':'validate'}))

class UserCreationForm(AjaxFormMixin,forms.ModelForm):
    error_messages = {
        'password_mismatch': _("The two password fields didn't match."),
    }
    email = forms.CharField(label=_("Email"),
        widget=forms.TextInput(attrs={'type':'email','data-validation':'email','data-content':'Email format is incorrect','name':'email','id':'email','class':'validate'}))
    first_name = forms.CharField(label=_("First name"),
        widget=forms.TextInput(attrs={'type':'text','data-validation':'text','data-content':'First name field is empty','name':'first','id':'first','class':'validate'}))
    last_name = forms.CharField(label=_("Last name"),
        widget=forms.TextInput(attrs={'type':'text','data-validation':'text','data-content':'Last name field is empty','name':'last','id':'last','class':'validate'}))
    password1 = forms.CharField(label=_("Password"),
        widget=forms.PasswordInput(attrs={'type':'password','data-validation':'password samepassword','data-content':'Password did not match','name':'pass1','id':'pass1','class':'validate'}))
    password2 = forms.CharField(label=_("Password confirmation"),
        widget=forms.PasswordInput(attrs={'type':'password','data-validation':'password samepassword2','name':'pass2','id':'pass2'}),
        help_text=_("Enter the same password as above, for verification."))

    class Meta:
        model = User
        fields = ('email','first_name','last_name','password1','password2')

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

    def __init__(self,user,*args, **kwargs):
        self.user = user
        super(UserForm, self).__init__(*args, **kwargs)

    def save(self, commit=True):
        self.user.first_name = self.cleaned_data['first_name']
        self.user.last_name = self.cleaned_data['last_name']
        if commit:
            self.user.save()
        return self.user

class ProfileForm(forms.ModelForm):
    HOMBRE = 'Male'
    MUJER = 'Female'
    OTRO = 'Unknown'
    GENDER_CHOICES = (
        (HOMBRE,'Male'),
        (MUJER,'Female'),
        (OTRO,'Unknown')
    )
    gender = forms.ChoiceField(label=_('Gender'),required=False,choices=GENDER_CHOICES,widget=forms.Select(attrs={'class':''}))
    birthdate = forms.DateField(label=_('Birthdate'),required=False,input_formats=settings.DATE_INPUT_FORMATS,widget=forms.TextInput(attrs=
                                {
                                    'class':'datepicker'
                                }))
    address = forms.CharField(label=_('Address'),required=False,max_length=52)
    phone = forms.CharField(label=_('Number phone'),required=False,max_length=11)
    #country = forms.CharField(required=False,widget=CountrySelectWidget())

    class Meta:
        model = Profile
        fields = ('gender','birthdate','address','country','phone')
        widgets = {'country': CountrySelectWidget(layout='{widget}')}

    def __init__(self,user,*args, **kwargs):
        self.user = user
        super(ProfileForm, self).__init__(*args, **kwargs)
        self.fields['country'].required = False

    def save(self, commit=True):
        # CAMBIAR ESTO
        self.user.profile.gender = self.cleaned_data['gender']
        self.user.profile.birthdate = self.cleaned_data['birthdate']
        self.user.profile.address = self.cleaned_data['address']
        self.user.profile.phone = self.cleaned_data['phone']
        self.user.profile.country = self.cleaned_data['country']
        if commit:
            op = Operation(user=self.user,type='Update')
            op.save()
            self.user.profile.save()
        return self.user.profile
