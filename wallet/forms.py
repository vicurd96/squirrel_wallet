from django.forms import ModelForm
from .models import *

class CreateUserForm(ModelForm):
    email = EmailField()
    first_name = CharField(min_length=2,max_length=20)
    last_name = CharField(min_length=2,max_length=20)
    birthday = DateField()
    address = CharField(min_length=5,max_length=52)
    phone = CharField(min_length=10,max_length=11)

    class Meta:
        model = User
        fields = ['email','first_name','last_name','gender','birthday','country','address','phone']
