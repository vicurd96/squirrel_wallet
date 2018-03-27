from rest_framework import serializers
from wallet.models import Currency,User

class CurrencySerializer(serializers.ModelSerializer):
    class Meta:
        model = Currency
        fields = ('abrev','name')

class UserCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('first_name','last_name','password','email','birthday','address','phone','gender','country')

class UserListSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('uuid','first_name','last_name','email','birthday','address','phone','gender','country')
