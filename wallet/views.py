from django.core.serializers import serialize
from rest_framework import generics, permissions
from .models import *
from .serializers import *
import django_filters.rest_framework
from django.contrib.auth.forms import AuthenticationForm
from two_factor.views import LoginView

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

class LoginView(LoginView):
    template_name = 'system/core/login.html'
    def get_user(self):
        self.request.user.backend = 'django.contrib.auth.backends.ModelBackend'
        return self.request.user
