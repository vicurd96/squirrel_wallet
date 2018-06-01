from django.conf.urls import url
from django.conf.urls import url, include
from wallet.views import *
from django.urls import path, re_path

user_urls = [
    path('dashboard',view=Dashboard.as_view(),name='dashboard'),
    path('bitcoin/create',view=CreateBTC.as_view(),name='bitcoincreate'),
    path('ethereum/create',view=CreateETH.as_view(),name='ethereumcreate'),
    path('',view=WalletView.as_view(),name="wallet"),
    path('settings/<pk>',view=SettingsView.as_view(),name="settings"),
    path('bitcoin/<pk>',view=TransactionView.as_view(),name="detail_bitcoin"),
    path('ether/<pk>',view=ETHTransactionView.as_view(),name="detail_ether"),
    path('activity/',view=ActivityView.as_view(),name="activity")
    ]

urlpatterns = [
    path('',include(user_urls)),
]
