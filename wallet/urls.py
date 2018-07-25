from django.conf.urls import url, include
from django.conf.urls.static import static

from wallet.views import *
from django.urls import path, re_path

user_urls = [
    path('dashboard/',view=Dashboard.as_view(),name='dashboard'),
    path('bitcoin/generate/', view=CreateWalletView.as_view(), name='createwallet'),
    path('',view=WalletView.as_view(),name='wallet'),
    path('settings/<pk>',view=SettingsView.as_view(),name="settings"),
    path('profile/<pk>',view=ProfileView.as_view(),name="profile"),
    path('bitcoin/<pk>',view=TransactionView.as_view(),name="detail_bitcoin"),
    path('activity/',view=ActivityView.as_view(),name="activity"),
    path('change_password/',view=PasswordChangeView.as_view(),name="change_password"),
    path('bitcoin/actions/new_transaction',view=TransactionCreateView.as_view(),name="bitcoin_new_transaction"),
]

urlpatterns = [
    path('',include(user_urls)),
]
