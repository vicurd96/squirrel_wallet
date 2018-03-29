from django.db import models
from django.contrib.auth.models import AbstractUser,BaseUserManager,AbstractBaseUser,PermissionsMixin
from django_countries.fields import CountryField
from django.conf import settings
from django.utils import timezone
from django.utils.translation import gettext as _
import uuid

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
    HOMBRE = 'Male'
    MUJER = 'Female'
    OTRO = 'Unknown'
    GENDER_CHOICES = (
        (HOMBRE,'Male'),
        (MUJER,'Female'),
        (OTRO,'Unknown')
    )
    id = models.UUIDField(primary_key=True,unique=True, default=uuid.uuid4,editable=False)
    first_name = models.CharField(_('First name'),null=False,blank=False,max_length=20)
    last_name = models.CharField(_('Last name'),null=False,blank=False,max_length=20)
    email = models.EmailField(_('Email'),unique=True,null=False,blank=False)
    birthdate = models.DateField(_('Birthdate'),null=False,blank=False)
    address = models.CharField(_('Address'),null=True,blank=True,max_length=52)
    phone = models.CharField(_('Number phone'),null=True,blank=True,max_length=11)
    gender = models.CharField(_('Gender'),null=False,max_length=7,choices=GENDER_CHOICES,default=OTRO)
    country = CountryField(_('Country'),null=False,blank_label='(Select country)')
    is_staff = models.BooleanField(_('staff status'), default=False,
        help_text=_('Designates whether the user can log into this admin '
                    'site.'))
    is_active = models.BooleanField(_('active'), default=True,
        help_text=_('Designates whether this user should be treated as '
                    'active. Unselect this instead of deleting accounts.'))
    date_joined = models.DateTimeField(_('date joined'), default=timezone.now)

    objects = UserManager()

    REQUIRED_FIELDS = ('first_name','last_name','birthdate','address','phone','gender','country')
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

class Currency(models.Model):
    abrev = models.CharField(null=False,unique=True,max_length=3)
    name = models.CharField(null=False,unique=False,max_length=20)

class Value(models.Model):
    date = models.DateTimeField(auto_now_add=True)
    currency = models.ForeignKey('Currency',on_delete=models.PROTECT)
    value = models.DecimalField(max_digits=16, decimal_places=4,default=0)

class Wallet(models.Model):
    address = models.CharField(primary_key = True,max_length=64)
    public_key = models.CharField(null=False,unique=True,max_length=64)
    private_key = models.CharField(null=False,unique=True,max_length=64)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    currency = models.ForeignKey('Currency', on_delete=models.PROTECT)
    balance = models.DecimalField(max_digits=16, decimal_places=8,default=0)

class Operation(models.Model):
    txid = models.CharField(null=False,unique=True,max_length=64)
    wallet = models.ForeignKey('Wallet',on_delete=models.PROTECT)
    to = models.CharField(null=False,unique=True,max_length=64)
    status = models.NullBooleanField(default=None)
    quantity = models.DecimalField(max_digits=16,decimal_places=8)
