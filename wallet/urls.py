#from django.conf.urls import url
from django.urls import path
from django.conf.urls import url, include
from wallet.views import *
from django.contrib.auth import *
import uuid

user_urls = [
    path('create/',NewUser.as_view()),
    path('list/',ListUsers.as_view()),
    path('search/',SearchUser.as_view()),
    ]

currency_urls = [
    path('',Currencies.as_view())
    ]

urlpatterns = [
    path('', include('django.contrib.auth.urls')),
    path('',include(user_urls)),
    path('currencies/',include(currency_urls))
]
