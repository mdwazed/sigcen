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
    retrive a specific ts in response to get request.
    set ts_receive_at on post request
    """
    print('ajax call receive')
    if request.method == 'GET':
        local_sta = request.GET.get('local_sta', None)
    else:
        local_sta = request.POST.get('local_sta', None)
    print(f'local_sta: {local_sta}')
    try: 
        ts = TransitSlip.objects.get(pk=pk)
    except ObjectDoesNotExist:
        print('ts not found')
        return Response(status=status.HTTP_404_NOT_FOUND)
    print(f'ts-dst: {ts.dst}')
    if local_sta != ts.dst.sta_name:
        print('domain mismatch')
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        print('ajax get receive')

        serializer = TransitSlipSerializer(ts)
        return Response(serializer.data)

    if request.method == 'POST':
        print('ajax post receive')
        ts_id = request.POST.get('ts_id')
        try:
            ts = TransitSlip.objects.get(pk=ts_id)
        except ObjectDoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        ts.received_on = datetime.now()
        ts.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

