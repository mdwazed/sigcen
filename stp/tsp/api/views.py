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
import logging
logger = logging.getLogger('transit_slip')

@api_view(['GET', 'POST'])
def transit_slip_detail(request, pk, format=None):
    """
    retrive a specific ts in response to get request.
    set ts_receive_at on post request
    """
    print('processing remote api call')
    if request.method == 'GET':
        local_sta = request.GET.get('local_sta', None)
    else:
        local_sta = request.POST.get('local_sta', None)
    if not local_sta:
        logger.warning(f'api call without local_sta arguments by user: {request.user}. ts_id: {pk}')
    try: 
        ts = TransitSlip.objects.get(pk=pk)
    except ObjectDoesNotExist:
        err_txt = f'object not found with given ts id in api call by user: {request.user}. ts_id: {pk}'
        logger.warning(err_txt)
        return Response(err_txt, status=status.HTTP_404_NOT_FOUND)
    print(f'ts-dst: {ts.dst}')
    if local_sta != ts.dst.sta_name:
        err_txt = f'local id and ts dst mismatch in api call by user: {request.user}. ts_id: {pk}'
        logger.warning(err_txt)
        return Response(err_txt, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = TransitSlipSerializer(ts)
        return Response(serializer.data)

    if request.method == 'POST':
        print('ajax post receive')
        ts_id = request.POST.get('ts_id')
        try:
            ts = TransitSlip.objects.get(pk=ts_id)
        except ObjectDoesNotExist:
            err_txt = f'object not found with given ts id while saving receive info \
                            in api call by user: {request.user}. ts_id: {pk}'
            logger.warning(err_txt)
            return Response(err_txt, status=status.HTTP_404_NOT_FOUND)
        ts.received_on = datetime.now()
        ts.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

