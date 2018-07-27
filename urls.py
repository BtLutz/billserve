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
    re_path(r'^states/$', views.StateList.as_view(), name='state-list'),
    re_path(r'^states/(?P<pk>[0-9]+)/$', views.StateDetail.as_view(), name='state-detail'),
    re_path(r'^districts/$', views.DistrictList.as_view(), name='district-list'),
    re_path(r'^districts/(?P<pk>[0-9]+)/$', views.DistrictDetail.as_view(), name='district-detail'),
    re_path(r'^legislators/$', views.LegislatorList.as_view(), name='legislator-list'),
    re_path(r'^representatives/$', views.RepresentativeList.as_view(), name='representative-list'),
    re_path(r'^representatives/(?P<pk>[0-9]+)/$', views.RepresentativeDetail.as_view(), name='representative-detail'),
    re_path(r'^senators/$', views.SenatorList.as_view(), name='senator-list'),
    re_path(r'^senators/(?P<pk>[0-9]+)/$', views.SenatorDetail.as_view(), name='senator-detail'),
    re_path(r'^bills/$', views.BillList.as_view(), name='bill-list'),
    re_path(r'^bills/(?P<pk>[0-9]+)/$', views.BillDetail.as_view(), name='bill-detail'),
    re_path(r'^legislative-subjects/$', views.LegislativeSubjectList.as_view(), name='legislativesubject-list'),
    re_path(r'^legislative-subjects/(?P<pk>[0-9]+)/$', views.LegislativeSubjectDetail.as_view(),
            name='legislativesubject-detail'),
    re_path(r'^policy-areas/$', views.PolicyAreaList.as_view(), name='policyarea-list'),
    re_path(r'^policy-areas/(?P<pk>[0-9]+)/$', views.PolicyAreaDetail.as_view(), name='policyarea-detail')
])
