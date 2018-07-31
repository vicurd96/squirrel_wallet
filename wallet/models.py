import io

import qrcode
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager, AbstractBaseUser, PermissionsMixin
from django.urls import reverse
from django_countries.fields import CountryField
from django.conf import settings
from django.utils import timezone
from django.utils.translation import gettext as _
from django.dispatch import receiver
from django.db.models.signals import post_save
from django.core.mail import send_mail
import uuid

from qrcode import constants
from qrcode.main import QRCode

#from wallet.currency.Bitcoin import *

from fernet_fields import EncryptedCharField
from bit import PrivateKeyTestnet

from wallet.helpers import RandomFileName
from wallet.storage import OverwriteStorage


class TransactionManager(models.Manager):
    use_in_migrations = True

    def _create(self, wallet, to, amount, fee):
        status = False
        now = timezone.now()
        wallet = self.model(wallet=wallet,
                            to=to,
                            status=status,
                            amount=amount,
                            fee=fee,
                            created_at=now,
                            )
        wallet.save(using=self._db)
        return wallet

    def create(self, wallet, to, amount, fee):
        return self._create(wallet, to, amount, fee)


class WalletManager(models.Manager):
    use_in_migrations = True

    def _create(self, user, currency):
        pair = PrivateKeyTestnet()
        now = timezone.now()
        balance = 0
        wallet = self.model(address=pair.address,
                            private_key=pair.to_wif(),
                            user=user,
                            currency=currency,
                            balance=balance,
                            created_at=now,
                            last_update=now,
                            )
        wallet.generate_qrcode()
        wallet.save(using=self._db)
        return wallet

    def create(self, user, currency):
        if not user or User.objects.filter(id=user.id) is None:
            raise ValueError('The given user must be set')
        if not currency or Currency.objects.filter(abrev=currency.abrev) is None:
            raise ValueError('The given currency must be set')
        return self._create(user, currency)


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError('The given email must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        return self._create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)
    first_name = models.CharField(_('First name'), null=False, blank=False, max_length=20)
    last_name = models.CharField(_('Last name'), null=False, blank=False, max_length=20)
    email = models.EmailField(_('Email'), unique=True, null=False, blank=False)
    contacts = models.ManyToManyField('User')
    is_staff = models.BooleanField(_('staff status'), default=False,
                                   help_text=_('Designates whether the user can log into this admin '
                                               'site.'))
    is_active = models.BooleanField(_('active'), default=True,
                                    help_text=_('Designates whether this user should be treated as '
                                                'active. Unselect this instead of deleting accounts.'))
    date_joined = models.DateTimeField(_('date joined'), default=timezone.now)

    objects = UserManager()

    REQUIRED_FIELDS = ('first_name', 'last_name')
    USERNAME_FIELD = 'email'

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')
        db_table = 'users'

    def get_full_name(self):
        full_name = '%s %s' % (self.first_name, self.last_name)
        return full_name.strip()

    def get_short_name(self):
        return self.first_name

    def email_user(self, subject, message, from_email=None, **kwargs):
        send_mail(subject, message, from_email, [self.email], **kwargs)


class Profile(models.Model):
    HOMBRE = 'Male'
    MUJER = 'Female'
    OTRO = 'Unknown'
    GENDER_CHOICES = (
        (HOMBRE, 'Male'),
        (MUJER, 'Female'),
        (OTRO, 'Unknown')
    )
    user = models.OneToOneField('User', on_delete=models.CASCADE)
    avatar = models.ImageField(upload_to=RandomFileName('static/avatar'), default='static/avatar/None/no-img.jpg', storage=OverwriteStorage())
    '''avatar_thumbnail = ImageSpecField(source='avatar',
                                      processors=[ResizeToFill(50, 50)],
                                      format='JPEG',
                                      options={'quality': 60})'''
    birthdate = models.DateField(_('Birthdate'), null=True, blank=True)
    address = models.CharField(_('Address'), null=True, blank=True, max_length=52)
    code_phone = models.CharField(_('Phone code'), null=True,blank=True,max_length=3)
    phone = models.CharField(_('Number phone'), null=True, blank=True, max_length=11)
    gender = models.CharField(_('Gender'), null=True, max_length=7, choices=GENDER_CHOICES, default=OTRO)
    country = CountryField(_('Country'), null=True, blank_label='')
    last_update = models.DateTimeField(_('Last update'), auto_now=True)

    class Meta:
        db_table = 'profiles'

    @receiver(post_save, sender=User)
    def create_user_profile(sender, instance, created, **kwargs):
        if created:
            Profile.objects.create(user=instance)

    @receiver(post_save, sender=User)
    def save_user_profile(sender, instance, **kwargs):
        instance.profile.save()


class Currency(models.Model):
    abrev = models.CharField(null=False, unique=True, max_length=3)
    name = models.CharField(null=False, unique=False, max_length=20)
    api = models.CharField(null=True, unique=False, max_length=255)

    class Meta:
        db_table = 'currencies'
        verbose_name = 'currency'
        verbose_name_plural = 'currencies'


class Value(models.Model):
    date = models.DateField(auto_now_add=True)
    value = models.DecimalField(max_digits=16, decimal_places=4, default=0)
    currency = models.ForeignKey('Currency', on_delete=models.PROTECT)

    class Meta:
        db_table = 'values'
        verbose_name = 'value'
        verbose_name_plural = 'values'


class Wallet(models.Model):
    address = models.CharField(primary_key=True, max_length=64)
    private_key = EncryptedCharField(null=False, max_length=64)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    currency = models.ForeignKey(Currency, on_delete=models.PROTECT)
    balance = models.DecimalField(_('Balance'), max_digits=16, decimal_places=8, default=0)
    created_at = models.DateTimeField(_('Created at'), auto_now_add=True)
    last_update = models.DateTimeField(_('Last update'), auto_now_add=False)
    qrcode = models.ImageField(_('QR Code'),upload_to='static/qrcode', blank=True, null=True)

    def generate_qrcode(self):
        qr = QRCode(
            version=1,
            error_correction=constants.ERROR_CORRECT_L,
            box_size=6,
            border=0,
        )
        qr.add_data(self.address)
        qr.make(fit=True)

        img = qr.make_image()

        buffer = io.BytesIO()
        img.save(buffer)
        filename = 'wallet-%s.png' % (self.address)
        filebuffer = InMemoryUploadedFile(
            buffer, None, filename, 'image/png', buffer.__sizeof__(), None)
        self.qrcode.save(filename, filebuffer)

    class Meta:
        db_table = 'wallets'

    objects = WalletManager()


class Transaction(models.Model):
    IN = 'IN'
    OUT = 'OUT'
    TX_CHOICES = (
        ('IN', IN),
        ('OUT', OUT),
    )
    txid = models.CharField(_('TXID'), null=True, max_length=255)
    wallet = models.ForeignKey(_('Wallet'), on_delete=models.PROTECT)
    to = models.CharField(_('To address'), null=False, max_length=64)
    status = models.NullBooleanField(_('Status'), default=False)
    created_at = models.DateTimeField(_('Created at'), auto_now_add=True)
    #sent = models.DateTimeField(_('Sent at'))
    type = models.CharField(_('Type'), max_length=3, choices=TX_CHOICES, default=OUT)
    amount = models.DecimalField(_('Amount'), null=True, max_digits=16, decimal_places=8)
    fee = models.DecimalField(_('Fee'), null=True, max_digits=16, decimal_places=8)

    class Meta:
        db_table = 'transactions'


class Operation(models.Model):
    PASS = _('Password change')
    SEC = _('2-pass authenticator configured')
    TX = _('Cryptocurrency transaction')
    UPDATE = _('Updated profile')
    OPERATION_CHOICES = (
        ('password', PASS),
        ('update', UPDATE),
        ('security', SEC),
        ('TX', TX),
    )
    user = models.ManyToManyField('User')
    type = models.CharField(null=True, max_length=8, choices=OPERATION_CHOICES)
    created_at = models.DateTimeField(_('Created at'), auto_now_add=True)

    class Meta:
        db_table = 'operations'
