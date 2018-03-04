from django.http import HttpResponse,JsonResponse
from wallet.models import Currency
from django.core.serializers import serialize
from rest_framework.renderers import JSONRenderer
from rest_framework.parsers import JSONParser
from wallet.serializers import CurrencySerializer
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view

@api_view(['GET', 'POST'])
def index(request):
    if request.method == 'GET':
        curr_serializer = CurrencySerializer(Currency.objects.all(),many=True)
        return Response(curr_serializer.data)
def detail(request, question_id):
    return HttpResponse("You're looking at question %s." % question_id)

def results(request, question_id):
    response = "You're looking at the results of question %s."
    return HttpResponse(response % question_id)

def vote(request, question_id):
    return HttpResponse("You're voting on question %s." % question_id)
