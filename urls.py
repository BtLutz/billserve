from django.urls import path, re_path
from django.conf.urls import url
from . import views


urlpatterns = [
    path('', views.index, name='index'),
    path('update', views.update, name='update'),
    re_path(r'^bills/$', views.bill_list),
    re_path(r'^bills/(?P<congress>\d+)/$', views.bill_congress_list),
    re_path(r'^bills/(?P<congress>\d+)/(?P<bill_number>\d+)/$', views.bill_congress_detail),
    re_path(r'^bills/subject/(?P<legislative_subject_pk>\d+)/$', views.bill_subject_list),
    re_path(r'^bills/subject/(?P<legislative_subject_pk>\d+)/(?P<congress>\d+)/$', views.bill_subject_congress_list),
    re_path(r'^subjects/$', views.subject_list)
]