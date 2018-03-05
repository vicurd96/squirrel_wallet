#from django.conf.urls import url
from django.urls import path
from django.conf.urls import url, include
from wallet.views import Users,Currencies
import uuid

user_urls = [
    path('<uuid:pk>/',Users.as_view())
    ]

currency_urls = [
    path('<int:pk>/',Currencies.as_view())
    ]

urlpatterns = [
    path('users/',include(user_urls)),
    path('currencies/',include(currency_urls))
]
