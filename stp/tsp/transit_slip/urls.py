
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    path('not_auth_view/', views.not_auth_view, name= 'not_auth_view'),
    path('', views.Home.as_view(), name= 'home'),
    
    # user
    path('user_list/', views.UserListView.as_view(), name= 'user_list'),
    path('create_user/', views.UserCreateView.as_view(), name= 'create_user'),
    path('update_user_info/<int:pk>/', views.UserUpdateView.as_view(), name= 'update_user_info'),
    path('user_password_change', views.UserPasswordChangeView.as_view(), name= 'user_password_change'),
    path('reset_user_password/<int:pk>/', views.ResetUserPasswordView.as_view(), name= 'reset_user_password'),
    path('delete_user/', views.DeleteUserView.as_view(), name= 'delete_user'),
    path('change_admin_aor/', views.ChangeAdminAorView.as_view(), name= 'change_admin_aor'),
    # Letter
    path('new_letter/', views.LetterView.as_view(), name= 'new_letter'),
    path('new_do/', views.DoView.as_view(), name= 'new_do'),
    path('letter_list/<catagory>/', views.LetterListView.as_view(), name= 'letter_list'),
    path('letter_delete/', views.letter_delete, name= 'letter_delete'),
    path('search_ltr', views.SearchLtrView.as_view(), name= 'search_ltr'),
    path('letter_state/<int:pk>', views.letter_state, name= 'letter_state'),
    path('label/', views.label, name= 'label'),
    path('label/<int:pk>/', views.label, name= 'label'),
    path('label_bulk/<str:ltr_no>/<str:date_str>', views.label_bulk, name= 'label_bulk'),
    path('label_do/<int:pk>', views.label_do, name= 'label_do'),
    # sigcen user
    path('receipt_list', views.receipt_list, name= 'receipt_list'),
    path('receive_receipt/<int:pk>', views.receive_receipt, name= 'receive_receipt'),
    path('dak_in_manual', views.DakInManualView.as_view(), name= 'dak_in_manual'),
    path('dak_in_scan', views.DakInScanView.as_view(), name= 'dak_in_scan'),
    path('dak_receive', views.DakReceive.as_view(), name= 'dak_receive'),
    path('create_transit_slip', views.CreateTransitSlipView.as_view(), name= 'create_transit_slip'),
    path('create_transit_slip_manually', views.CreateTransitSlipManualView.as_view(), name= 'create_transit_slip_manually'),
    path('current_transit_slip', views.CurrentTransitSlipView.as_view(), name= 'current_transit_slip'),
    path('transit_slip_ltrs', views.transit_slip_ltrs, name= 'transit_slip_ltrs'),
    path('old_transit_slip', views.OldTransitSlipView.as_view(), name= 'old_transit_slip'),
    path('transit_slip_detail/<int:id>', views.TransitSlipDetailView.as_view(), name= 'transit_slip_detail'),
    path('create_spl_pkg', views.CreateSplPkgView.as_view(), name= 'create_spl_pkg'),
    path('generate_spl_pkg_ts', views.generate_spl_pkg_ts, name= 'generate_spl_pkg_ts'),
    path('transit_slip_despatch/<int:id>', views.transit_slip_despatch, name= 'transit_slip_despatch'),
    path('ts_rcv_update', views.ts_rcv_update, name= 'ts_rcv_update'),
    path('fetch_letter_json', views.fetch_letter_json, name= 'fetch_letter_json'),
    path('outstanding_dak', views.OutStandingDakView.as_view(), name= 'outstanding_dak'),
    # outgoing ltr
    path('remote_ltr', views.RemoteLtrView.as_view(), name= 'remote_ltr'), # use in api call
    path('fetch_unit_names/', views.fetch_unit_names, name= 'fetch_unit_names'), # used in API call
    path('search_outgoing_ltr/', views.SearchOutgoingLtrView.as_view(), name= 'search_outgoing_ltr'),
    path('deliver_ltr/', views.DeliverLetterView.as_view(), name= 'deliver_ltr'),
    path('letter_local_deliver/', views.letter_local_deliver, name= 'letter_local_deliver'),
    path('save_delivery/', views.SaveDeliveryView.as_view(), name= 'save_delivery'),
    path('letter_delivery_state/<int:pk>', views.letter_delivery_state, name= 'letter_delivery_state'),
    path('dak_rtu/', views.DakRtuView.as_view(), name= 'dak_rtu'),
    path('fetch_ltr/', views.fetch_ltr, name= 'fetch_ltr'),
    path('create_rtu_ltr/', views.create_rtu_ltr, name= 'create_rtu_ltr'),
    path('rtu_ltr_details/', views.rtu_ltr_details, name= 'rtu_ltr_details'),
    path('delivery_setup/', views.DeliverySetupView.as_view(), name= 'delivery_setup'),
    path('get_parent/', views.get_parent, name= 'get_parent'),
    path('change_parent/', views.change_parent, name= 'change_parent'),
    # through packet
    path('through_pkg', views.ThroughPkgView.as_view(), name= 'through_pkg'),
    path('through_pkg_despatch', views.through_pkg_despatch, name= 'through_pkg_despatch'),
    # unit related path
    path('add_sta', views.StaAddView.as_view(), name= 'add_sta'),
    path('update_sta/<int:pk>', views.UpdateStaView.as_view(), name= 'update_sta'),
    path('unit_list', views.UnitListView.as_view(), name= 'unit_list'),
    path('create_unit/', views.UnitCreateView.as_view(), name= 'create_unit'),
    path('update_unit/<int:pk>', views.UnitUpdateView.as_view(), name= 'update_unit'),
    path('delete_unit/<int:pk>', views.UnitDeleteView.as_view(), name= 'delete_unit'),
    path('letter_delete_admin', views.letter_delete_admin_view, name= 'letter_delete_admin'),
    #statics and analysis
    path('misc_admin_info_general/', views.MiscAdminInfo.as_view(), name= 'misc_admin_info_general'),
    path('misc_admin_info_ts/', views.MiscAdminInfoTs.as_view(), name= 'misc_admin_info_ts'),
    path('misc_admin_info_dak_by_date/', views.MiscAdminInfoDakByDate.as_view(), name= 'misc_admin_info_dak_by_date'),
]
