from django.contrib import admin
from transit_slip.models import Unit, Sta, Letter, Profile

# Register your models here.
admin.site.register(Unit)
admin.site.register(Sta)
admin.site.register(Letter)
admin.site.register(Profile)
