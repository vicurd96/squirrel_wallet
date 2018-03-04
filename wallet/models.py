from django.db import models
from django_countries.fields import CountryField
import uuid

class User(models.Model):
    HOMBRE = 'H'
    MUJER = 'M'
    OTRO = 'D'
    GENDER_CHOICES = (
        (HOMBRE,'HOMBRE'),
        (MUJER,'MUJER'),
        (OTRO,'OTRO')
    )
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(null=False,blank=False,max_length=20)
    last_name = models.CharField(null=False,blank=False,max_length=20)
    password = models.CharField(null=False,blank=False,max_length=32)
    email = models.EmailField(null=False,blank=False,unique=True)
    birthday = models.DateField(null=False,blank=False)
    address = models.CharField(null=True,blank=True,max_length=52)
    phone = models.CharField(null=True,blank=True,max_length=11)
    gender = models.CharField(null=False,max_length=2,choices=GENDER_CHOICES,default=OTRO)
    country = CountryField(null=False,blank_label='(Select country)')
    last_update = models.DateTimeField(auto_now_add=True)

class Currency(models.Model):
    abrev = models.CharField(null=False,unique=True,max_length=3)
    name = models.CharField(null=False,unique=False,max_length=20)

    def _str__(self):
        return self.name

class Wallet(models.Model):
    address = models.CharField(primary_key = True,max_length=64)
    public_key = models.CharField(null=False,unique=True,max_length=64)
    private_key = models.CharField(null=False,unique=True,max_length=64)
    user = models.ForeignKey('User', on_delete=models.CASCADE)
    currency = models.ForeignKey('Currency', on_delete=models.CASCADE)
    balance = models.DecimalField(max_digits=18, decimal_places=8,default=0)
