from django.core.serializers import serialize
from rest_framework import generics, permissions
from .models import *
from .serializers import *
import django_filters.rest_framework
import django.contrib.auth

class NewUser(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserCreateSerializer

class ListUsers(generics.ListAPIView):
    serializer_class = UserListSerializer
    queryset = User.objects.all()
    filter_backends = (django_filters.rest_framework.DjangoFilterBackend,)

class SearchUser(generics.RetrieveAPIView):
    queryset = User.objects.all()
    serializer_class = UserListSerializer

class Currencies(generics.ListAPIView):
    queryset = Currency.objects.all()
    serializer_class = CurrencySerializer
