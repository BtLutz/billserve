from django.shortcuts import render
from django.http import HttpResponse, Http404

from rest_framework.reverse import reverse
from rest_framework import generics
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView

from billserve.models import *
from billserve.serializers import *
from billserve.enumerations import LegislativeSubjectActivityType
from billserve.tasks import update

import urllib3
import certifi
import json
import logging
import xmltodict
import datetime
from pytz import utc

# Note: Possible ways to make money...
# 1. Sell wholesale yearly access to congresspeople (i.e. $20K for unlimited queries)
# 2. Sell per-unit queries (i.e. $0.05 per record accessed / $5 per query / etc.)

# Process:
# 1. Roll Call, Politico, Glenn Kessler @ WP would know if something like this has already been done
# 2. Voting records

# Features:
# 1. Legislator reference page. Fancy vote counter

# Important references:
# 1. House of Representative voting example: http://clerk.house.gov/evs/2018/roll297.xml
# 2. Senate voting example: https://www.senate.gov/legislative/LIS/roll_call_votes/vote1141/vote_114_1_00067.xml
# It seems like the House of Representatives votes on a lot more bills than the senate...
# TODO: Implement API tokens. A special token should be allocated to allow access to the protected /update endpoint.
# Everyone else should get generic tokens that allow access to the API methods.
# TODO: Got an exception when parsing the 987 bill. The exception happened when I tried to save a char field that was
# longer than 50 characters. It happened when I was parsing live on Heroku.


@api_view(['GET'])
def api_root(request, format=None):
    return Response({
        'parties': reverse('party-list', request=request, format=format),
        # 'legislativeBodies': reverse('legislative-bodies-list', request=request, format=format),
        'districts': reverse('district-list', request=request, format=format),
        # 'legislators': reverse('legislator-list', request=request, format=format),
        'senators': reverse('senator-list', request=request, format=format),
        'representatives': reverse('representative-list', request=request, format=format),
        'bills': reverse('bill-list', request=request, format=format),
        # 'committees': reverse('committee-list', request=request, format=format),
        'policyAreas': reverse('policyarea-list', request=request, format=format),
        'legislativeSubjects': reverse('legislativesubject-list', request=request, format=format),
        'states': reverse('state-list', request=request, format=format),
    })


class PartyList(generics.ListAPIView):
    """
    List all parties.
    """
    queryset = Party.objects.all()
    serializer_class = PartyShortSerializer


class PartyDetail(generics.RetrieveAPIView):
    """
    Retrieve a party instance.
    """
    queryset = Party.objects.all()
    serializer_class = PartySerializer


class StateList(generics.ListAPIView):
    """
    List all states.
    """
    queryset = State.objects.all()
    serializer_class = StateShortSerializer


class StateDetail(generics.RetrieveAPIView):
    """
    Retrieve a state instance.
    """
    queryset = State.objects.all()
    serializer_class = StateSerializer


class DistrictList(generics.ListAPIView):
    """
    List all districts.
    """
    queryset = District.objects.all()
    serializer_class = DistrictShortSerializer


class DistrictDetail(generics.RetrieveAPIView):
    """
    Retrieve a district instance.
    """
    queryset = District.objects.all()
    serializer_class = DistrictSerializer


class LegislatorList(generics.ListAPIView):
    """
    List all legislators.
    """
    queryset = Legislator.objects.all()
    serializer_class = LegislatorListSerializer


class RepresentativeList(generics.ListAPIView):
    """
    List all representatives.
    """
    queryset = Representative.objects.all()
    serializer_class = RepresentativeShortSerializer


class RepresentativeDetail(generics.RetrieveAPIView):
    """
    Retrieve a representative instance.
    """
    queryset = Representative.objects.all()
    serializer_class = RepresentativeSerializer


class SenatorList(generics.ListAPIView):
    """
    List all senators.
    """
    queryset = Senator.objects.all()
    serializer_class = SenatorShortSerializer


class SenatorDetail(generics.RetrieveAPIView):
    """
    Retrieve a senator instance.
    """
    queryset = Senator.objects.all()
    serializer_class = SenatorSerializer


class BillList(generics.ListAPIView):
    """
    List all bills.
    """
    queryset = Bill.objects.all()
    serializer_class = BillShortSerializer


class BillDetail(generics.RetrieveAPIView):
    """
    Retrieve a bill instance.
    """
    queryset = Bill.objects.all()
    serializer_class = BillSerializer


class LegislativeSubjectList(generics.ListAPIView):
    """
    List all legislative subjects.
    """
    queryset = LegislativeSubject.objects.all()
    serializer_class = LegislativeSubjectShortSerializer


class LegislativeSubjectDetail(generics.RetrieveAPIView):
    """
    Retrieve a legislative subject instance.
    """
    queryset = LegislativeSubject.objects.all()
    serializer_class = LegislativeSubjectSerializer


class PolicyAreaList(generics.ListAPIView):
    """
    List all policy areas.
    """
    queryset = PolicyArea.objects.all()
    serializer_class = PolicyAreaShortSerializer


class PolicyAreaDetail(generics.RetrieveAPIView):
    """
    Retrieve a policy area instance.
    """
    queryset = PolicyArea.objects.all()
    serializer_class = PolicyAreaSerializer


def update_view(request):
    """
    Updates the database with new data from govinfo.
    :param request: A request object
    """

    origin_url = 'https://www.govinfo.gov/bulkdata/BILLSTATUS/115/s/BILLSTATUS-115s119.xml'
    update.delay(origin_url=origin_url)
    return HttpResponse(status=200, content='OK: Update queued.')

