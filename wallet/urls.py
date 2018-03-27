#from django.conf.urls import url
from django.urls import path, re_path
from django.conf.urls import url, include
from wallet.views import *
from django.contrib.auth import *
from two_factor.urls import urlpatterns as tf_urls
from two_factor.views import (BackupTokensView, DisableView, PhoneDeleteView, PhoneSetupView,
ProfileView, QRGeneratorView, SetupCompleteView, SetupView,)

user_urls = [
    path('login/',view=Login.as_view(),name='login'),
    path('signup/',view=SignUp.as_view(),name='signup'),
    ]
two_factor = [
    path(
        'account/two_factor/setup/',
        view=SetupView.as_view(),
        name='setup',
    ),
    path(
        'account/two_factor/qrcode/',
        view=QRGeneratorView.as_view(),
        name='qr',
    ),
    path(
        'account/two_factor/setup/complete/',
        view=SetupCompleteView.as_view(),
        name='setup_complete',
    ),
    path(
        'account/two_factor/backup/tokens/',
        view=BackupTokensView.as_view(),
        name='backup_tokens',
    ),
    path(
        'account/two_factor/backup/phone/register/',
        view=PhoneSetupView.as_view(),
        name='phone_create',
    ),
    re_path(
        'account/two_factor/backup/phone/unregister/(?P<pk>\d+)/$',
        view=PhoneDeleteView.as_view(),
        name='phone_delete',
    ),
    path(
        'account/two_factor/',
        view=ProfileView.as_view(),
        name='profile',
    ),
    path(
        'account/two_factor/disable/',
        view=DisableView.as_view(),
        name='disable',
    ),
]

urlpatterns = [
    path('',include(user_urls)),
    path('', include('django.contrib.auth.urls')),
    path('', include(two_factor)),
]
