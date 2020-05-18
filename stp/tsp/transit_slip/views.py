from django.shortcuts import render, redirect, get_object_or_404
from django.core.exceptions import ObjectDoesNotExist, ValidationError, MultipleObjectsReturned
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
from django.db.models import F, Q, Count

from transit_slip.models import (User, Letter, Unit, Sta, TransitSlip, LetterReceipt,
                                    OutGoingLetter, DeliveryReceipt)
from transit_slip.forms import forms
from transit_slip import utility

from datetime import datetime, date, timedelta
from random import randint
from io import BytesIO
from urllib.parse import urlparse
from PIL import Image
import qrcode
import uuid
import os
import urllib
import logging
import json
import itertools
import base64


logger = logging.getLogger('transit_slip')

def not_auth_view(request):
    err_msg = "You are not Auth to see this page. Contact Admin/Super Admin."
    return render(request, 'transit_slip/generic_error.html', {'err_msg':err_msg})

class Home(View):
    """ Render home page with user instr """

    template_name = "transit_slip/home.html"
    
    def get(self, request, *args, **kwargs):
        # print(request.headers)
        user = request.user
        if user.is_authenticated:
            request.session['userid'] = user.pk
            request.session.set_expiry(1800)
            
            try:
                request.session['unitid'] = user.profile.unit.pk
            except AttributeError as e:
                logger.warnig(f'user logoin without unitid. {e}') 
                request.session['unitid'] = None
        context = {
        }
        return render(request, self.template_name, context)

class AdminPermissionView(LoginRequiredMixin, UserPassesTestMixin, View):
    """ provide base class for user admin realted task """

    def test_func(self):
        user_type = self.request.user.profile.user_type
        if user_type == 'ad':
            return True
        else:
            return False

class UserCreateView(AdminPermissionView):
    """ Admin can create user of their respective admin AOR  """

    template = 'registration/create_user.html'

    # def get_sta(self, request):
    #     unit_id = request.session.get('unitid', None)
    #     try:
    #         sta = Unit.objects.get(pk=unit_id).sta_name
    #     except ObjectDoesNotExist as e:
    #         logger.warning(f'Sta not available. {e}')
    #         return None
    #     return sta

    def get(self, request):
        stas = request.user.profile.get_admin_stas()
        form = forms.CreateUserForm(stas=stas, user=request.user)
        return render(request, self.template, {'form': form})

    def post(self, request):
        stas = request.user.profile.get_admin_stas()
        form = forms.CreateUserForm(request.POST, stas=stas, user=request.user)
        if form.is_valid():
            # save user.auth attr
            user = form.save()
            user.refresh_from_db()  # load the profile instance created by the signal
            selected_unit_id = form.cleaned_data.get('unit')
            user.profile.unit = Unit.objects.get(pk=selected_unit_id)
            user.profile.user_type = form.cleaned_data.get('user_type')
            user.save()
            logger.info(f'New user {user.username} created by {request.user}')
            return redirect('user_list')
        else:
            return render(request, self.template, {'form': form})

class UserUpdateView(AdminPermissionView):
    """ allow admin to update user info """

    template = "registration/update_user.html"

    def get(self, request, pk):
        try:
            user = User.objects.get(pk=pk)
        except ObjectDoesNotExist:
            err_msg = "User not available."
            return render(request, "transit_slip/generic_error.html", {'err_msg': err_msg})
        if not user.is_staff:
            form = forms.UpdateUserForm(user=user)
        else:
            err_msg = "Shitty admin can't access super admin DAMM...."
            return render(request, "transit_slip/generic_error.html", {'err_msg': err_msg})
        context = {
            'form': form,
        }
        return render(request, self.template, context )

    def post(self, request, pk):
        try:
            user = User.objects.get(pk=pk)
        except ObjectDoesNotExist:
            err_msg = "User not available."
            return render(request, "transit_slip/generic_error.html", {'err_msg': err_msg})
        form = forms.UpdateUserForm(request.POST)
        # print(form)
        if form.is_valid():
            user.first_name = form.cleaned_data["first_name"]            
            user.last_name = form.cleaned_data["last_name"]            
            user.is_active = form.cleaned_data["is_active"]   
            user.save()
        else:
            form = forms.UpdateUserForm(user=user)
        return redirect('user_list')

class ResetUserPasswordView(AdminPermissionView):
    """ Allow admin to reset user passwd """

    template = "registration/reset_user_password.html"

    def get(self, request, pk):
        try:
            user = User.objects.get(pk=pk)
        except ObjectDoesNotExist as e:
            logger.warning(f'User not found' + str(e))
            err_msg = "User not found"
            return render(request, 'transit_slip/generic_error.html', {'err_msg':err_msg})
        print(user)
        context = {
            'target_user':user,
        }
        return render(request, self.template, context)

    def post(self, request, pk=None):
        try:
            user = User.objects.get(username=request.POST['username'])
        except ObjectDoesNotExist as e:
            logger.warning(f'User not found' + str(e))
            err_msg = "User not found"
            return render(request, 'transit_slip/generic_error.html', {'err_msg':err_msg})
        new_passwd_1 = request.POST['new-passwd-1']
        new_passwd_2 = request.POST['new-passwd-2']
        if type(new_passwd_1) is str and type(new_passwd_2) is str:
            if new_passwd_1 == new_passwd_2:
                user.set_password(new_passwd_1)
                user.save()
                logger.info(f'password of user {user.username} reset by {request.user}')
                return redirect("user_list")

class UserListView(AdminPermissionView):
    """ list user of the admin's respective stas """

    template = 'registration/user_list.html'

    def get(self, request):
        if request.user.is_staff:
            users = User.objects.all()
        else:
            stas = request.user.profile.get_admin_stas()
            print(stas)
            users = User.objects.filter(profile__unit__sta_name__sta_name__in=stas)
        context = {
            'users': users,
        }

        return render(request, self.template , context)


class UserPasswordChangeView(LoginRequiredMixin, PasswordChangeView):
    """ user changes own passwd """

    success_url = reverse_lazy("home")


class ChangeAdminAorView(LoginRequiredMixin, UserPassesTestMixin, View):
    """ Edit stations an admin can administer """
    template = 'transit_slip/change_admin_aor.html'

    def test_func(self):
        if self.request.user.is_staff is True:
            return True
        else:
            return False
    def handle_no_permission(self):
        # overrides method to handle not auth req
        err_msg = "You are not Auth to see this page."
        return render(self.request, 'transit_slip/generic_error.html', {'err_msg':err_msg})

    def get(self, request):
        admin_users = User.objects.filter(profile__user_type='ad')
        stas = Sta.objects.all()
        context = {
            'admin_users': admin_users,
            'stas': stas,
        }
        return render(request, self.template, context)

    def post(self, request):
        admin_user_id = int(request.POST.get('admin-user'))
        admin_stas = request.POST.getlist('stas')
        admin_stas_json = json.dumps(admin_stas)
        try:
            admin_user = User.objects.get(pk=admin_user_id)
            admin_user.profile.admin_stas = admin_stas_json
            admin_user.save()
        except ObjectDoesNotExist as e:
            err_msg = f'Intended user not found.' + str(e)
            return render(request, 'transit_slip/generic_error.html', {'err_msg':err_msg})
        
        return redirect('/user_list/')


class DeleteUserView(AdminPermissionView):
    def post(self, request):
        user_id = request.POST.get('user_id', None)
        try:
            user = User.objects.get(pk=user_id)
        except ObjectDoesNotExist as e:
            logger.warning(f'Intended user for update not found. {e}')
            err_msg = f'Intended user for update not found.' + str(e)
            return render(request, 'transit_slip/generic_error.html', {'err_msg':err_msg})
        if not user.is_staff:
            user.delete()
        return HttpResponse(status=200)


class StaAddView(AdminPermissionView):
    template = 'transit_slip/add_sta.html'
    def get(self, request):
        form = forms.StaForm()
        stas = Sta.objects.all()
        context = {
            'form': form,
            'stas': stas,
        }
        return render(request, self.template, context)

    def post(self, request):
        if request.user.is_staff:
            form = forms.StaForm(request.POST)
            if form.is_valid():
                form.save()
                return redirect('add_sta')
        else:
            return redirect('not_auth_view')


class UpdateStaView(AdminPermissionView):
    """ admin update sta info """

    template = 'transit_slip/add_sta.html'

    def get(self, request, pk=None):
        try:
            sta = Sta.objects.get(pk=pk)
        except ObjectDoesNotExist as e:
            logger.warning(f'Intended sta for update not found. {e}')
            err_msg = f'Intended sta for update not found.' + str(e)
            return render(request, 'transit_slip/generic_error.html', {'err_msg':err_msg})
        form = forms.StaForm(instance= sta)
        context = {
            'form': form,
        }
        return render(request, self.template, context)

    def post(self, request, pk=None):
        if request.user.is_staff:
            try:
                sta = Sta.objects.get(pk=pk)
            except ObjectDoesNotExist as e:
                logger.warning(f'Intended sta for update not found. {e}')
                err_msg = f'Intended sta for update not found.' + str(e)
                return render(request, 'transit_slip/generic_error.html', {'err_msg':err_msg})
            form = forms.StaForm(instance= sta, data=request.POST)
            if form.is_valid():
                form.save()
                return redirect('add_sta')
            else:
                form = forms.StaForm(instance=sta, data = request.POST)
                return render(request, self.template, {'form': form})
        else:
            return redirect('not_auth_view')

class UnitListView(LoginRequiredMixin, View):
    """ display list of units from own sta in admin panel. """

    template = 'transit_slip/unit_list.html'

    def get(self, request):
        # if request.user.is_staff is True:
        units = Unit.objects.all().order_by('unit_name')
        # else:
            # units = Unit.objects.filter(sta_name=request.user.profile.unit.sta_name)
        context = {
            'units': units,
        }
        return render(request, self.template, context)


class UnitCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """ Allow only super admin to create new unit. """

    model = Unit
    fields = "__all__"
    template_name = "transit_slip/unit_add_update.html"
    success_url = reverse_lazy("unit_list")

    def test_func(self):
        if self.request.user.is_staff is True:
            return True
        else:
            return False
    def handle_no_permission(self):
        # overrides method to handle not auth req
        err_msg = "You are not Auth to see this page."
        return render(self.request, 'transit_slip/generic_error.html', {'err_msg':err_msg})

class UnitUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Unit
    fields = ['unit_name', 'unit_full_name', 'sta_name', 'unit_code', 'parent']
    template_name = "transit_slip/unit_add_update.html"
    success_url = reverse_lazy("unit_list")

    def test_func(self):
        if self.request.user.is_staff is True:
            return True
        else:
            return False
    def handle_no_permission(self):
        err_msg = "You are not Auth to see this page."
        return render(self.request, 'transit_slip/generic_error.html', {'err_msg':err_msg})


class UnitDeleteView(View):
    def get(self, request, pk):
        info = """Unit can't be deleted as it will leave inconsistant letter data in database.
            To delete an unit delete all letter of the respective unit and then
            delete the unit from the super admin panel."""
        return render(request, 'transit_slip/generic_info.html', { 'info': info })


class LetterView(LoginRequiredMixin, View):
    """
    create new letter
    """
    template_name = 'transit_slip/new_letter.html'

    def get(self, request, *args, **kwargs):
        cur_date = datetime.today()
        init_ltr_no = utility.get_default_letter_no(request, type='regular')
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
        err_msg = None
        for to_unit_id in to_units:
            post_data = request.POST.copy()
            form = forms.LetterForm(post_data)
            units = Unit.objects.all()
            
            if form.is_valid():
                try:
                    letter = form.save(commit=False)
                    letter.letter_type = 'reg'
                    letter.from_unit = request.user.profile.unit
                    letter.to_unit = Unit.objects.get(pk=to_unit_id)
                    letter.u_string = str(randint(10000, 99999))
                    qr_code_name = str(date.today().strftime("%d%m%Y")) + '-' + str(letter.u_string)
                    file_name = qr_code_name + '.png'
                    file_path = settings.MEDIA_ROOT
                    file_url = file_path + '/qr_code/' + date.today().strftime("%Y/%m/%d/") + file_name
                    directory = os.path.dirname(file_url)
                    if not os.path.exists(directory):
                        os.makedirs(directory)
                    img = qrcode.make(qr_code_name)
                    img.save(file_url)
                    letter.qr_image_url = 'qr_code/' +date.today().strftime("%Y/%m/%d/")+ file_name
                    letter.save()
                except Exception as e:
                    logger.warning(f'letter creation failed. {e}')
                    err_msg = "One or more new DAK cration failed. Check in house list" \
                                " and create the failed DAK again."
            else:
                context = {
                    'form' : form,
                    'units' : units,
                }
                return render(request, self.template_name, context)
        if err_msg:
            return render(request, 'transit_slip/generic_error.html', {'err_msg':err_msg})
        return redirect('/letter_list/inhouse')
            
class DoView(LoginRequiredMixin, View):
    """ create new DO """

    template_name = 'transit_slip/new_do.html'

    def get(self, request, *args, **kwargs):
        cur_date = datetime.today()
        init_ltr_no = utility.get_default_letter_no(request, type='do')
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
                    letter.u_string = str(randint(10000, 99999))
                    qr_code_name = str(date.today().strftime("%d%m%Y")) + '-' + str(letter.u_string)
                    file_name = qr_code_name + '.png'
                    file_path = settings.MEDIA_ROOT
                    # file_url = file_path + '/qr_code/' + file_name
                    file_url = file_path + '/qr_code/' + date.today().strftime("%Y/%m/%d/") + file_name
                    directory = os.path.dirname(file_url)
                    if not os.path.exists(directory):
                        os.makedirs(directory)
                    img = qrcode.make(qr_code_name)
                    img.save(file_url)
                    # letter.qr_image_url = file_name
                    letter.qr_image_url = 'qr_code/' + date.today().strftime("%Y/%m/%d/")+ file_name
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
        return redirect('/letter_list/inhouse')


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
        try:
            letter = Letter.objects.get(pk=pk)
        except ObjectDoesNotExist as e:
            err_msg = "letter not found in system." + str(e)
            return render(request, 'transit_slip/letter_details.html', {'err_msg':err_msg})
        try:
            through_sigcens = json.loads(letter.transit_slip.through_sigcens)
        except (AttributeError, TypeError): # transit slip not yet assigned
            through_sigcens = None
        try:
            dst_ltr = OutGoingLetter.objects.get(date=letter.date, code=letter.u_string)
        except (ObjectDoesNotExist, MultipleObjectsReturned) as e:
            # not yet received by dst sigcen. continue with home sigcen info.
            dst_ltr = None
            
        context = {
            'letter': letter,
            'dst_ltr': dst_ltr,
            'through_sigcens': through_sigcens,
        }
        return render(request, 'transit_slip/letter_state.html', context)


# @login_required
# def letter_list_inhouse(request):
#     unit = Unit.objects.get(pk=request.session['unitid'])
#     letters = Letter.objects.filter(from_unit=unit, ltr_receipt=None,).order_by('-created_at')
#     context = {
#         'letters' : letters,
#         'unit' : unit,
#         'caller': 'inhouse',
#     }
#     return render(request, 'transit_slip/letter_list.html', context)

class LetterListView(LoginRequiredMixin, View):
    """ lists ltrs of various type ie. inhouse, despatched, local delivered  """

    template = 'transit_slip/letter_list.html'
    
    def get(self, request, *args, **kwargs):
        unit = Unit.objects.get(pk=request.session['unitid'])
        catagory = kwargs.pop('catagory')
        print(catagory)
        if catagory == 'inhouse':
            letters = Letter.status_objects.get_unit_ltrs().filter(
                from_unit=request.user.profile.unit).order_by('-created_at')[:200]
            
        elif catagory == 'despatched':
            letters = Letter.status_objects.get_despatched_letters().filter(
                from_unit=request.user.profile.unit).order_by('-created_at')[:200]
        elif catagory == 'local_delivered':
            letters = Letter.status_objects.get_local_delivered_ltrs().filter(
                from_unit=request.user.profile.unit).order_by('-created_at')[:200]
        context = {
        'letters' : letters,
        'unit' : unit,
        }
        return render(request, self.template, context)

    def post(self, request, *args, **kwargs):
        try:
            catagory = kwargs.pop('catagory')
            from_date = datetime.strptime(request.POST['from-date'], '%d-%m-%Y')
            to_date = datetime.strptime(request.POST['to-date'], '%d-%m-%Y')
            unit = request.user.profile.unit
        except ValueError:
            err_msg = "Error: Either From or To date is missing"
            return render(request, 'transit_slip/generic_error.html', {'err_msg': err_msg})
        if catagory == 'inhouse':
            letters = Letter.status_objects.get_unit_ltrs().filter(from_unit=unit,
                date__gte=from_date, date__lte=to_date).order_by('-created_at')[:200]
        elif catagory == 'despatched':
            letters = Letter.status_objects.get_despatched_letters().filter(from_unit=unit, 
                date__gte=from_date, date__lte=to_date,).order_by('-created_at')[:200]  
        elif catagory == 'local_delivered':
            letters = Letter.status_objects.get_local_delivered_ltrs().filter(from_unit=unit, 
                date__gte=from_date, date__lte=to_date,).order_by('-created_at')[:200]
        context = {
        'letters' : letters,
        }
        return render(request, self.template, context)

@login_required
def letter_delete(request):
    if request.method == 'POST':
        try:
            ltr = Letter.objects.get(pk=request.POST['ltr_id'])
            print(request.POST['ltr_id'])
            ltr.delete()
            return HttpResponse(status=204)
        except Exception:
            return HttpResponse(status=404)

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
    letters = Letter.objects.filter(ltr_no=ltr_no, date=date)
    context = {
        'letters' : letters,
    }
    return render(request, 'transit_slip/label_printer.html', context)

@login_required
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



class DakInManualView(LoginRequiredMixin, UserPassesTestMixin, View):
    """ Manually receive DAK from various unit at sigcen """

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
        sta = request.user.profile.unit.sta_name
        form = forms.DakInForm(request.POST, sta=sta)
        if form.is_valid():
            unit = form.cleaned_data['unit']
            date = form.cleaned_data['date']
            code = form.cleaned_data['code']
            if date and code:
                letters = Letter.objects.filter(from_unit=unit, date=date, 
                    u_string=code, ltr_receipt=None, delivered_locally=False).order_by('-created_at')
            elif date:
                letters = Letter.objects.filter(from_unit=unit, date=date, 
                    ltr_receipt=None, delivered_locally=False).order_by('-created_at')
            elif code:
                letters = Letter.objects.filter(from_unit=unit, u_string=code, 
                    ltr_receipt=None, delivered_locally=False).order_by('-created_at')
            else:
                letters = Letter.objects.filter(from_unit=unit, 
                    ltr_receipt=None, delivered_locally=False).order_by('-created_at')[:50]
            context = {
                'form' : form,
                'letters' : letters
            }
        else:
            err_msg = "form validation failed."
            return render(request, 'transit_slip/generic_error.html', {'err_msg':err_msg})
        return render(request, self.template, context)

class DakInScanView(LoginRequiredMixin, UserPassesTestMixin, View):
    """ Receive DAK by scanning from various unit at sigcen """

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
    activated on clicking receive button on dak_in page.
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
@user_passes_test(utility.not_unit_clk_test)
def receipt_list(request):
    receipt_lists = LetterReceipt.objects.filter(
                received_by__profile__unit__sta_name=request.user.profile.unit.sta_name
                ).order_by('-received_at_sigcen')[:200]
    context = {
        'receipt_lists': receipt_lists,
    }
    return render(request, 'transit_slip/receipt_list.html', context)

@login_required
@user_passes_test(utility.not_unit_clk_test)
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
    create a transit slip automatically based on selected dst and number of ltr.
    ltrs are sorted according to the received time at sigcen
    """
    template = 'transit_slip/create_transit_slip.html'
    stas = Sta.objects.all().order_by('sta_name') 

    def test_func(self):
        user_type = self.request.user.profile.user_type
        if user_type == 'sc' or user_type == 'ad':
            return True
        else:
            return False

    def get(self, request, sta_id=None):
        # if sta_id:
            # user_sta = request.user.profile.unit.sta_name
            # print(f'user sta {user_sta}')
            # dst_sta = Sta.objects.get(pk=sta_id)
            # ltrs = Letter.objects.filter(to_unit__sta_name=dst_sta, 
                # transit_slip=None).exclude(ltr_receipt=None, from_unit__sta_name=user_sta ).order_by('-ltr_receipt__received_at_sigcen')
        # else:
            # ltrs = None
        context = {
            'stas' : self.stas,
            # 'ltrs' : ltrs,
        }
        return render(request, self.template, context)

    def post(self, request):
        # print(request.POST)
        user_sta = request.user.profile.unit.sta_name
        print(type(user_sta))
        sta_id = request.POST['sta']
        try:
            sta_name = Sta.objects.get(pk=sta_id)
        except ValueError:
            return redirect('create_transit_slip')
        max_size = int(request.POST['pkg-size'])
        ltrs = Letter.objects.filter(to_unit__sta_name=sta_id, transit_slip=None, 
                spl_pkg=False, from_unit__sta_name=user_sta).exclude(ltr_receipt=None,).order_by('-ltr_receipt__received_at_sigcen')[:max_size]
        # ltr_count = len(ltrs)
        # ltrs = Letter.objects.filter(from_unit__sta_name=user_sta)
        context = {
            'stas' : self.stas,
            'ltrs' : ltrs,
            'sta_name' : sta_name,
            # 'ltr_count' : ltr_count,
        }
        return render(request, self.template, context)

class CreateTransitSlipManualView(LoginRequiredMixin, UserPassesTestMixin, View):
    """ creates transit slip by scanning the qr code """
    template = 'transit_slip/create_transit_slip_manually.html'
    stas = Sta.objects.all().order_by('sta_name') 

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
    """ displays a transit slip with given id """

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
        qr_code = qrcode.make(transit_slip.id)
        buffered = BytesIO()
        qr_code.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue())
        img_str = img_str.decode('utf-8')
        context = {
            'transit_slip' : transit_slip, 
            'ltrs' : ltrs,
            'ltr_count' : ltr_count,
            'qr_code': img_str,
        }
        return render(request, self.template, context)
        

# class TransitSlipPrintView(LoginRequiredMixin, UserPassesTestMixin, View):
#     """ print transit slip. why a separate view? """
#     template = 'transit_slip/transit_slip_print.html'

#     def test_func(self):
#         user_type = self.request.user.profile.user_type
#         if user_type == 'sc' or user_type == 'ad':
#             return True
#         else:
#             return False

#     def get(self, request, id):
#         transit_slip = TransitSlip.objects.get(pk=id)
#         ltrs = Letter.objects.filter(transit_slip=transit_slip)
#         ltr_count = len(ltrs)
#         qr_code = qrcode.make(transit_slip.id)
#         context = {
#             'transit_slip' : transit_slip, 
#             'ltrs' : ltrs,
#             'ltr_count': ltr_count,
#             'qr_code': qr_code,
#         }
#         return render(request, self.template, context)

@login_required
@user_passes_test(utility.not_unit_clk_test)
def transit_slip_ltrs(request):
    """
    create the actual transit slip fetching letters from the CreateTransitSlipView
    and createTransitSlipManualView
    """
    candidate_ltr_count = 0
    if request.method == 'POST':
        try:
            dst = Sta.objects.get(sta_name=request.POST.get('dst-sta'))
        except ObjectDoesNotExist:
            err_msg = 'No STA was selected. Please select a dst sta.'
            return render(request, 'transit_slip/generic_error.html', {'err_msg':err_msg})
        if (dst == request.user.profile.unit.sta_name):
            err_msg = 'Same STA TS not allowed.'
            return render(request, 'transit_slip/generic_error.html', {'err_msg':err_msg})
        ltr_ids = request.POST.getlist('ltr-ids')
        if len(ltr_ids) <= 0:
            logger.info(f'Zero length Transit slip create prevented')
            err_msg = 'No DAK was selected. One or more DAK needed.'
            return render(request, 'transit_slip/generic_error.html', {'err_msg':err_msg})
        date = datetime.today()
        prepared_by = User.objects.get(pk=request.session['userid'])
        transit_slip = TransitSlip(date=date, dst=dst, prepared_by=prepared_by)
        transit_slip.save()
        for ltr_id in ltr_ids:
            ltr = Letter.objects.get(pk=ltr_id)
            if not ltr.transit_slip:
                ltr.transit_slip = transit_slip
                ltr.save()
                candidate_ltr_count +=1
        if not candidate_ltr_count:
            transit_slip.delete()
            logger.info(f'Zero length Transit slip create prevented')
            err_msg = 'No suitable candidate ltr for transit slip.'
            return render(request, 'transit_slip/generic_error.html', {'err_msg':err_msg})


    return redirect('transit_slip_detail', transit_slip.pk)

class CurrentTransitSlipView(LoginRequiredMixin, UserPassesTestMixin, View):
    """ displays transit slip awaiting to despatch both originating and through """

    template = 'transit_slip/current_transit_slip.html'

    def test_func(self):
        user_type = self.request.user.profile.user_type
        if user_type == 'sc' or user_type == 'ad':
            return True
        else:
            return False

    def get(self, request):
        t_slips = TransitSlip.objects.filter(despatched_on=None, 
                prepared_by__profile__unit__sta_name=request.user.profile.unit.sta_name
                ).order_by('dst')
        through_pkgs = self.get_through_pkgs(request)
        summary_dict = self.get_summary(t_slips, through_pkgs)
        # print(summary_dict)
        context = {
            't_slips' : t_slips,
            'through_pkgs': through_pkgs,
            'summary_dict' : summary_dict,
        }
        return render(request, self.template, context)

    def get_through_pkgs(self, request):
        t_slips = TransitSlip.objects.filter(despatched_on__isnull=False,
        received_on__isnull=True)
        through_pkgs = []
        for t_slip in t_slips:
            if t_slip.through_sigcens:
                # print(t_slip.through_sigcens)
                through_sigcens = json.loads(t_slip.through_sigcens)
                for sigcen in through_sigcens:
                    sta = sigcen.get('sigcen')
                    if (sta == request.user.profile.unit.sta_name.sta_name
                        and not sigcen.get('despatched_at', None)
                    ):
                        through_pkgs.append(t_slip)
        return through_pkgs


    def get_summary(self, own_t_slips, through_pkgs):
        get_s_key = lambda x : x.dst.sta_name
        t_slips = list(own_t_slips) + through_pkgs
        t_slips.sort(key=get_s_key)

        ts_list =[]
        for t_slip in t_slips:
            ts_touple = (t_slip.dst.sta_name, t_slip.ltr_count(), t_slip.id)
            ts_list.append(ts_touple)
        key_f = lambda x: x[0]
        sum_dict = {}
        for key, group in itertools.groupby(ts_list, key_f):
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

class ThroughPkgView(LoginRequiredMixin, UserPassesTestMixin, View):
    """ receive through pkg in transit sigcens """
    template = 'transit_slip/through_pkg.html'
    def test_func(self):
        user_type = self.request.user.profile.user_type
        if user_type == 'sc' or user_type == 'ad':
            return True
        else:
            return False

    def get(self, request):
        return render(request, self.template, context= {})

    def post(self, request):
        ts_no = request.POST['ts_no']
        try:
            ts = TransitSlip.objects.get(pk=ts_no, despatched_on__isnull=False)
        except ObjectDoesNotExist:
            return HttpResponse("Not Found. Did other side despatched the Transit slip?",
                status=404)
        # not source or dst sta of the transit slip
        if ((ts.dst != request.user.profile.unit.sta_name) and
            (ts.prepared_by.profile.unit.sta_name != request.user.profile.unit.sta_name)):
            # through sigcen entry in transit_slip
            sigcen = str(request.user.profile.unit.sta_name)
            received_at = datetime.now().strftime("%d/%m/%Y %H:%M")
            received_by = request.user.username
            despatched_at = None
            receive_info = {'sigcen':sigcen, 'received_at': received_at, 'received_by': received_by,
                            'despatched_at': despatched_at}
            if not ts.through_sigcens:
                through_sigcens = []
                through_sigcens.append(receive_info)
            else:
                through_sigcens = json.loads(ts.through_sigcens)
                for sigcen in through_sigcens:
                    sta_name = sigcen.get('sigcen')
                    print(f'sta_name: ${sta_name}')
                    if sta_name == str(request.user.profile.unit.sta_name):
                        return HttpResponse("Duplicate receive not possible.", status=403)
                        
                through_sigcens.append(receive_info)
            ts.through_sigcens = json.dumps(through_sigcens)
            ts.save()

            ts_id = str(ts.id) 
            ts_from = str(ts.from_sta())
            ts_to = str(ts.dst)
            ts_date = (ts.date).strftime("%d-%m-%Y %H:%M")
            ts_info = {'ts_id':ts_id, 'ts_from': ts_from, 'ts_to': ts_to, 'ts_date': ts_date}   
            serialize_ts = json.dumps(ts_info)
            return HttpResponse( serialize_ts, status=200)
        else:
            return HttpResponse("This is not a through pkg", status=403)

def through_pkg_despatch(request):
    ts = TransitSlip.objects.get(pk=request.POST['ts_id'])
    through_sigcens = json.loads(ts.through_sigcens)
    for sigcen_info in through_sigcens:
        if sigcen_info.get('sigcen') == request.user.profile.unit.sta_name.sta_name:
            sigcen_info['despatched_at'] = datetime.now().strftime("%d/%m/%Y %H:%M")
            
            updated_info = json.dumps(through_sigcens)
            ts.through_sigcens = updated_info
            ts.save()
            return HttpResponse(status=201)
    return HttpResponse(status=404)

class OldTransitSlipView(LoginRequiredMixin, UserPassesTestMixin, View):
    """ displays transitslip which has already been despatched """

    template = 'transit_slip/old_transit_slip.html'

    def test_func(self):
        user_type = self.request.user.profile.user_type
        if user_type == 'sc' or user_type == 'ad':
            return True
        else:
            return False

    def get(self, request):
        stas = Sta.objects.all().order_by('sta_name')
        tr_slip_per_sta = []
        for sta in stas:
            tr_slips = TransitSlip.objects.filter(dst=sta, despatched_on__isnull=False,
                        prepared_by__profile__unit__sta_name=request.user.profile.unit.sta_name
                        ).order_by('-date')[:30]
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
@user_passes_test(utility.not_unit_clk_test)
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
@user_passes_test(utility.not_unit_clk_test)
def transit_slip_despatch(request, id):
    t_slip = TransitSlip.objects.get(pk=id)
    t_slip.despatched_on = datetime.today()
    t_slip.save()
    return redirect('current_transit_slip')

@login_required
@user_passes_test(utility.not_unit_clk_test)
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
@user_passes_test(utility.not_unit_clk_test)
def fetch_letter_json(request):
    """ fetch lettter on scanning the qr code """
    date = request.POST.get('date', None)
    u_string = request.POST.get('u_string', None)
    # if this call is for selecting ltr for transit slip
    ts_making = request.POST.get('ts_making', False)
    dst_sta = request.POST.get('dst_sta', False)

    try:
        if not ts_making:
            ltr = Letter.objects.get(u_string=u_string, date=date, 
                    from_unit__sta_name=request.user.profile.unit.sta_name, 
                    ltr_receipt__isnull=True)
        else:
            ltr = Letter.objects.get(u_string=u_string, date=date, 
                    from_unit__sta_name=request.user.profile.unit.sta_name,
                    ltr_receipt__isnull=False, to_unit__sta_name__sta_name=dst_sta,
                    transit_slip__isnull=True)
    except Exception as e:
        logger.warning(f'No Letter returned with given criteria: {e}')
        return HttpResponse(str(e),status=404)
    serialize_ltr = serializers.serialize("json", [ltr,], use_natural_foreign_keys=True)
    return HttpResponse(serialize_ltr)



class SearchLtrView(LoginRequiredMixin, UserPassesTestMixin, View):
    """
    Search letter for sigcen clk. also work as a parent view for other varient 
    of search.
    """
    template = 'transit_slip/search_ltr.html'

    def test_func(self):
        user_type = self.request.user.profile.user_type
        if user_type == 'sc' or user_type == 'ad':
            return True
        else:
            return False

    def get_unit_choices(self, request):
        units = utility.local_units(request)
        unit_choices = [(unit.pk, unit.unit_name) for unit in units]
        return unit_choices

    def get_user_unit(self, request):
        user_unit_id = request.session.get('unitid')
        try:
            user_unit = Unit.objects.get(pk=user_unit_id).unit_full_name
        except ObjectDoesNotExist as e:
            logger.warning(f'user unit full name could not retrive. {e}')
        return user_unit

    def get(self, request):
        unit_choices = self.get_unit_choices(request)
        user_unit = self.get_user_unit(request)
        context = {
            'unit_choices': unit_choices,
            'user_unit': user_unit,
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
                letters = Letter.objects.filter(from_unit=unit, date=search_date,)[:300]
            elif request.POST['unit-id']:
                unit = Unit.objects.get(pk=request.POST['unit-id'])
                letters = Letter.objects.filter(from_unit=unit)[:500]
            else:
                search_date = datetime.strptime(request.POST['search-date'], "%d-%m-%Y")
                # get letters of same sta of logged in user
                letters = Letter.objects.filter(date=search_date, 
                        from_unit__sta_name=request.user.profile.unit.sta_name)[:300]
            unit_choices = self.get_unit_choices(request)
            context = {
                'letters': letters,
                'unit_choices': unit_choices,
            }
            return render(request, self.template, context)

class SearchOutgoingLtrView(SearchLtrView):
    template = 'transit_slip/search_outgoing_ltr.html'

    def post(self, request):
        print(request.POST)
        if not (request.POST['unit-id'] or request.POST['search-date']):
            return redirect('search_outgoing_ltr')
        else:
            if request.POST['unit-id'] and request.POST['search-date']:
                unit = Unit.objects.get(pk=request.POST['unit-id'])
                search_date = datetime.strptime(request.POST['search-date'], "%d-%m-%Y")
                letters = OutGoingLetter.objects.filter(to_unit=unit, date=search_date)[:500]
            elif request.POST['unit-id']:
                unit = Unit.objects.get(pk=request.POST['unit-id'])
                letters = OutGoingLetter.objects.filter(to_unit=unit)[:500]
            else:
                search_date = datetime.strptime(request.POST['search-date'], "%d-%m-%Y")
                letters = OutGoingLetter.objects.filter(date=search_date)[:500]
            unit_choices = self.get_unit_choices(request)
            context = {
                'letters': letters,
                'unit_choices': unit_choices,
            }
            return render(request, self.template, context)

@login_required
def letter_delete_admin_view(request):
    """
    Allows admin to delete a dak regardless of their status 
    """
    # print(request.POST['ltr_id'])
    if request.method == 'POST':
        try:
            ltr = Letter.objects.get(pk=request.POST['ltr_id'])
            ltr.delete()
            return HttpResponse('true')
        except Exception:
            return HttpResponse('false')

################################################################################
############ views related to recepient sigcen while using api #################
################################################################################

class RemoteLtrView(View):
    """
    fetch letter from remote sigcen and save them to local DB.
    """
    def get(self, request):
        stas = Sta.objects.all().order_by('sta_name')
        domains = json.dumps(settings.DOMAINS)
        context = {
            'stas': stas,
            'domains': domains,
        }
        return render(request, 'transit_slip/get_remote_ltr.html', context)

    def post(self, request):
        from_units = request.POST.getlist('from_unit')
        to_units = request.POST.getlist('to_unit')
        dates = request.POST.getlist('date')
        codes = request.POST.getlist('code')
        ltr_nos = request.POST.getlist('ltr_no')
        ts_info = request.POST.get('ts-info')
        for idx, from_unit in enumerate(from_units):
            try:
                from_unit = Unit.objects.get(unit_code=from_units[idx])
                to_unit = Unit.objects.get(unit_code=to_units[idx])
            except ObjectDoesNotExist:
                err_msg = """One or more Unit was not found in local DB. Please add 
                    the appropriate unit with unit code to local DB."""
                return render(request, 'transit_slip/generic_error.html', {'err_msg':err_msg})
                
            date = datetime.strptime(dates[idx], '%d/%m/%Y')
            code = codes[idx]
            ltr_no = ltr_nos[idx]
            out_ltr = OutGoingLetter(from_unit=from_unit, to_unit=to_unit, date=date,
                        code=code, ltr_no=ltr_no, ts_info=ts_info,)
            try:
                out_ltr.full_clean()
            except ValidationError as e:
                err_msg = "DAK contain incorrect data." + str(e)
                return render(request, 'transit_slip/generic_error.html', {'err_msg':err_msg})
            out_ltr.save()
        info = "All DAK has been received successfully!!"
        return render(request, 'transit_slip/generic_info.html', { 'info': info })


def fetch_unit_names(request):
    unit_names = []
    err_msg = ''
    found_all_unit = True
    if request.method == "POST":
        unit_codes = request.POST.getlist('unit_codes[]')
        for unit_code in unit_codes:
            try:
                unit = Unit.objects.get(unit_code=unit_code)
            except (ObjectDoesNotExist, Unit.MultipleObjectsReturned) as e:
                found_all_unit = False
                err_msg = 'Unit not found or multiple unit returned.'
                err_msg += str(e)
                print(err_msg)
            else:
                unit_names.append(unit.unit_name)
    context = {
        'unit_names' : unit_names,
        'err_msg' : err_msg,
        'found_all_unit' : found_all_unit,
    }
    return JsonResponse(context, safe=False)


################################################################################
######################### end of api realted views  ############################
# ##############################################################################    

class DeliverLetterView(SearchLtrView):
    template = 'transit_slip/deliver_ltr.html'
    
    err_txt = None
    def get(self, request):
        unit_choices = utility.get_delivery_unit_choices(request)
        context = {
            'unit_choices': unit_choices,
        }
        return render(request, self.template, context)
    def post(self, request):
        err_txt = None
        letters = None
        unit = None
        null_return = False
        if not request.POST['unit-id']:
            err_txt = "No unit was selected!!"
        else:
            try:
                unit = Unit.objects.get(pk=request.POST.get('unit-id'))
                child_units = Unit.objects.filter(parent=unit)
                utility.process_local_ltrs(request, child_units) # save local ltrs from Letter to OutGoingLtr
                letters = OutGoingLetter.objects.filter(Q(to_unit__in=child_units),
                        delivery_receipt=None)
                null_return=True if letters.count()==0 else False
            except ObjectDoesNotExist as e:
                err_msg = "Unit not found." + str(e)
                return render(request, 'transit_slip/generic_error.html', {'err_msg':err_msg})
            
        unit_choices = utility.get_delivery_unit_choices(request)
        context = {
                'unit' : unit,
                'letters': letters,
                'unit_choices': unit_choices,
                'err_txt': err_txt,
                'null_return': null_return,
            }
        return render(request, self.template, context)

class SaveDeliveryView(View):
    def post(self, request):
        err_txt = None
        try:
            ltr_ids = request.POST.getlist("ltr-ids")
            letters = OutGoingLetter.objects.filter(pk__in=ltr_ids)
            print(letters)
        except ObjectDoesNotExist as e:
            err_txt = "Something went wrong while fetching unit." + str(e)
        if not err_txt:
            delivered_at = datetime.now()
            delivered_by = User.objects.get(pk=request.session['userid'])
            recepient_no = request.POST.get('army-no')
            recepient_rank = request.POST.get('rank')
            recepient_name = request.POST.get('name')
            derlivery_receipt = DeliveryReceipt(delivered_at=delivered_at, delivered_by=delivered_by,
                    recepient_no=recepient_no, recepient_rank=recepient_rank, recepient_name=recepient_name)
            try:
                derlivery_receipt.full_clean() # validate 
            except ValidationError as e:
                err_msg = "Validation failed on delivery receipt." + str(e)
                return render(request, 'transit_slip/generic_error.html', {'err_msg':err_msg})
            derlivery_receipt.save()
            derlivery_receipt.refresh_from_db()
            for ltr in letters:
                ltr.delivery_receipt = derlivery_receipt
                ltr.save()
            info = "Delivery data saved successfully."
            return render(request, "transit_slip/generic_info.html", {'info':info})
        else:
            return render(request, "transit_slip/generic_error.html", {'err_msg': err_txt})

def letter_local_deliver(request):
    """deliver local dak by unit DR and saved as delivered"""
    print('delivering local letter')
    if request.method == "POST":
        ltr_id = request.POST.get('ltr_id') 
        if ltr_id:
            ltr = Letter.objects.get(pk=ltr_id)
            ltr.delivered_locally = True
            ltr.save()
            return HttpResponse(status=204)
        return HttpResponse(status=404)


def letter_delivery_state(request, pk):
    if request.method == "GET":
        try:
            ltr = OutGoingLetter.objects.get(pk=pk)
        except ObjectDoesNotExist:
            err_txt = "Target DAK is not found. May have been removed."
            return render(request, "transit_slip/generic_error.html", {'err_msg': err_txt})
        context = {
            'letter': ltr,
        }
        return render(request, "transit_slip/letter_delivery_state.html", context )

class DeliverySetupView(LoginRequiredMixin, UserPassesTestMixin, View):
    """ setup which DR can receive DAK of which unit """

    template = "transit_slip/delivery_setup.html"
    def test_func(self):
        user = self.request.user.profile
        if user.user_type == 'ad':
            return True
        else:
            return False

    def get(self, request):
        units = utility.local_units(request)
        context = {
            'units' : units,
        }
        return render(request, self.template, context)


def get_parent(request):
    """ get parent unit of a given child unit id """
    if request.method == 'POST':
        child_id = int(request.POST.get('child_unit_id'))
        try:
            child_unit = Unit.objects.get(id=child_id)
        except ObjectDoesNotExist:
            return HttpResponse(status=404)
        parent_unit_name = child_unit.parent.unit_name
        return HttpResponse(parent_unit_name, status=200)

def change_parent(request):
    """ change parent of a given child for delivery """
    if request.method == 'POST':
        child_id = int(request.POST.get('child_unit_id'))
        parent_id = int(request.POST.get('parent_unit_id'))
        try:
            child_unit = Unit.objects.get(id=child_id)
            parent_unit = Unit.objects.get(id=parent_id)
            child_unit.parent = parent_unit
            child_unit.save()
        except ObjectDoesNotExist:
            return HttpResponse(status=404)
        return HttpResponse(status=204)



class OutStandingDakView(LoginRequiredMixin, UserPassesTestMixin, View):
    """ Displays dak waiting for delivery for a certain time """
    template = "transit_slip/outstanding_dak.html"
    def test_func(self):
        user = self.request.user.profile
        if user.user_type == 'sc':
            return True
        else:
            return False

    def get(self, request):
        context = {

        }
        return render (request, self.template, context)
    def post(self, request):
        days = int(request.POST.get('days-outstanding'))
        sta = request.user.profile.unit.sta_name
        if days:
            search_date = date.today() - timedelta(days=days)
            ltrs = OutGoingLetter.objects.filter(received_at__lte=search_date, delivery_receipt__isnull=True,
                to_unit__sta_name=sta).values('to_unit__unit_name').annotate(ltr_count=Count('to_unit'))
        else:
            ltrs = OutGoingLetter.objects.filter(delivery_receipt__isnull=True,
                to_unit__sta_name=sta).values('to_unit__unit_name').annotate(ltr_count=Count('to_unit'))
        context = {
            'ltrs' : ltrs,
        }
        return render(request, self.template, context)

def fetch_ltr(request):
    if request.method == 'POST':
        date_code = request.POST.get('date_code')
        try:
            date, code = date_code.split('-')
            date = datetime.strptime(date, "%d%m%Y")
        except ValueError as e:
            print(e)
        
        ltr = Letter.objects.get(u_string=code, date=date)
        print(ltr)

        serialize_ltr = serializers.serialize("json", [ltr], use_natural_foreign_keys=True)
        return HttpResponse(serialize_ltr)

def create_rtu_ltr(request):
    if request.method == 'POST':
        orig_pk = request.POST.get('orig_pk')
        ltr = Letter.objects.get(pk=orig_pk)
        rtu_ltr_no = 'RTU-' + ltr.ltr_no
        from_unit = request.user.profile.unit
        u_string = str(randint(10000, 99999))
        # qr_code_name = str(date.today().strftime("%d%m%Y")) + '-' + str(u_string)
        rtu_ltr = Letter(classification=ltr.classification, ltr_no=rtu_ltr_no,
            date=ltr.date, from_unit= from_unit, to_unit=ltr.from_unit,
             u_string=u_string, rtu_of=ltr, )
        rtu_ltr.save()
        # print(rtu_ltr)
        return HttpResponse('response', status=204)

def rtu_ltr_details(request):
    """ show details of original and rtu ltrs """
    rtu_ltr = Letter.objects.get(pk=request.POST.get('rtu-ltr-pk'))
    context = {
        'ltr': rtu_ltr,
    }

    return render(request, 'transit_slip/rtu_ltr_details.html', context)

class DakRtuView(LoginRequiredMixin, UserPassesTestMixin, View):
    """ Dak RTU in case of not possible delivery """
    template = "transit_slip/dak_rtu.html"
    def test_func(self):
        user = self.request.user.profile
        if user.user_type == 'sc':
            return True
        else:
            return False

    def get(self, request):
        unit = request.user.profile.unit
        rtu_ltrs = Letter.objects.filter(from_unit=unit, rtu_of__isnull=False)
        context = {
            'letters' : rtu_ltrs, 
        }
        return render(request, self.template, context)

    def post(self, request):
        date_code = request.POST.get('rtu-dak-code')
        try:
            date, code = date_code.split('-')
            date = datetime.strptime(date, "%d%m%Y")
        except ValueError as e:
            print(e)
        
        ltr = Letter.objects.get(u_string=code, date=date)
        print(ltr)

        context = {

        }
        return render(request, self.template, context)

class MiscAdminInfo(LoginRequiredMixin, UserPassesTestMixin, View):
    """ Display generated DAK statistics info for site admin"""
    template = "transit_slip/misc_admin_info.html"
    def test_func(self):
        user = self.request.user
        if user.is_staff == True:
            return True
        else:
            return False

    def get(self, request):
        todays_ltr_count = Letter.objects.filter(created_at__gte=date.today()).count()
        last_day_ltr_count = Letter.objects.filter(created_at__gte=date.today()-timedelta(days=1)).count()
        last_wk_ltr_count = Letter.objects.filter(created_at__gte=date.today()-timedelta(days=7)).count()
        last_day_ltr_gp_by_unit = Letter.objects.filter(created_at__gte=date.today()-timedelta(days=1
            )).values('from_unit__unit_name').annotate(ltr_count=Count('from_unit')).order_by('-ltr_count')[:30]
        last_day_ltr_gp_by_sta = Letter.objects.filter(created_at__gte=date.today()-timedelta(days=1
            )).values('from_unit__sta_name__sta_name').annotate(ltr_count=Count('from_unit')).order_by('-ltr_count')
        last_wk_ltr_gp_by_unit = Letter.objects.filter(created_at__gte=date.today()-timedelta(days=7
            )).values('from_unit__unit_name').annotate(ltr_count=Count('from_unit')).order_by('-ltr_count')[:30]
        last_wk_ltr_gp_by_sta = Letter.objects.filter(created_at__gte=date.today()-timedelta(days=7
            )).values('from_unit__sta_name__sta_name').annotate(ltr_count=Count('from_unit')).order_by('-ltr_count')
        context = {
            'todays_ltr_count': todays_ltr_count,
            'last_day_ltr_count': last_day_ltr_count,
            'last_wk_ltr_count': last_wk_ltr_count,
            'last_day_ltr_gp_by_unit': last_day_ltr_gp_by_unit,
            'last_day_ltr_gp_by_sta': last_day_ltr_gp_by_sta,
            'last_wk_ltr_gp_by_unit': last_wk_ltr_gp_by_unit,
            'last_wk_ltr_gp_by_sta': last_wk_ltr_gp_by_sta,
        }
        return render(request, self.template, context)

class MiscAdminInfoTs(MiscAdminInfo):
    """ displays few latest transit slip with current status  """
    template = "transit_slip/misc_admin_info_ts.html"
    def get(self, request):
        ts_list = TransitSlip.objects.filter(date__gte=date.today()-timedelta(days=10)
        ).order_by('-id')[:200]
        ts_display_list = []
        for ts in ts_list:
            if ts.through_sigcens:
                through_sigcen = json.loads(ts.through_sigcens)
            else:
                through_sigcen = None
            ts_display = utility.TsDisplay(ts.id, ts.date, ts.dst, ts.prepared_by,
                ts.despatched_on, ts.received_on, through_sigcen)
            ts_display_list.append(ts_display)
        # print(ts_display_list[3].through_sigcen[0].get('sigcen'))
        # print(type(ts_display_list[3].date))
        context = {
            'ts_display_list': ts_display_list,
        }

        return render(request, self.template, context)

class MiscAdminInfoDakByDate(MiscAdminInfo):
    """ displays dak statistics by date of a selected sta """
    template = "transit_slip/misc_admin_info_dak_by_date.html"


    def get(self, request):
        

        context = {

        }
        return render(request, self.template, context)