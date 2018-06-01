from django.conf.urls import include, url
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from wallet.views import *
from django.urls import path, re_path
from wallet.forms import AuthenticationForm
from django.contrib.auth.views import login

extra_patterns = [
    url(r'^', include('registration.backends.default.urls')),
]

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^account/login', LoginView.as_view(),
    {'auth': AuthenticationForm},name='login'),
    url(r'^account/', include(extra_patterns)),
    url(r'^wallet/',include('wallet.urls')),
    url(r'^',Index.as_view()),
]
