from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.core.exceptions import ObjectDoesNotExist

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from api.serializers import LetterSerializer, TransitSlipSerializer

from transit_slip.models import Letter, TransitSlip

# Create your views here.
def test_view(request):
    """
    Check the functionality of the system
    """
    return HttpResponse('test view functioning well')

@api_view(['GET', ])
def transit_slip_detail(request, pk, format=None):
    """
    retrive a specific ts
    """
    try: 
        ts = TransitSlip.objects.get(pk=pk)
    except ObjectDoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)
    if request.method == 'GET':
        serializer = TransitSlipSerializer(ts)
        return Response(serializer.data)