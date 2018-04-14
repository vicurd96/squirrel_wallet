from django import forms
from .models import *
from django_countries.fields import CountryField
from django.utils.translation import gettext as _
from bit import Key, PrivateKeyTestnet
from Ethereum import *
import uuid

class CreateWalletForm(forms.ModelForm):
    password = forms.CharField(label=_("Password"),widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ('password', )

    def clean(self):
        cleaned_data = super(ConfirmPasswordForm, self).clean()
        password = cleaned_data.get('password')
        if not check_password(password, self.instance.password):
            self.add_error('password', 'Password does not match.')

    def save(self, commit=True):
        user = super(ConfirmPasswordForm, self).save(commit)
        if commit:
            ETH = Currency.objects.filter(abrev='ETH')
            key = Ethereum.generate_address()
            w = Wallet(key['address'],key['private_key'],user,ETH.id,0)
            user.save()
            w.save()
        return user

class UserCreationForm(forms.ModelForm):
    error_messages = {
        'password_mismatch': _("The two password fields didn't match."),
    }
    password1 = forms.CharField(label=_("Password"),
        widget=forms.PasswordInput)
    password2 = forms.CharField(label=_("Password confirmation"),
        widget=forms.PasswordInput,
        help_text=_("Enter the same password as above, for verification."))

    class Meta:
        model = User
        fields = ('email','password1','password2','first_name','last_name')

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
            BTC = Currency.objects.filter(abrev='BTC').get()
            key = PrivateKeyTestnet()
            w = Wallet(key.address,key.to_wif(),user,BTC.id,key.balance)
            user.save()
            w.save()
        return user

class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ('gender','birthdate','country','address','phone')
