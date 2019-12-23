
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    path('', views.Home.as_view(), name= 'home'),
    path('create_user', views.create_user, name= 'create_user'),

    # unit user
    path('new_letter/', views.LetterView.as_view(), name= 'new_letter'),
    path('letter_list_inhouse/', views.letter_list_inhouse, name= 'letter_list_inhouse'),
    path('letter_list_despatched/', views.letter_list_despatched, name= 'letter_list_despatched'),
    path('letter_delete/<str:ltr_no>', views.letter_delete, name= 'letter_delete'),
    # path('letter/', views.letter_details, name= 'letter_details'),
    # path('letter/<int:pk>', views.letter_details, name= 'letter_details'),
    path('label/', views.label, name= 'label'),
    path('label/<int:pk>', views.label, name= 'label'),
    path('label_bulk/<str:ltr_no>', views.label_bulk, name= 'label_bulk'),
    # sigcen user
    path('dak_in_manual', views.DakInManualView.as_view(), name= 'dak_in_manual'),
    path('dak_in_scan', views.DakInScanView.as_view(), name= 'dak_in_scan'),
    path('dak_receive', views.DakReceive.as_view(), name= 'dak_receive'),
    path('create_transit_slip', views.CreateTransitSlipView.as_view(), name= 'create_transit_slip'),
    path('current_transit_slip', views.CurrentTransitSlipView.as_view(), name= 'current_transit_slip'),
    path('transit_slip_ltrs', views.transit_slip_ltrs, name= 'transit_slip_ltrs'),
    path('old_transit_slip', views.OldTransitSlipView.as_view(), name= 'old_transit_slip'),
    path('transit_slip_detail/<int:id>', views.TransitSlipDetailView.as_view(), name= 'transit_slip_detail'),
    path('transit_slip_print/<int:id>', views.TransitSlipPrintView.as_view(), name= 'transit_slip_print'),
    path('transit_slip_despatch/<int:id>', views.transit_slip_despatch, name= 'transit_slip_despatch'),
    path('test', views.test_view, name= 'test_view'),

    path('fetch_letter_json', views.fetch_letter_json, name= 'fetch_letter_json'),
    
    path('add_sta', views.add_new_sta, name= 'add_sta'),
    path('unit', views.UnitView.as_view(), name= 'unit'),
    # path('unit/<int:unit_id>', views.UnitView.as_view(), name= 'unit'),
]
if settings.DEBUG:
    urlpatterns = urlpatterns + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)