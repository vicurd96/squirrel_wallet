from django.db import models
from django.contrib.auth.models import AbstractUser,BaseUserManager,AbstractBaseUser,PermissionsMixin
from django_countries.fields import CountryField
from django.conf import settings
from django.utils import timezone
from django.utils.translation import gettext as _
from django.dispatch import receiver
from django.db.models.signals import post_save
from django.core.mail import send_mail
import uuid

from fernet_fields import EncryptedCharField
from bit import PrivateKeyTestnet
from bit.network import get_fee, get_fee_cached, NetworkAPI
from Ethereum import *
import rlp

class TransactionManager(models.Manager):
    use_in_migrations = True

    def _create(self,wallet,to,amount,fee):
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

    def create(self,wallet,to,amount,fee):
        return self._create(wallet,to,amount,fee)

class WalletManager(models.Manager):
    use_in_migrations = True

    def _create(self,address,private_key,user,currency,balance):
        if not user:
            raise ValueError('The given user must be set')
        if not currency:
            raise ValueError('The given currency must be set')
        now = timezone.now()
        wallet = self.model(address=address,
                            private_key=private_key,
                            user=user,
                            currency=currency,
                            balance=balance,
                            created_at=now,
                            )
        wallet.save(using=self._db)
        return wallet

    def create(self,user,currency):
        balance = 0
        key = PrivateKeyTestnet()
        address = key.address
        private_key = key.to_wif()
        return self._create(address,private_key,user,currency,balance)

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

class User(AbstractBaseUser,PermissionsMixin):
    id = models.UUIDField(default=uuid.uuid4,editable=False)
    first_name = models.CharField(_('First name'),null=False,blank=False,max_length=20)
    last_name = models.CharField(_('Last name'),null=False,blank=False,max_length=20)
    email = models.EmailField(_('Email'),primary_key=True,unique=True,null=False,blank=False)
    is_staff = models.BooleanField(_('staff status'), default=False,
        help_text=_('Designates whether the user can log into this admin '
                    'site.'))
    is_active = models.BooleanField(_('active'), default=True,
        help_text=_('Designates whether this user should be treated as '
                    'active. Unselect this instead of deleting accounts.'))
    date_joined = models.DateTimeField(_('date joined'), default=timezone.now)

    objects = UserManager()

    REQUIRED_FIELDS = ('first_name','last_name')
    USERNAME_FIELD = 'email'

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')

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
        (HOMBRE,'Male'),
        (MUJER,'Female'),
        (OTRO,'Unknown')
    )
    user = models.OneToOneField('User',on_delete=models.CASCADE)
    birthdate = models.DateField(_('Birthdate'),null=True,blank=True)
    address = models.CharField(_('Address'),null=True,blank=True,max_length=52)
    phone = models.CharField(_('Number phone'),null=True,blank=True,max_length=11)
    gender = models.CharField(_('Gender'),null=True,max_length=7,choices=GENDER_CHOICES,default=OTRO)
    country = CountryField(_('Country'),null=True,blank_label='')
    last_update = models.DateTimeField(_('Last update'),auto_now=True)

    @receiver(post_save, sender=User)
    def create_user_profile(sender, instance, created, **kwargs):
        if created:
            Profile.objects.create(user=instance)

    @receiver(post_save, sender=User)
    def save_user_profile(sender, instance, **kwargs):
        instance.profile.save()

class Currency(models.Model):
    abrev = models.CharField(null=False,unique=True,max_length=3)
    name = models.CharField(null=False,unique=False,max_length=20)
    api = models.CharField(null=False,unique=False,max_length=256)

class Value(models.Model):
    date = models.DateField(auto_now_add=True)
    value = models.DecimalField(max_digits=16, decimal_places=4,default=0)

class Wallet(models.Model):
    address = models.CharField(primary_key = True,max_length=64)
    private_key = EncryptedCharField(null=False,max_length=64)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    currency = models.ForeignKey('Currency', on_delete=models.PROTECT)
    balance = models.DecimalField(max_digits=16, decimal_places=8,default=0)
    created_at = models.DateTimeField(_('Created at'),auto_now_add=True)
    last_update = models.DateTimeField(_('Last update'),auto_now_add=False)

    objects = WalletManager()

class Transaction(models.Model):
    IN = 'IN'
    OUT = 'OUT'
    TX_CHOICES = (
        ('IN',IN),
        ('OUT',OUT),
    )
    txid = models.CharField(_('TXID'),null=True,max_length=256)
    wallet = models.ForeignKey(_('Wallet'),'Wallet',on_delete=models.PROTECT)
    to = models.CharField(_('To address'),null=False,max_length=64)
    status = models.NullBooleanField(_('Status'),default=False)
    created_at = models.DateTimeField(_('Created at'),auto_now_add=True)
    type = models.CharField(_('Type'),max_length=3,choices=TX_CHOICES,default=OUT)
    amount = models.DecimalField(_('Amount'),null=True,max_digits=16,decimal_places=8)
    fee = models.DecimalField(_('Fee'),null=True,max_digits=16,decimal_places=8)

class Operation(models.Model):
    PASS = _('Password change')
    SEC = _('2-pass authenticator configured')
    TX = _('Cryptocurrency transaction')
    UPDATE = _('Updated profile')
    OPERATION_CHOICES = (
        ('password',PASS),
        ('update',UPDATE),
        ('security',SEC),
        ('TX',TX),
    )
    user = models.ForeignKey('User',on_delete=models.PROTECT)
    type = models.CharField(null=True,max_length=8,choices=OPERATION_CHOICES)
    created_at = models.DateTimeField(_('Created at'),auto_now_add=True)
