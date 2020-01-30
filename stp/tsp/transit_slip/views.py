from django.shortcuts import render, redirect, get_object_or_404
from django.core.exceptions import ObjectDoesNotExist
from django.core.files.storage import FileSystemStorage
from django.core.files import File
from django.http import HttpResponse, JsonResponse
from django.views.generic import TemplateView
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, UpdateView
from django.views import View
from django.conf import settings
from django.core import serializers
from django.urls import reverse_lazy 
from django.contrib.auth.views import PasswordChangeView
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin

from datetime import datetime, date, timedelta

from transit_slip.models import User, Letter, Unit, Sta, TransitSlip
from transit_slip.forms import forms
import qrcode
import uuid
import os
import urllib
from random import randint
from PIL import Image
import logging
import json

logger = logging.getLogger('transit_slip')
# Create your views here.

def test_view(request):
    context = {
        'test' : 'test string',
    }
    logger.info("hello")
    return render(request, 'transit_slip/test_page.html', context)

class Home(View):
    template_name = "transit_slip/home.html"
    

    def get(self, request, *args, **kwargs):
        # if request.user.is_authenticated:
        user = request.user
        if user.is_authenticated:
            request.session['userid'] = user.pk
            request.session['unitid'] = user.profile.unit.pk
        context = {
            'user': user
        }
        return render(request, self.template_name, context)

@login_required
def add_new_sta(request):
    if request.method == 'POST':
        form = forms.StaForm(request.POST)
        if form.is_valid():
            form.save()
            context = {
                'info' : "New sta added successfully"
            }
            return render(request, 'transit_slip/generic_info.html', context)
    else:
        form = forms.StaForm()
    return render(request, 'transit_slip/add_sta.html', {'form': form})



@login_required
def unit_list_view(request):
    units = Unit.objects.all()
    context = {
        'units':units
    }
    return render(request, 'transit_slip/unit_list.html', context)


class UnitCreateView(LoginRequiredMixin, CreateView):
    model = Unit
    fields = "__all__"
    template_name = "transit_slip/unit_add_update.html"
    success_url = reverse_lazy("unit_list")


class UnitUpdateView(LoginRequiredMixin, UpdateView):
    model = Unit
    fields = ['unit_name', 'sta_name']
    template_name = "transit_slip/unit_add_update.html"
    success_url = reverse_lazy("unit_list")


class LetterView(LoginRequiredMixin, View):
    """
    create new letter
    """
    template_name = 'transit_slip/new_letter.html'

    def get(self, request, *args, **kwargs):
        cur_date = datetime.today()
        init_ltr_no = self.get_default_letter_no()
        form = forms.LetterForm(initial={'ltr_no':init_ltr_no, 'date': cur_date})
        logger.info('new letter form created with ltr no %s', init_ltr_no)
        units = Unit.objects.all()
        context = {
            'form' : form,
            'units' : units,
            'init_ltr_no': init_ltr_no,
        }
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        to_units = request.POST.getlist('to_units')
        for to_unit_id in to_units:
            post_data = request.POST.copy()
            form = forms.LetterForm(post_data)
            # print(form)
            units = Unit.objects.all()
            context = {
                'form' : form,
                'units' : units,
            }
            if form.is_valid():
                letter = form.save(commit=False)
                letter.from_unit = request.user.profile.unit
                letter.to_unit = Unit.objects.get(pk=to_unit_id)
                letter.u_string = str(randint(1000, 10000))
                qr_code_name = str(date.today().strftime("%d%m%Y")) + '-' + str(letter.u_string)
                file_name = qr_code_name + '.png'
                file_path = settings.MEDIA_ROOT
                # file_url = file_path + '/qr_code/' + file_name
                file_url = file_path + '/qr_code/' +date.today().strftime("%Y/%m/%d/")+ file_name
                directory = os.path.dirname(file_url)
                if not os.path.exists(directory):
                    os.makedirs(directory)
                img = qrcode.make(qr_code_name)
                img.save(file_url)
                # letter.qr_image_url = file_name
                letter.qr_image_url = 'qr_code/' +date.today().strftime("%Y/%m/%d/")+ file_name
                # letter.to_unit = Unit.objects.get(pk=address)
                # print(letter.to_unit)
                letter.save()
                logger.info("new letter created with id %s", letter.pk)
            else:
                return render(request, self.template_name, context)
        return redirect(letter_list_inhouse)
            
        # return render(request, self.template_name, context)
    
    def get_default_letter_no(self):
        prefix = '23.01.955.__.__.01.01.'
        current_date = datetime.today().strftime('%d.%m.%Y')
        return prefix + current_date

@login_required
def letter_details(request, pk=None):
    if request.method == 'POST':
        data = request.POST.copy()
        search_token = data.get('search_token')
        try:
            letter = Letter.objects.get(date=datetime.today(), u_string=search_token)
        except ObjectDoesNotExist:
            err_msg = "letter doesn't exists or created"
            return render(request, 'transit_slip/generic_error.html', {'err_msg':err_msg})
        context = {
            'letter' : letter,
        }
    else:
        try:
            letter = Letter.objects.get(pk=pk)
        except ObjectDoesNotExist:
            err_msg = "letter doesn't exists or created"
            return render(request, 'transit_slip/letter_details.html', {'err_msg':err_msg})
        
        context = {
            'letter' : letter,
        }
    return render(request, 'transit_slip/letter_details.html', context)

@login_required
def letter_list_inhouse(request):
    unit = Unit.objects.get(pk=request.session['unitid'])
    letters = Letter.objects.filter(from_unit=unit, received_by_sigcen=False, date__gte=datetime.today()-timedelta(days=7)).order_by('-created_at')
    context = {
        'letters' : letters,
        'unit' : unit,
    }
    return render(request, 'transit_slip/letter_list.html', context)

@login_required
def letter_list_despatched(request):
    unit = Unit.objects.get(pk=request.session['unitid'])
    letters = Letter.objects.filter(from_unit=unit, received_by_sigcen=True, date__gte=datetime.today()-timedelta(days=7)).order_by('-created_at')
    context = {
        'letters' : letters,
        'unit' : unit,
    }
    return render(request, 'transit_slip/letter_list.html', context)

@login_required
def letter_delete(request, ltr_no):
    Letter.objects.filter(ltr_no=ltr_no).delete()
    return redirect('letter_list_inhouse')

@login_required
def label(request, pk=None):
    """
    provide labels suitable for printing
    """
    if not pk:
        # letters = Letter.objects.filter(from_unit= request.session['unitid'], date=datetime.today())
        from_unit = Unit.objects.get(pk=request.session['unitid'])
        letters = Letter.objects.filter(from_unit=from_unit, date=datetime.today()).order_by('-date')
        context = {
            'letters' : letters,
        }
    else:
        letter = Letter.objects.get(pk=pk)
        letters = [letter,]
        context = {
            'letters' : letters,
        }
    return render(request, 'transit_slip/label_printer.html', context)

@login_required
def label_bulk(request, ltr_no):
    """
    print all label of the same latter
    """
    ltr_no = urllib.parse.unquote(ltr_no)
    letters = Letter.objects.filter(ltr_no=ltr_no)
    context = {
        'letters' : letters,
    }
    return render(request, 'transit_slip/label_printer.html', context)

@login_required
def user_list(request):
    users = User.objects.all()
    context = {
        'users':users,
    }
    return render(request, 'registration/user_list.html', context)

@login_required
def create_user(request):
    """
    create new user
    """
    unit_id = request.session['unitid']
    sta = Unit.objects.get(pk=unit_id).sta_name
    if request.method == 'POST':
        form = forms.CreateUserForm(request.POST, sta=sta)
        if form.is_valid():
            user = form.save()
            user.refresh_from_db()  # load the profile instance created by the signal
            selected_unit_id = form.cleaned_data.get('unit')
            user.profile.unit = Unit.objects.get(pk=selected_unit_id)
            user.profile.user_type = form.cleaned_data.get('user_type')
            user.save()
            # raw_password = form.cleaned_data.get('password1')
            # user = authenticate(username=user.username, password=raw_password)
            # login(request, user)
            return redirect('user_list')
    else:
        form = forms.CreateUserForm(sta=sta)
    return render(request, 'registration/create_user.html', {'form': form})
    

class UserPasswordChangeView(LoginRequiredMixin, PasswordChangeView):
    success_url = reverse_lazy("home")

class ResetUserPasswordView(LoginRequiredMixin, View):
    def post(self, request):
        user = User.objects.get(username=request.POST['username'])
        new_passwd = request.POST['new-passwd']
        if type(new_passwd) is str:
            user.set_password(new_passwd)
            user.save()
            return redirect("user_list")

class PreResetUserPasswordView(LoginRequiredMixin, View):
    template = "registration/reset_user_password.html"
    def post(self, request):
        user = User.objects.get(username=request.POST['username'])
        context = {
            'user':user,
        }
        return render(request, self.template, context)

@login_required
def delete_user(request):
    try:
        user = User.objects.get(username=request.POST['username'])
    except ObjectDoesNotExist:
        msg = "The system was unable to find appropriate user"
        context = {
            'msg': msg,
        }
        return render(request, "transit_slip/generic_info.html", context)
    user.delete()
    return redirect("user_list")

class DakInManualView(LoginRequiredMixin, View):
    """
    Manually receive DAK from various unit at sigcen
    """
    template = 'transit_slip/dak_in_manual.html'
    
    def get(self, request, *args, **kwargs):
        unit_id = request.session['unitid']
        sta = Unit.objects.get(pk=unit_id).sta_name
        form = forms.DakInForm(sta=sta)
        context = {
            'form' : form,
        }
        return render(request, self.template, context)

    def post(self, request, *args, **kwargs):
        # print(request.POST)
        unit_id = request.session['unitid']
        sta = Unit.objects.get(pk=unit_id).sta_name
        form = forms.DakInForm(request.POST, sta=sta)
        if form.is_valid():
            unit = form.cleaned_data['unit']
            date = form.cleaned_data['date']
            if form.cleaned_data['code']:
                code = form.cleaned_data['code']
            else:
                code = None
            if not code:
                letters = Letter.objects.filter(from_unit=unit, date=date, received_by_sigcen=False).order_by('-created_at')
            else:
                letters = Letter.objects.filter(from_unit=unit, date=date, u_string=code)


            context = {
                'form' : form,
                'letters' : letters
            }
        return render(request, self.template, context)

class DakInScanView(LoginRequiredMixin, View):
    """
    Receive DAK by scanning from various unit at sigcen
    """
    template = 'transit_slip/dak_in_scan.html'

    def get(self, request, *args, **kwargs):

        context = {

        }
        return render(request, self.template, context)

class DakReceive(LoginRequiredMixin, View):
    """
    Receive dak by sigcen clk after they have been scanned or manually selected as IN DAK
    """
    def post(self, request):
        print(request.POST['submit-type'])
        ltr_ids = request.POST.getlist('received_ltr')
        spl_pkgs = request.POST.getlist('spl_pkg')
        for ltr_id in ltr_ids:
            try:
                ltr = Letter.objects.get(pk=ltr_id)
            except ObjectDoesNotExist:
                err_msg = 'Intended letter not available or created'
                return render(request, 'transit_slip/generic_error.html', err_msg)
            ltr.received_by_sigcen = True
            ltr.received_at_sigcen = datetime.now()
            if ltr_id in spl_pkgs:
                ltr.spl_pkg = True
                # print(ltr)
            ltr.save()
        if request.POST['submit-type'] == 'manual':
            return redirect('dak_in_manual')
        else:
            return redirect('dak_in_scan')
            


class CreateTransitSlipView(LoginRequiredMixin, View):
    template = 'transit_slip/transit_slip.html'
    stas = Sta.objects.all() 

    def get(self, request, sta_id=None):
        if sta_id:
            dst_sta = Sta.objects.get(pk=sta_id)
            ltrs = Letter.objects.filter(to_unit__sta_name=dst_sta, 
                received_by_sigcen=True, transit_slip=None).order_by('-received_at_sigcen')
        else:
            ltrs = None
        context = {
            'stas' : self.stas,
            'ltrs' : ltrs,
        }
        return render(request, self.template, context)

    def post(self, request):
        # print(request.POST)
        sta_id = request.POST['sta']
        try:
            sta_name = Sta.objects.get(pk=sta_id)
        except ValueError:
            return redirect('create_transit_slip')
        max_size = int(request.POST['pkg-size'])
        ltrs = Letter.objects.filter(to_unit__sta_name=sta_id, 
                received_by_sigcen=True, transit_slip=None, spl_pkg=False).order_by('-received_at_sigcen')[:max_size]
        ltr_count = len(ltrs)
        context = {
            'stas' : self.stas,
            'ltrs' : ltrs,
            'sta_name' : sta_name,
            'ltr_count' : ltr_count,
        }
        return render(request, self.template, context)

@login_required
def transit_slip_ltrs(request):
    if request.method == 'POST':
        dst = Sta.objects.get(sta_name=request.POST['dst-sta'])
        date = datetime.today()
        prepared_by = User.objects.get(pk=request.session['userid'])
        transit_slip = TransitSlip(date=date, dst=dst, prepared_by=prepared_by)
        transit_slip.save()
        ltr_ids = request.POST.getlist('ltr-ids')
        for ltr_id in ltr_ids:
            ltr = Letter.objects.get(pk=ltr_id)
            ltr.transit_slip = transit_slip
            ltr.save()

    return redirect('current_transit_slip')

class CurrentTransitSlipView(LoginRequiredMixin, View):
    template = 'transit_slip/current_transit_slip.html'

    def get(self, request):
        t_slips = TransitSlip.objects.filter(despatched_on=None)
        context = {
            't_slips' : t_slips,
        }
        return render(request, self.template, context)


class OldTransitSlipView(LoginRequiredMixin, View):
    template = 'transit_slip/old_transit_slip.html'

    def get(self, request):
        stas = Sta.objects.all()
        tr_slip_per_sta = []
        for sta in stas:
            tr_slips = TransitSlip.objects.filter(dst=sta, despatched_on__isnull=False).order_by('-date')[:30]
            sta_name = sta.sta_name
            dict = {
                'sta_name' : sta_name,
                'tr_slips' : tr_slips,
            }
            tr_slip_per_sta.append(dict)
        context = {
            'tr_slip_per_sta' : tr_slip_per_sta,
        }
        # print(tr_slip_per_sta)
        return render(request, self.template, context)


class TransitSlipDetailView(LoginRequiredMixin, View):
    template = 'transit_slip/transit_slip_detail.html'
    def get(self, request, id):
        transit_slip = TransitSlip.objects.get(pk=id)
        ltrs = Letter.objects.filter(transit_slip=transit_slip)
        ltr_count = len(ltrs)
        context = {
            'transit_slip' : transit_slip, 
            'ltrs' : ltrs,
            'ltr_count' : ltr_count,
        }
        return render(request, self.template, context)

@login_required        
def transit_slip_despatch(request, id):
    t_slip = TransitSlip.objects.get(pk=id)
    t_slip.despatched_on = datetime.today()
    t_slip.save()
    return redirect('current_transit_slip')

@login_required
def fetch_letter_json(request):
    date = request.POST['date']
    u_string = request.POST['u_string']
    try:
        ltr = Letter.objects.get(u_string=u_string, date=date)
        # print(ltr)
        serialize_ltr = serializers.serialize("json", [ltr,], use_natural_foreign_keys=True)
        # print(serialize_ltr)
    except ObjectDoesNotExist:
        return HttpResponse(None)
    return HttpResponse(serialize_ltr)

class TransitSlipPrintView(LoginRequiredMixin, View):
    template = 'transit_slip/transit_slip_print.html'
    def get(self, request, id):
        transit_slip = TransitSlip.objects.get(pk=id)
        ltrs = Letter.objects.filter(transit_slip=transit_slip)
        ltr_count = len(ltrs)
        context = {
            'transit_slip' : transit_slip, 
            'ltrs' : ltrs,
            'ltr_count': ltr_count,
        }
        return render(request, self.template, context)