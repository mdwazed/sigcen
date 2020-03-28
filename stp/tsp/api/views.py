from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from api.serializers import LetterSerializer, TransitSlipSerializer

from transit_slip.models import Letter, TransitSlip

from datetime import datetime, date, timedelta
import json

# Create your views here.
def test_view(request):
    """
    Check the functionality of the system
    """
    return HttpResponse('test view functioning well')

@api_view(['GET', 'POST'])
def transit_slip_detail(request, pk, format=None):
    """
    retrive a specific ts
    """
    
    remote_sta = request.GET.get('local_sta', None)
    try: 
        ts = TransitSlip.objects.get(pk=pk)
    except ObjectDoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)
    if remote_sta != ts.dst.sta_name:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = TransitSlipSerializer(ts)
        return Response(serializer.data)

    if request.method == 'POST':
        ts_id = request.POST.get('ts_id')
        try:
            ts = TransitSlip.objects.get(pk=ts_id)
        except ObjectDoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        ts.received_on = datetime.now()
        ts.save()
        return Response(status=status.HTTP_204_NO_CONTENT)