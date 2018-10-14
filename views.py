from django.shortcuts import render
from django.http import HttpResponse, Http404

from rest_framework.reverse import reverse
from rest_framework import generics
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView

from billserve.serializers import *
from billserve.tasks import update, rebuild


@api_view(['GET'])
def api_root(request, format=None):
    """
    Returns URLs to all child API views.
    :param request: A request object
    :param format: Format expected by the request. E.G. JSON, XML, etc.
    :return: A response containing URLs to each child API view
    """
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
    serializer_class = BillShortSerializer

    def get_queryset(self):
        """
        Optionally restricts the returned bills to those whose title contains a string, such as 'CFPB'
        """
        queryset = Bill.objects.all()
        filter_string = self.request.query_params.get('title', None)
        if filter_string is not None:
            queryset = queryset.filter(title__icontains=filter_string)
        return queryset


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
    :return An HTTP response stating that the update has been queued
    """
    origin_url_s = 'https://www.govinfo.gov/bulkdata/json/BILLSTATUS/115/s'
    origin_url_hr = 'https://www.govinfo.gov/bulkdata/json/BILLSTATUS/115/hr'
    update.delay(origin_url_s), update.delay(origin_url_hr)
    return HttpResponse(status=200, content='OK: Update queued.')


def rebuild_view(request):
    """
    Rebuilds all legislative subject support splits based on data in the current database instance.
    :param request: A request object
    :return: An HTTP response stating that the rebuild has been queued
    """
    rebuild.delay()
    return HttpResponse(status=200, content='OK: Rebuild queued.')
