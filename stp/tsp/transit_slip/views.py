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
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

from datetime import datetime, date, timedelta

from transit_slip.models import User, Letter, Unit, Sta, TransitSlip, LetterReceipt
from transit_slip.forms import forms
import qrcode
import uuid
import os
import urllib
from random import randint
from PIL import Image
import logging
import json
import itertools

logger = logging.getLogger('transit_slip')
# Create your views here.

def get_default_letter_no(type):
    if type == 'regular':
        prefix = '23.01.955.__.__.01.01.'
        current_date = datetime.today().strftime('%d.%m.%Y')
        return prefix + current_date 
    elif type == 'do':
        return 'PF:'

def admin_user_test(user):
    if user.profile.user_type == 'ad':
        return True
    else:
        return False

def not_unit_clk_test(user):
    if user.profile.user_type == 'sc' or user.profile.user_type == 'ad':
        return True
    else:
        return False

def test_view(request):
    """
    Check the functionality of the system
    """
    context = {
        'test' : 'test string',
    }
    logger.info("hello")
    return render(request, 'transit_slip/test_page.html', context)

class Home(View):
    """
    Render home page with user instr
    """
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
@user_passes_test(admin_user_test)
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


class UnitCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Unit
    fields = "__all__"
    template_name = "transit_slip/unit_add_update.html"
    success_url = reverse_lazy("unit_list")

    def test_func(self):
        user_type = self.request.user.profile.user_type
        if user_type == 'ad':
            return True
        else:
            return False


class UnitUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Unit
    fields = ['unit_name', 'sta_name']
    template_name = "transit_slip/unit_add_update.html"
    success_url = reverse_lazy("unit_list")

    def test_func(self):
        user_type = self.request.user.profile.user_type
        if user_type == 'ad':
            return True
        else:
            return False


class LetterView(LoginRequiredMixin, View):
    """
    create new letter
    """
    template_name = 'transit_slip/new_letter.html'

    def get(self, request, *args, **kwargs):
        cur_date = datetime.today()
        init_ltr_no = get_default_letter_no(type='regular')
        form = forms.LetterForm(initial={'ltr_no':init_ltr_no, 'date': cur_date})
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
                try:
                    letter = form.save(commit=False)
                    letter.letter_type = 'reg'
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
                except Exception as err:
                    logger.warning(f'letter creation failed {err}')
                    err_msg = "New letter cration failed. Contact system admin"
                    return render(request, 'transit_slip/generic_error.html', {'err_msg':err_msg})
            else:
                return render(request, self.template_name, context)
        return redirect(letter_list_inhouse)
            
 

class DoView(LoginRequiredMixin, View):
    """
    create new DO
    """
    template_name = 'transit_slip/new_do.html'

    def get(self, request, *args, **kwargs):
        cur_date = datetime.today()
        init_ltr_no = get_default_letter_no(type='do')
        form = forms.LetterForm(initial={'ltr_no':init_ltr_no, 'date': cur_date})
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
                try:
                    letter = form.save(commit=False)
                    letter.letter_type = 'do'
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
                except Exception as err:
                    logger.warning(f'letter creation failed {err}')
                    err_msg = "New letter cration failed. Contact system admin"
                    return render(request, 'transit_slip/generic_error.html', {'err_msg':err_msg})
            else:
                return render(request, self.template_name, context)
        return redirect(letter_list_inhouse)

    


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
def letter_state(request, pk=None):
    if not pk:
        return redirect('search_ltr')
    else:
        letter = Letter.objects.get(pk=pk)
        print(request.session)
        context = {
            'letter': letter,
        }
        return render(request, 'transit_slip/letter_state.html', context)


@login_required
def letter_list_inhouse(request):
    unit = Unit.objects.get(pk=request.session['unitid'])
    letters = Letter.objects.filter(from_unit=unit, ltr_receipt=None,).order_by('-created_at')
    context = {
        'letters' : letters,
        'unit' : unit,
        'caller': 'inhouse',
    }
    return render(request, 'transit_slip/letter_list.html', context)

class LetterListDespatchedView(LoginRequiredMixin, View):
    """
    list ltr which has been despatched to sigcen
    """
    template = 'transit_slip/letter_list.html'
    
    def get(self, request, *args, **kwargs):
        unit = Unit.objects.get(pk=request.session['unitid'])
        letters = Letter.objects.filter(from_unit=unit, 
                date__gte=datetime.today()-timedelta(days=10)).exclude(ltr_receipt=None)[:400]
        context = {
        'letters' : letters,
        'unit' : unit,
        }
        return render(request, self.template, context)

    def post(self, request, *args, **kwargs):
        try:
            from_date = datetime.strptime(request.POST['from-date'], '%d-%m-%Y')
            to_date = datetime.strptime(request.POST['to-date'], '%d-%m-%Y')
            unit = Unit.objects.get(pk=request.session['unitid'])
        except ValueError:
            err_msg = "Error: Either From or To date is missing"
            return render(request, 'transit_slip/generic_error.html', {'err_msg': err_msg})
        letters = Letter.objects.filter(from_unit=unit, 
            date__gte=from_date, date__lte=to_date,).exclude(ltr_receipt=None)[:200]    
        context = {
        'letters' : letters,
        'unit' : unit,
        }
        return render(request, self.template, context)

@login_required
def letter_delete(request):
   
    if request.method == 'POST':
        print('letter delete called')
        try:

            ltr = Letter.objects.get(pk=request.POST['ltr_id'])
            print(request.POST['ltr_id'])
            ltr.delete()
            return HttpResponse('true')
        except Exception:
            return HttpResponse('false')

@login_required
def label(request, pk=None):
    """
    provide labels suitable for printing
    """
    if not pk:
        from_unit = Unit.objects.get(pk=request.session['unitid'])
        letters = Letter.objects.filter(from_unit=from_unit, ltr_receipt=None)
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
def label_bulk(request, ltr_no, date_str):
    """
    print all label of the same latter
    """
    ltr_no = urllib.parse.unquote(ltr_no)
    date = datetime.strptime(date_str, '%d%m%Y')
    print(ltr_no)
    letters = Letter.objects.filter(ltr_no=ltr_no, date=date)
    context = {
        'letters' : letters,
    }
    return render(request, 'transit_slip/label_printer.html', context)

def label_do(request, pk=None):
    """
    print label of DO letter one at once
    """
    if pk:
        letter = Letter.objects.get(pk=pk)
        unit = letter.to_unit
        sta = unit.sta_name
        # sta_full_name = letter.to_unit.sta_name
        # print(unit_full_name.sta_full_name)
        context = {
            'letter' : letter,
            'unit_full_name': unit.unit_full_name,
            'sta_full_name': sta.sta_full_name,
        }
        return render(request, 'transit_slip/label_do.html', context)

@login_required
@user_passes_test(admin_user_test)
def user_list(request):
    users = User.objects.all()
    context = {
        'users':users,
    }
    return render(request, 'registration/user_list.html', context)

@login_required
@user_passes_test(admin_user_test)
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

class ResetUserPasswordView(LoginRequiredMixin, UserPassesTestMixin, View):

    def test_func(self):
        user_type = self.request.user.profile.user_type
        if user_type == 'ad':
            return True
        else:
            return False

    def post(self, request):
        user = User.objects.get(username=request.POST['username'])
        new_passwd_1 = request.POST['new-passwd-1']
        new_passwd_2 = request.POST['new-passwd-2']
        if type(new_passwd_1) is str and type(new_passwd_2) is str:
            if new_passwd_1 == new_passwd_2:
                user.set_password(new_passwd_1)
                user.save()
                return redirect("user_list")

class PreResetUserPasswordView(LoginRequiredMixin, UserPassesTestMixin, View):
    template = "registration/reset_user_password.html"

    def test_func(self):
        user_type = self.request.user.profile.user_type
        if user_type == 'ad':
            return True
        else:
            return False

    def post(self, request):
        target_user = User.objects.get(username=request.POST['username'])
        context = {
            'target_user':target_user,
        }
        return render(request, self.template, context)

@login_required
@user_passes_test(admin_user_test)
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

class DakInManualView(LoginRequiredMixin, UserPassesTestMixin, View):
    """
    Manually receive DAK from various unit at sigcen
    """
    template = 'transit_slip/dak_in_manual.html'
    
    def test_func(self):
        user_type = self.request.user.profile.user_type
        if user_type == 'sc' or user_type == 'ad':
            return True
        else:
            return False

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
            # if searched by unique code or assigne code=none
            if form.cleaned_data['code']:
                code = form.cleaned_data['code']
            else:
                code = None
            # search letter wothout code
            if not code:
                letters = Letter.objects.filter(from_unit=unit, date=date, 
                    ltr_receipt=None).order_by('-created_at')
            else:
                letters = Letter.objects.filter(from_unit=unit, date=date, u_string=code)


            context = {
                'form' : form,
                'letters' : letters
            }
        return render(request, self.template, context)

class DakInScanView(LoginRequiredMixin, UserPassesTestMixin, View):
    """
    Receive DAK by scanning from various unit at sigcen
    """
    template = 'transit_slip/dak_in_scan.html'

    def test_func(self):
        user_type = self.request.user.profile.user_type
        if user_type == 'sc' or user_type == 'ad':
            return True
        else:
            return False

    def get(self, request, *args, **kwargs):

        context = {

        }
        return render(request, self.template, context)

class DakReceive(LoginRequiredMixin, UserPassesTestMixin, View):
    """
    Receive dak by sigcen clk after they have been scanned or manually selected as IN DAK.
    activated on clicking receive button on DAK in page.
    """

    def test_func(self):
        user_type = self.request.user.profile.user_type
        if user_type == 'sc' or user_type == 'ad':
            return True
        else:
            return False

    def post(self, request):
        # print(request.POST['submit-type'])
        received_ltrs = []
        ltr_ids = request.POST.getlist('received_ltr')
        if len(ltr_ids) <= 0:
            err_msg = 'No DAK was selected. One or more DAK needed.'
            return render(request, 'transit_slip/generic_error.html', {'err_msg':err_msg})
        spl_pkgs = request.POST.getlist('spl_pkg')
        # create ltr receipt
        received_by = User.objects.get(pk=request.session['userid'])
        ltr_receipt = LetterReceipt(received_at_sigcen=datetime.now(), received_by=received_by)
        ltr_receipt.save()
        # modifiy received  and spl_pkg attributes of each ltr 
        for ltr_id in ltr_ids:
            try:
                ltr = Letter.objects.get(pk=ltr_id)
            except ObjectDoesNotExist:
                err_msg = 'Intended letter not available or created'
                return render(request, 'transit_slip/generic_error.html', {'err_msg':err_msg})
            if ltr_id in spl_pkgs:
                ltr.spl_pkg = True
            try:
                if ltr.ltr_receipt is None:
                    ltr.ltr_receipt = ltr_receipt
                    ltr.save()
                    received_ltrs.append(ltr)
            except Exception:
                err_msg = 'Intended letter could not be received'
                logger.warning(err_msg)
                return render(request, 'transit_slip/generic_error.html', {'err_msg':err_msg})
        return redirect('receive_receipt', ltr_receipt.pk)

@login_required
@user_passes_test(not_unit_clk_test)
def receipt_list(request):
    receipt_lists = LetterReceipt.objects.all().order_by('-received_at_sigcen')[:500]
    context = {
        'receipt_lists': receipt_lists,
    }
    return render(request, 'transit_slip/receipt_list.html', context)

@login_required
@user_passes_test(not_unit_clk_test)
def receive_receipt(request, pk):
    receipt = LetterReceipt.objects.get(pk=pk)
    receive_ltrs = Letter.objects.filter(ltr_receipt=receipt)
    context = {
        'receipt': receipt,
        'receive_ltrs': receive_ltrs,
    }
    return render(request, 'transit_slip/received_receipt.html', context)


class CreateTransitSlipView(LoginRequiredMixin, UserPassesTestMixin, View):
    """
    create a transit slip automatically based on selected dst and number of ltr
    ltrs are sorted according to the received time at sigcen
    """
    template = 'transit_slip/create_transit_slip.html'
    stas = Sta.objects.all() 

    def test_func(self):
        user_type = self.request.user.profile.user_type
        if user_type == 'sc' or user_type == 'ad':
            return True
        else:
            return False

    def get(self, request, sta_id=None):
        if sta_id:
            dst_sta = Sta.objects.get(pk=sta_id)
            ltrs = Letter.objects.filter(to_unit__sta_name=dst_sta, 
                transit_slip=None).exclude(ltr_receipt=None).order_by('-ltr_receipt__received_at_sigcen')
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
        ltrs = Letter.objects.filter(to_unit__sta_name=sta_id, transit_slip=None, 
                spl_pkg=False).exclude(ltr_receipt=None).order_by('-ltr_receipt__received_at_sigcen')[:max_size]
        # ltr_count = len(ltrs)
        context = {
            'stas' : self.stas,
            'ltrs' : ltrs,
            'sta_name' : sta_name,
            # 'ltr_count' : ltr_count,
        }
        return render(request, self.template, context)

class CreateTransitSlipManualView(LoginRequiredMixin, UserPassesTestMixin, View):
    template = 'transit_slip/create_transit_slip_manually.html'
    stas = Sta.objects.all() 

    def test_func(self):
        user_type = self.request.user.profile.user_type
        if user_type == 'sc' or user_type == 'ad':
            return True
        else:
            return False

    def get(self, request):

        context = {
            'stas' : self.stas,
        }
        return render(request, self.template, context)
        
    

class TransitSlipDetailView(LoginRequiredMixin, UserPassesTestMixin, View):
    """
    displays a transit slip with given id
    """
    template = 'transit_slip/transit_slip_detail.html'

    def test_func(self):
        user_type = self.request.user.profile.user_type
        if user_type == 'sc' or user_type == 'ad':
            return True
        else:
            return False

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
@user_passes_test(not_unit_clk_test)
def transit_slip_ltrs(request):
    """
    create the actual transit slip fetching letters from the CreateTransitSlipView
    """
    if request.method == 'POST':
        try:
            dst = Sta.objects.get(sta_name=request.POST['dst-sta'])
        except ObjectDoesNotExist:
            err_msg = 'No STA was selected. Please select a dst sta.'
            return render(request, 'transit_slip/generic_error.html', {'err_msg':err_msg})
        ltr_ids = request.POST.getlist('ltr-ids')
        if len(ltr_ids) <= 0:
            err_msg = 'No DAK was selected. One or more DAK needed.'
            return render(request, 'transit_slip/generic_error.html', {'err_msg':err_msg})
        date = datetime.today()
        prepared_by = User.objects.get(pk=request.session['userid'])
        transit_slip = TransitSlip(date=date, dst=dst, prepared_by=prepared_by)
        transit_slip.save()
        for ltr_id in ltr_ids:
            ltr = Letter.objects.get(pk=ltr_id)
            ltr.transit_slip = transit_slip
            ltr.save()
    return redirect('transit_slip_detail', transit_slip.pk)

class CurrentTransitSlipView(LoginRequiredMixin, UserPassesTestMixin, View):
    template = 'transit_slip/current_transit_slip.html'

    def test_func(self):
        user_type = self.request.user.profile.user_type
        if user_type == 'sc' or user_type == 'ad':
            return True
        else:
            return False

    def get(self, request):
        t_slips = TransitSlip.objects.filter(despatched_on=None).order_by('dst')
        summary_dict = self.get_summary(t_slips)
        # print(summary_dict)
        context = {
            't_slips' : t_slips,
            'summary_dict' : summary_dict,
        }
        return render(request, self.template, context)

    def get_summary(self, t_slips):
        ts_list =[]
        for t_slip in t_slips:
            ts_touple = (t_slip.dst.sta_name, t_slip.ltr_count(), t_slip.id)
            ts_list.append(ts_touple)
        key_f = lambda x: x[0]
        sum_dict = {}
        for key, group in itertools.groupby(ts_list, key_f):
            # print(key + ":" + str(list(group)))

            ltr_count = 0
            ts_count=0
            ts_ids = []
            for idx, ltrs in enumerate(group):
                ltr_count += ltrs[1]
                ts_ids.append(ltrs[2])
                ts_count = idx+1
            sum_dict[key]= (ts_count, ltr_count, ts_ids)
            # print(ts_ids)
        return sum_dict



class OldTransitSlipView(LoginRequiredMixin, UserPassesTestMixin, View):
    template = 'transit_slip/old_transit_slip.html'

    def test_func(self):
        user_type = self.request.user.profile.user_type
        if user_type == 'sc' or user_type == 'ad':
            return True
        else:
            return False

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




class CreateSplPkgView(LoginRequiredMixin, UserPassesTestMixin, View):
    template = 'transit_slip/spl_pkg.html'
    stas = Sta.objects.all()

    def test_func(self):
        user_type = self.request.user.profile.user_type
        if user_type == 'sc' or user_type == 'ad':
            return True
        else:
            return False

    def get(self, request):
        context = {
            'stas': self.stas,
        }
        return render(request, self.template, context)

    def post(self, request):
        sta_id = request.POST['sta']
        try:
            sta_name = Sta.objects.get(pk=sta_id)
        except ValueError:
            return redirect('create_spl_pkg')
        max_size = int(request.POST['pkg-size'])
        ltrs = Letter.objects.filter(to_unit__sta_name=sta_id, transit_slip=None, 
                spl_pkg=True).exclude(ltr_receipt=None).order_by('-ltr_receipt__received_at_sigcen')[:max_size]
        # ltr_count = len(ltrs)
        context = {
            'stas' : self.stas,
            'ltrs' : ltrs,
            'sta_name' : sta_name,
            # 'ltr_count' : ltr_count,
        }
        return render(request, self.template, context)

@login_required 
@user_passes_test(not_unit_clk_test)
def generate_spl_pkg_ts(request):
    """
    create transit slip of spl pkg
    """
    if request.method == 'POST':
        dst = Sta.objects.get(sta_name=request.POST['dst-sta'])
        date = datetime.today()
        prepared_by = User.objects.get(pk=request.session['userid'])
        transit_slip = TransitSlip(date=date, dst=dst, prepared_by=prepared_by)
        transit_slip.save()
        ltr_ids = request.POST.getlist('ltr-ids')
        if len(ltr_ids) > 0:
            for ltr_id in ltr_ids:
                ltr = Letter.objects.get(pk=ltr_id)
                ltr.transit_slip = transit_slip
                ltr.save()
                # print(ltr)
        else:
            err_msg = "No DAK was selected."
            return render(request, 'transit_slip/generic_error.html', {'err_msg':err_msg})

    return redirect('transit_slip_detail', transit_slip.pk)


@login_required        
@user_passes_test(not_unit_clk_test)
def transit_slip_despatch(request, id):
    t_slip = TransitSlip.objects.get(pk=id)
    t_slip.despatched_on = datetime.today()
    t_slip.save()
    return redirect('current_transit_slip')

@login_required
@user_passes_test(not_unit_clk_test)
def ts_rcv_update(request):
    ts_id = int(request.POST['ts_id'])
    date = datetime.strptime(request.POST['date'], '%d-%m-%Y')
    try:
        ts = TransitSlip.objects.get(pk=ts_id)
    except ObjectDoesNotExist:
        response = HttpResponse("Error: Could not retrive the transit slip")
        response.status_code = 400
        return response
    ts.received_on = date    
    ts.save()
    return HttpResponse("Received date updated...")

@login_required
@user_passes_test(not_unit_clk_test)
def fetch_letter_json(request):
    date = request.POST['date']
    u_string = request.POST['u_string']
    try:
        ltr = Letter.objects.get(u_string=u_string, date=date)
        print(ltr.ltr_receipt)
        if ltr.ltr_receipt is None:
            serialize_ltr = serializers.serialize("json", [ltr,], use_natural_foreign_keys=True)
        else:
            serialize_ltr = None
    except ObjectDoesNotExist:
        return HttpResponse(None)
    return HttpResponse(serialize_ltr)

class TransitSlipPrintView(LoginRequiredMixin, UserPassesTestMixin, View):
    template = 'transit_slip/transit_slip_print.html'

    def test_func(self):
        user_type = self.request.user.profile.user_type
        if user_type == 'sc' or user_type == 'ad':
            return True
        else:
            return False

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

class SearchLtrView(LoginRequiredMixin, UserPassesTestMixin, View):
    template = 'transit_slip/search_ltr.html'

    def test_func(self):
        user_type = self.request.user.profile.user_type
        if user_type == 'sc' or user_type == 'ad':
            return True
        else:
            return False

    def get_unit_choices(self, request):
        unit_id = request.session['unitid']
        sta = Unit.objects.get(pk=unit_id).sta_name
        unit_choices = [(unit.pk, unit.unit_name) for unit in Unit.objects.filter(sta_name=sta)]
        return unit_choices

    def get(self, request):
        unit_choices = self.get_unit_choices(request)
        context = {
            'unit_choices': unit_choices,
        }
        return render(request, self.template, context)

    def post(self, request):
        print(request.POST)
        if not (request.POST['unit-id'] or request.POST['search-date']):
            return redirect('search_ltr')
        else:
            if request.POST['unit-id'] and request.POST['search-date']:
                unit = Unit.objects.get(pk=request.POST['unit-id'])
                search_date = datetime.strptime(request.POST['search-date'], "%d-%m-%Y")
                letters = Letter.objects.filter(from_unit=unit, date=search_date)[:500]
            elif request.POST['unit-id']:
                unit = Unit.objects.get(pk=request.POST['unit-id'])
                letters = Letter.objects.filter(from_unit=unit)[:500]
            else:
                search_date = datetime.strptime(request.POST['search-date'], "%d-%m-%Y")
                letters = Letter.objects.filter(date=search_date)[:500]
            unit_choices = self.get_unit_choices(request)
            context = {
                'letters': letters,
                'unit_choices': unit_choices,
            }
            return render(request, self.template, context)


@login_required
def letter_delete_admin_view(request):
    # print(request.POST['ltr_id'])
    if request.method == 'POST':
        try:
            ltr = Letter.objects.get(pk=request.POST['ltr_id'])
            ltr.delete()
            return HttpResponse('true')
        except Exception:
            return HttpResponse('false')