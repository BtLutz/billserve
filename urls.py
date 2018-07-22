from django.urls import path, re_path
from django.conf.urls import url, include

from rest_framework.urlpatterns import format_suffix_patterns
from . import views

# Thoughts:
# - It would be really interesting to experiment with advanced asynchronous design.
#   For instance, it sucks to have to wait for my whole Facebook feed to load before I can scroll.
#   Instead of requesting all bills a senator has co-sponsored at once (could be thousands), it'd be cool to get a small
#   data dump containing the basic data about the bill, display that to the user, and then make individual asynchronous
#   requests back to the server for each bill's full set of data. When I get a request back, I populate it.
#   It'd work kind of like the volley library for Android.

# API endpoints
urlpatterns = format_suffix_patterns([
    path('', views.api_root),
    path('update', views.update, name='update'),
    re_path(r'^parties/$', views.PartyList.as_view(), name='party-list'),
    re_path(r'^parties/(?P<pk>[0-9]+)/$', views.PartyDetail.as_view(), name='party-detail'),
    re_path(r'^representatives/$', views.RepresentativeList.as_view(), name='representative-list'),
    re_path(r'^representatives/(?P<pk>[0-9]+)/$', views.RepresentativeDetail.as_view(), name='representative-detail'),
    re_path(r'^senators/$', views.SenatorList.as_view(), name='senator-list'),
    re_path(r'^senators/(?P<pk>[0-9]+)/$', views.SenatorDetail.as_view(), name='senator-detail'),
    re_path(r'^bills/$', views.BillList.as_view(), name='bill-list'),
    re_path(r'^bills/(?P<pk>[0-9]+)/$', views.BillDetail.as_view(), name='bill-detail')
])
