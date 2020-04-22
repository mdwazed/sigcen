""" provide all utility functions"""

from transit_slip.models import Unit
from datetime import datetime
    
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
    else:
        return None


