from django.db import models
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from datetime import date, datetime


# Create your models here.
# types of users. define access permission based on usr type.
user_type_choices = {
        ('uc', 'Unit clk'),
        ('ad', 'Admin'),
        ('sc', 'Sigcen clk'),
    }
# letter classification to choose620

classification_choices = {
    ('rs', 'Restricted'),
    ('cf', 'Confidential'),
    ('sc', 'Secret'),
    ('ts', 'Top Secret'),
    ('uc', 'Unclass'),
}

    
class Sta(models.Model):
    sta_name = models.CharField(max_length=4)
    sta_full_name = models.CharField(max_length=50, null=True, blank=True)

    def __str__(self):
        return self.sta_name
    
    def natural_key(self):
        return(self.sta_name)

class Unit(models.Model):
    unit_name = models.CharField(max_length=50)
    unit_full_name = models.CharField(max_length=100, null=True, blank=True)
    sta_name = models.ForeignKey(Sta, on_delete=models.PROTECT,)
    unit_code = models.IntegerField(default=0)

    def __str__(self):
        return self.unit_name

    def natural_key(self):
        return(self.unit_name)

class TransitSlip(models.Model):
    date = models.DateTimeField()
    dst = models.ForeignKey(Sta, on_delete=models.PROTECT)
    prepared_by = models.ForeignKey(User, on_delete=models.PROTECT)
    despatched_on = models.DateField(null=True, blank=True, )
    received_on = models.DateTimeField(null=True, blank=True)

    def ltr_count(self):
        ltr_count = Letter.objects.filter(transit_slip=self).count()
        return ltr_count

class LetterReceipt(models.Model):
    received_at_sigcen = models.DateTimeField(null=True)
    received_by = models.ForeignKey(User, on_delete=models.PROTECT)

    def get_ltr_count(self):
        ltr_count = Letter.objects.filter(ltr_receipt=self).count()
        return ltr_count

class DeliveryReceipt(models.Model):
    delivered_at = models.DateTimeField(null=True)
    delivered_by = models.ForeignKey(User, on_delete=models.PROTECT)
    recepient_no = models.CharField(max_length=100, null=True, blank=True)
    recepient_rank = models.CharField(max_length=100, null=True, blank=True)
    recepient_name = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return(f'{self.delivered_by}--{self.recepient_name}')

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
    letter_type = models.CharField(max_length=3, default='reg') # reg or do letter. decide in views
    classification = models.CharField(choices=classification_choices, default='rs', max_length=2, blank=True, null=True )
    addr_line_1 = models.CharField(max_length=100, blank=True, null=True) #name of receipient
    addr_line_2 = models.CharField(max_length=50, blank=True, null=True) # appt of receipient
    ltr_no = models.CharField(max_length=50)
    date = models.DateField()
    from_unit = models.ForeignKey(Unit, on_delete=models.PROTECT, related_name='from_unit',)
    to_unit = models.ForeignKey(Unit, on_delete=models.PROTECT, related_name='to_unit',)
    u_string = models.CharField(max_length=5)
    qr_image_url = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    spl_pkg = models.BooleanField(default=False)
    ltr_receipt = models.ForeignKey(LetterReceipt, on_delete=models.SET_NULL, null=True)
    # despatched_at = models.DateTimeField(null=True)
    transit_slip = models.ForeignKey(TransitSlip, related_name='ltrs', on_delete=models.SET_NULL, blank=True, null=True)

    class Meta:
        unique_together = ('date', 'u_string',)

    def __str__(self):
        return (f'letter from {self.from_unit} u_string{self.u_string}')

    def get_absolute_url(self):
        return (f'/letter/{self.pk}')

    def get_current_status(self):
        try:
            dst_ltr = OutGoingLetter.objects.get(code=self.u_string, date=self.date)
        except ObjectDoesNotExist:
            dst_ltr = None

        if not self.ltr_receipt:
            return "In Unit"
        elif not self.transit_slip:
            return "In Sigcen"
        elif not self.transit_slip.received_on:
            return "In Transit"
        if dst_ltr:
            if self.transit_slip.received_on and not dst_ltr.delivery_receipt:
                return "DST SIGCEN"
            elif dst_ltr.delivery_receipt:
                return "Delivered"
        else:
            return "Unknown"

class OutGoingLetter(models.Model):
    from_unit = models.ForeignKey(Unit, on_delete=models.PROTECT, related_name='orig_unit')
    to_unit = models.ForeignKey(Unit, on_delete=models.PROTECT, related_name='dst_unit')
    date = models.DateField()
    code = models.CharField(max_length=5)
    ltr_no = models.CharField(max_length=50)
    ts_info = models.CharField(max_length=10)
    received_at = models.DateTimeField(auto_now_add=True)
    delivery_receipt = models.ForeignKey(DeliveryReceipt, on_delete=models.SET_NULL, null=True,
                            blank=True, related_name='ltrs')
    class Meta:
        unique_together = ('date', 'code',)
    def __str__(self):
        return (f'{self.from_unit}--{self.to_unit}--{self.ts_info}--{self.code}')