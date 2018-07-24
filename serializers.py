from .models import *
from rest_framework import serializers


class BillShortSerializer(serializers.HyperlinkedModelSerializer):
    title = serializers.CharField(source='__str__')

    class Meta:
        model = Bill
        fields = ('title', 'url')


class PartyShortSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Party
        fields = ('abbreviation', 'url')


class StateShortSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = State
        fields = ('abbreviation', 'url')


class DistrictShortSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = District
        fields = ('number', 'url')


class LegislatorShortSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Legislator
        fields = ('lis_id', 'first_name', 'last_name', 'url')


class SenatorShortSerializer(serializers.HyperlinkedModelSerializer):
    full_name = serializers.CharField(source='__str__')
    party = PartyShortSerializer()
    state = StateShortSerializer()

    class Meta:
        model = Senator
        fields = ('full_name', 'state', 'party', 'url')


class RepresentativeShortSerializer(serializers.HyperlinkedModelSerializer):
    full_name = serializers.CharField(source='__str__')
    party = PartyShortSerializer()
    state = StateShortSerializer()
    district = DistrictShortSerializer()

    class Meta:
        model = Representative
        fields = ('full_name', 'party', 'state', 'district', 'url')


class SenatorSerializer(serializers.ModelSerializer):
    sponsored_bills = BillShortSerializer(many=True)
    co_sponsored_bills = BillShortSerializer(many=True)
    state = StateShortSerializer()
    party = PartyShortSerializer()

    class Meta:
        model = Senator
        fields = ('lis_id', 'party', 'legislative_body', 'state', 'committees', 'first_name', 'last_name', 'pk',
                  'co_sponsored_bills', 'sponsored_bills')


class RepresentativeSerializer(serializers.ModelSerializer):
    sponsored_bills = BillShortSerializer(many=True)
    co_sponsored_bills = BillShortSerializer(many=True)
    state = StateShortSerializer()
    party = PartyShortSerializer()

    class Meta:
        model = Representative
        fields = ('lis_id', 'party', 'legislative_body', 'state', 'committees', 'first_name', 'last_name', 'district',
                  'pk', 'sponsored_bills', 'co_sponsored_bills')


class PartySerializer(serializers.ModelSerializer):
    senators = SenatorShortSerializer(many=True)
    representatives = RepresentativeShortSerializer(many=True)
    senator_count = serializers.IntegerField(source='senators.count')
    representative_count = serializers.IntegerField(source='representatives.count')

    class Meta:
        model = Party
        fields = ('name', 'abbreviation', 'senators', 'representatives', 'pk', 'representative_count', 'senator_count')


class StateSerializer(serializers.ModelSerializer):
    representatives = RepresentativeSerializer(many=True)
    representative_count = serializers.IntegerField(source='representatives.count')
    senators = SenatorSerializer(many=True)

    class Meta:
        model = State
        fields = ('name', 'abbreviation', 'pk', 'senators', 'representatives', 'representative_count')


class LegislativeBodySerializer(serializers.ModelSerializer):
    class Meta:
        model = LegislativeBody
        fields = ('name', 'abbreviation', 'pk')


class DistrictSerializer(serializers.ModelSerializer):
    representative = RepresentativeShortSerializer()

    class Meta:
        model = District
        fields = ('number', 'state', 'pk', 'representative')


class LegislatorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Legislator
        fields = '__all__'


class LegislatorListSerializer(serializers.ModelSerializer):
    def to_representation(self, instance):
        if isinstance(instance, Representative):
            return RepresentativeShortSerializer(instance=instance, context=self.context).data
        elif isinstance(instance, Senator):
            return SenatorSerializer(instance=instance, context=self.context).data
        else:
            return LegislatorShortSerializer(instance=instance, context=self.context).data

    class Meta:
        model = Legislator
        fields = '__all__'


class LegislativeSubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = LegislativeSubject
        fields = ('name', 'pk')


class BillSerializer(serializers.ModelSerializer):
    related_bills = BillShortSerializer(many=True)
    sponsors = serializers.SerializerMethodField()
    co_sponsors = serializers.SerializerMethodField()

    class Meta:
        model = Bill
        fields = ('sponsors', 'co_sponsors', 'policy_area', 'legislative_subjects', 'related_bills', 'committees',
                  'originating_body', 'title', 'introduction_date', 'last_modified', 'bill_number', 'congress', 'type',
                  'cbo_cost_estimate', 'url', 'bill_url', 'pk')
        depth = 1

    def get_sponsors(self, obj):
        sponsors = obj.sponsors.select_subclasses()
        return LegislatorListSerializer(sponsors, many=True, context=self.context).data

    def get_co_sponsors(self, obj):
        co_sponsors = obj.co_sponsors.select_subclasses()
        return LegislatorListSerializer(co_sponsors, many=True, context=self.context).data


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


class ActionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Action
        fields = ('committee', 'bill', 'action_text', 'action_type', 'action_date', 'pk')


class VoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vote
        fields = ('yea', 'pk')
