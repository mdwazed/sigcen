from django.db import models
from django.contrib.auth.models import User
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from datetime import date, datetime

# Create your models here.

user_type_choices = {
        ('uc', 'Unit clk'),
        ('ad', 'Admin'),
        ('sc', 'Sigcen clk'),
    }

    
class Sta(models.Model):
    sta_name = models.CharField(max_length=4)

    def __str__(self):
        return self.sta_name

class Unit(models.Model):
    unit_name = models.CharField(max_length=50)
    sta_name = models.ForeignKey(Sta, on_delete=models.PROTECT,)

    def __str__(self):
        return self.unit_name

    def natural_key(self):
        return(self.unit_name)

class TransitSlip(models.Model):
    date = models.DateTimeField()
    dst = models.ForeignKey(Sta, on_delete=models.PROTECT)
    prepared_by = models.ForeignKey(User, on_delete=models.PROTECT)
    despatched_on = models.DateField(null=True, blank=True, )
    received_on = models.DateField(null=True, blank=True)

    def ltr_count(self):
        ltr_count = Letter.objects.filter(transit_slip=self).count()
        return ltr_count

class Profile(models.Model):
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    unit = models.ForeignKey(Unit, on_delete=models.PROTECT, blank=True, null=True)
    user_type = models.CharField(max_length=2, blank=True, null=True,
                choices=user_type_choices, default='uc')

    def __str__(self):
        return self.user.username
    def get_user_type(self):
        return self.user_type

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()
    
class Letter(models.Model):
    addr_line_1 = models.CharField(max_length=50, blank=True, null=True)
    ltr_no = models.CharField(max_length=50)
    date = models.DateField()
    from_unit = models.ForeignKey(Unit, on_delete=models.PROTECT, related_name='from_unit',)
    to_unit = models.ForeignKey(Unit, on_delete=models.PROTECT, related_name='to_unit',)
    # to_unit = models.ManyToManyField(Unit, related_name='to_unit')
    u_string = models.CharField(max_length=5)
    qr_image_url = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    received_by_sigcen = models.BooleanField(default=False)
    received_at_sigcen = models.DateTimeField(null=True)
    spl_pkg = models.BooleanField(default=False)
    despatched_at = models.DateTimeField(null=True)
    transit_slip = models.ForeignKey(TransitSlip, on_delete=models.SET_NULL, blank=True, null=True)

    class Meta:
        unique_together = ('date', 'u_string',)

    def __str__(self):
        return (f'letter from {self.from_unit} u_string{self.u_string}')

    def get_absolute_url(self):
        return (f'/letter/{self.pk}')

