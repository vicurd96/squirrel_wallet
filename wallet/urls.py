from django.conf.urls import url
from django.conf.urls import url, include
from wallet.views import *
from django.urls import path, re_path

user_urls = [
    path('dashboard',view=Dashboard.as_view(),name='dashboard'),
    path('profile/',UpdateProfile.as_view(),name='createprofile'),
    ]

urlpatterns = [
    path('',include(user_urls)),
]
