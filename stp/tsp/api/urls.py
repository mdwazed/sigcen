
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    path('test_view/', views.test_view, name= 'test_view'),
    path('letters/', views.test_view, name= 'test_view'),
    path('ts_detail/<int:pk>', views.transit_slip_detail, name= 'transit_slip_detail'),
]
