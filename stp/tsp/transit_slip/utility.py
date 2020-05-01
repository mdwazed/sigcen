""" provide all utility functions"""

from django.shortcuts import render
from django.db import IntegrityError
from transit_slip.models import Unit
from datetime import datetime
from django.db.models import F

from transit_slip.models import (User, Letter, OutGoingLetter)
    
def get_default_letter_no(request, type):
    if type == 'regular':
        sta = request.user.profile.unit.sta_name.sta_name
        prefix = get_ltr_prefix(sta)
        current_date = datetime.today().strftime('%d.%m.%Y')
        return prefix + current_date 
    elif type == 'do':
        return 'PF:'

def not_unit_clk_test(user):
    if user.profile.user_type == 'sc' or user.profile.user_type == 'ad':
        return True
    else:
        return False

def local_units(request):
    """
    returns the local units list. useful for select options.
    """
    sta = request.user.profile.unit.sta_name
    units = Unit.objects.filter(sta_name=sta).order_by('unit_name')
    return units

def render_generic_err(request, err_msg):
    """ Renders different error msg with custom text """
    return render(request, 'transit_slip/generic_error.html', {'err_msg': err_msg})

def get_delivery_unit_choices(request):
    sta = request.user.profile.unit.sta_name
    units = [(unit.id, unit.unit_name) for unit in Unit.objects.filter(parent=F('id'),
            sta_name=sta).order_by('unit_name')]
    return units

def process_local_ltrs(request, units):
    ltrs = Letter.objects.filter(to_unit__in=units, ltr_receipt__isnull=False,
            from_unit__sta_name=request.user.profile.unit.sta_name, delivered_locally=False)
    for ltr in ltrs:
        outgoing_ltr = OutGoingLetter(from_unit=ltr.from_unit, to_unit=ltr.to_unit,
                    date=ltr.date, code=ltr.u_string, ltr_no=ltr.ltr_no, ts_info='Local',)
        try:
            outgoing_ltr.save()
        except IntegrityError:
            pass
        ltr.delivered_locally=True
        ltr.save()

def get_ltr_prefix(sta):
    if sta == "JSR":
        return "23.01.955.__.__.01.01."
    elif sta == "RNP":
        return "23.01.966.__.__.01.01."
    elif sta == "BGR":
        return "23.01.911.__.__.01.01."
    elif sta == "SVR":
        return "23.01.909.__.__.01.01."
    elif sta == "CML":
        return "23.01.933.__.__.01.01."
    elif sta == "CTG":
        return "23.01.924.__.__.01.01."
    elif sta == "GTL":
        return "23.01.919.__.__.01.01."
    elif sta == "DHK":
        return "23.01.901.__.__.01.01."
    elif sta == "SYL":
        return "23.01.917.__.__.01.01."
    elif sta == "JLB":
        return "23.01.918.__.__.01.01."
    elif sta == "JNB":
        return "23.01.956.__.__.01.01."
    elif sta == "MRP":
        return "23.01.902.__.__.01.01."
    elif sta == "RJP":
        return "23.01.903.__.__.01.01."
    elif sta == "MWA":
        return "23.01.908.__.__.01.01."
    elif sta == "BSL":
        return "23.01.907.__.__.01.01."
    elif sta == "RAMU":
        return "23.01.910.__.__.01.01."
    elif sta == "FSK":
        return "23.01.910.__.__.01.01."
    elif sta == "ALKM":
        return "23.01.960.__.__.01.01."
    elif sta == "JBAD":
        return "23.01.912.__.__.01.01."
    elif sta == "QBAD":
        return "23.01.914.__.__.01.01."
    elif sta == "RAJ":
        return "23.01.913.__.__.01.01."
    elif sta == "MYN":
        return "23.01.920.__.__.01.01."
    elif sta == "BBC":
        return "23.01.921.__.__.01.01."
    elif sta == "AC&S":
        return "23.01.925.__.__.01.01."
    elif sta == "BMA":
        return "23.01.926.__.__.01.01."
    elif sta == "GMR":
        return "23.01.927.__.__.01.01."
    elif sta == "BBON":
        return "23.01.929.__.__.01.01."
    elif sta == "RMT":
        return "23.01.931.__.__.01.01."
    elif sta == "KPT":
        return "23.01.932.__.__.01.01."
    elif sta == "SDP":
        return "23.01.967.__.__.01.01."
    elif sta == "SMS":
        return "23.01.968.__.__.01.01."
    elif sta == "KHC":
        return "23.01.930.__.__.01.01."
    else:
        return None


