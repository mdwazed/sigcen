from django import forms
from django.db import models
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
# from django.forms import Form, ModelForm
from transit_slip.models import Letter, Unit, user_type_choices, Sta

from datetime import date, datetime


class LetterForm(forms.ModelForm):
    addr_line_1 = forms.CharField(widget=forms.TextInput(attrs={'size': '60'}), required=False)
    ltr_no = forms.CharField(widget=forms.TextInput(attrs={'size':'30', 'class':'inputText'}))
    to_units = forms.CharField(max_length=500) #uses slect2 for choices
    date = forms.DateField()
    
    class Meta:
        model = Letter
        fields = ['addr_line_1','addr_line_2', 'ltr_no', 'to_units', 'date', 'classification',]

class StaForm(forms.ModelForm):

    class Meta:
        model = Sta
        fields = '__all__'

class CreateUserForm(UserCreationForm):

    unit = forms.ChoiceField()
    user_type = forms.ChoiceField(choices=user_type_choices )
    def __init__(self, *args, **kwargs):
        sta = kwargs.pop('sta')
        super(CreateUserForm, self).__init__(*args, **kwargs)
        choices = [(unit.pk, unit.unit_name) for unit in Unit.objects.filter(sta_name=sta)]
        self.fields['unit'].choices = choices

    class Meta:
        model = User
        fields = ('username', 'password1', 'password2', 'first_name', 'last_name', 'unit', 'user_type' )

class DakInForm(forms.Form):
    """
    In dak filtering form. use for receiving dak at counter room
    """
    unit = forms.ChoiceField()
    date = forms.DateField()
    code = forms.CharField(required=False)
    def __init__(self, *args, **kwargs):
        sta = kwargs.pop('sta')
        super(DakInForm, self).__init__(*args, **kwargs)
        choices = [(unit.pk, unit.unit_name) for unit in Unit.objects.filter(sta_name=sta)]
        self.fields['unit'].choices = choices
        self.fields['unit'].initial = '0'
        # self.fields['code'].max_length=3
        self.fields['date'].widget.attrs['class'] = 'datepicker'
        self.fields['date'].widget.attrs['autocomplete'] = 'off'
        
