from django.http import HttpResponse,JsonResponse
from django.core.serializers import serialize
from rest_framework.renderers import JSONRenderer
from rest_framework.parsers import JSONParser
from rest_framework.response import Response
from rest_framework import status

from django.http import Http404
from rest_framework.views import APIView
from rest_framework import generics, permissions
from .models import Currency,User,Wallet
from .serializers import CurrencySerializer,UserSerializer

class Users(APIView):
    def get_object(self,pk):
        try:
            return User.objects.get(pk=pk)
        except User.DoesNotExist:
            raise Http404

    def get(self,request,pk,format=None):
        user = self.get_object(pk)
        serializer = UserSerializer(user)
        return Response(serializer.data)

class Currencies(APIView):
    def get_object(self,pk):
        try:
            return Currency.objects.get(pk=pk)
        except Currency.DoesNotExist:
            raise Http404

    def get(self,request,pk,format=None):
        currency = self.get_object(pk)
        serializer = CurrencySerializer(currency)
        return Response(serializer.data)
