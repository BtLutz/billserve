from django.urls import path, re_path
from django.conf.urls import url, include

from rest_framework.urlpatterns import format_suffix_patterns
from . import views


# API endpoints
urlpatterns = format_suffix_patterns([
    path('', views.api_root),
    path('update', views.update_view, name='update'),
    path('rebuild-derived-data', views.rebuild_derived_data_view, name='rebuild-derived-data'),
    re_path(r'^parties/$', views.PartyList.as_view(), name='party-list'),
    re_path(r'^states/$', views.StateList.as_view(), name='state-list'),
    re_path(r'^districts/$', views.DistrictList.as_view(), name='district-list'),
    re_path(r'^legislators/$', views.LegislatorList.as_view(), name='legislator-list'),
    re_path(r'^representatives/$', views.RepresentativeList.as_view(), name='representative-list'),
    re_path(r'^senators/$', views.SenatorList.as_view(), name='senator-list'),
    re_path(r'^bills/$', views.BillList.as_view(), name='bill-list'),
    re_path(r'^legislative-subjects/$', views.LegislativeSubjectList.as_view(), name='legislativesubject-list'),
    re_path(r'^policy-areas/$', views.PolicyAreaList.as_view(), name='policyarea-list'),
    re_path(r'^parties/(?P<pk>[0-9]+)/$', views.PartyDetail.as_view(), name='party-detail'),
    re_path(r'^states/(?P<pk>[0-9]+)/$', views.StateDetail.as_view(), name='state-detail'),
    re_path(r'^districts/(?P<pk>[0-9]+)/$', views.DistrictDetail.as_view(), name='district-detail'),
    re_path(r'^representatives/(?P<pk>[0-9]+)/$', views.RepresentativeDetail.as_view(), name='representative-detail'),
    re_path(r'^senators/(?P<pk>[0-9]+)/$', views.SenatorDetail.as_view(), name='senator-detail'),
    re_path(r'^bills/(?P<pk>[0-9]+)/$', views.BillDetail.as_view(), name='bill-detail'),
    re_path(r'^legislative-subjects/(?P<pk>[0-9]+)/$', views.LegislativeSubjectDetail.as_view(),
            name='legislativesubject-detail'),
    re_path(r'^policy-areas/(?P<pk>[0-9]+)/$', views.PolicyAreaDetail.as_view(), name='policyarea-detail')
])
