from django.contrib.auth.models import User, Group
from .models import *
from rest_framework import serializers


class PartySerializer(serializers.ModelSerializer):
    class Meta:
        model = Party
        fields = ('name', 'abbreviation', 'pk')


class LegislativeBodySerializer(serializers.ModelSerializer):
    class Meta:
        model = LegislativeBody
        fields = ('name', 'abbreviation', 'pk')


class DistrictSerializer(serializers.ModelSerializer):
    class Meta:
        model = District
        fields = ('number', 'state', 'pk')


class LegislatorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Legislator
        fields = ('lis_id', 'party', 'legislative_body', 'state', 'committees', 'first_name', 'last_name', 'pk')


class SenatorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Senator
        fields = ('lis_id', 'party', 'legislative_body', 'state', 'committees', 'first_name', 'last_name', 'pk')


class RepresentativeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Representative
        fields = ('lis_id', 'party', 'legislative_body', 'state', 'committees', 'first_name', 'last_name', 'district',
                  'pk')


class BillSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bill
        fields = ('sponsors', 'co_sponsors', 'policy_area', 'legislative_subjects', 'related_bills', 'committees',
                  'originating_body', 'title', 'introduction_date', 'last_modified', 'bill_number', 'congress', 'type',
                  'cbo_cost_estimate', 'url', 'pk')
        depth = 1


class BillSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = BillSummary
        fields = ('name', 'text', 'action_description', 'action_date', 'bill', 'pk')


class CommitteeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Committee
        fields = ('name', 'type', 'system_code', 'chamber', 'pk')


class PolicyAreaSerializer(serializers.ModelSerializer):
    class Meta:
        model = PolicyArea
        fields = ('name', 'pk')


class LegislativeSubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = LegislativeSubject
        fields = ('name', 'pk')


class ActionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Action
        fields = ('committee', 'bill', 'action_text', 'action_type', 'action_date', 'pk')


class StateSerializer(serializers.ModelSerializer):
    class Meta:
        model = State
        fields = ('name', 'abbreviation', 'pk')


class VoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vote
        fields = ('yea', 'pk')
