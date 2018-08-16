from .models import *
from rest_framework import serializers


class PolicyAreaShortSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = PolicyArea
        fields = ('name', 'url')


class BillShortSerializer(serializers.HyperlinkedModelSerializer):
    title = serializers.CharField(source='__str__')
    policy_area = PolicyAreaShortSerializer()

    class Meta:
        model = Bill
        fields = ('title', 'introduction_date', 'policy_area', 'url')


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
        fields = ('lis_id', 'party', 'legislative_body', 'state', 'committees', 'first_name', 'last_name',
                  'co_sponsored_bills', 'sponsored_bills')


class RepresentativeSerializer(serializers.ModelSerializer):
    sponsored_bills = BillShortSerializer(many=True)
    co_sponsored_bills = BillShortSerializer(many=True)
    state = StateShortSerializer()
    party = PartyShortSerializer()

    class Meta:
        model = Representative
        fields = ('lis_id', 'party', 'legislative_body', 'state', 'committees', 'first_name', 'last_name', 'district',
                  'sponsored_bills', 'co_sponsored_bills')


class PartySerializer(serializers.ModelSerializer):
    senators = SenatorShortSerializer(many=True)
    representatives = RepresentativeShortSerializer(many=True)
    senator_count = serializers.IntegerField(source='senators.count')
    representative_count = serializers.IntegerField(source='representatives.count')

    class Meta:
        model = Party
        fields = ('name', 'abbreviation', 'senators', 'representatives', 'representative_count', 'senator_count')


class StateSerializer(serializers.ModelSerializer):
    representatives = RepresentativeSerializer(many=True)
    representative_count = serializers.IntegerField(source='representatives.count')
    senators = SenatorSerializer(many=True)

    class Meta:
        model = State
        fields = ('name', 'abbreviation', 'senators', 'representatives', 'representative_count')


class LegislativeBodySerializer(serializers.ModelSerializer):
    class Meta:
        model = LegislativeBody
        fields = ('name', 'abbreviation')


class DistrictSerializer(serializers.ModelSerializer):
    representative = RepresentativeShortSerializer(many=True)

    class Meta:
        model = District
        fields = ('number', 'state', 'representative')


class LegislatorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Legislator
        fields = '__all__'


class LegislatorListSerializer(serializers.ModelSerializer):
    def to_representation(self, instance):
        if isinstance(instance, Representative):
            return RepresentativeShortSerializer(instance=instance, context=self.context).data
        elif isinstance(instance, Senator):
            return SenatorShortSerializer(instance=instance, context=self.context).data
        else:
            return LegislatorShortSerializer(instance=instance, context=self.context).data

    class Meta:
        model = Legislator
        fields = '__all__'


class LegislativeSubjectShortSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = LegislativeSubject
        fields = ('name', 'url')


class LegislativeSubjectSerializer(serializers.ModelSerializer):
    bills = BillShortSerializer(many=True)
    support_split = serializers.SerializerMethodField()

    class Meta:
        model = LegislativeSubject
        fields = ('name', 'bills', 'support_split')

    def get_support_split(self, obj):
        def generate_split(legislators):
            red_count = blue_count = white_count = 0
            republican_party = Party.objects.get(abbreviation="R")
            democratic_party = Party.objects.get(abbreviation="D")
            independent_party = Party.objects.get(abbreviation="I")

            for legislator in legislators:
                legislator_party = legislator.party
                if legislator_party == republican_party:
                    red_count += 1
                elif legislator_party == democratic_party:
                    blue_count += 1
                elif legislator_party == independent_party:
                    white_count += 1
                else:
                    raise ValueError('Unexpected party encountered: {p}'.format(p=legislator_party))
            return red_count, blue_count, white_count

        total_red_count = total_blue_count = total_white_count = 0

        for bill in obj.bills.all():
            co_red_count, co_blue_count, co_white_count = generate_split(bill.co_sponsors.select_subclasses())
            sp_red_count, sp_blue_count, sp_white_count = generate_split(bill.sponsors.select_subclasses())

            total_red_count += co_red_count + sp_red_count
            total_blue_count += co_blue_count + sp_blue_count
            total_white_count += co_white_count + sp_white_count

        return {'red_count': total_red_count, 'blue_count': total_blue_count, 'white_count': total_white_count}


class PolicyAreaSerializer(serializers.ModelSerializer):
    bills = BillShortSerializer(many=True)

    class Meta:
        model = PolicyArea
        fields = ('name', 'bills')


class BillSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = BillSummary
        fields = ('name', 'text', 'action_description', 'action_date', 'bill')


class BillSerializer(serializers.ModelSerializer):
    related_bills = BillShortSerializer(many=True)
    sponsors = serializers.SerializerMethodField()
    co_sponsors = serializers.SerializerMethodField()
    legislative_subjects = LegislativeSubjectShortSerializer(many=True)
    policy_area = PolicyAreaShortSerializer()
    bill_summaries = BillSummarySerializer(many=True)
    support_splits = serializers.SerializerMethodField()

    class Meta:
        model = Bill
        fields = ('sponsors', 'co_sponsors', 'policy_area', 'legislative_subjects', 'related_bills', 'committees',
                  'originating_body', 'support_splits', 'title', 'bill_summaries', 'introduction_date', 'last_modified',
                  'bill_number', 'congress', 'type', 'cbo_cost_estimate', 'url', 'bill_url')
        depth = 1

    def get_sponsors(self, obj):
        sponsors = obj.sponsors.select_subclasses()
        return LegislatorListSerializer(sponsors, many=True, context=self.context).data

    def get_co_sponsors(self, obj):
        co_sponsors = obj.co_sponsors.select_subclasses()
        return LegislatorListSerializer(co_sponsors, many=True, context=self.context).data

    def get_support_splits(self, obj):
        class SupportSplit:
            def __init__(self, red_count, blue_count, white_count):
                self.red_count = red_count
                self.blue_count = blue_count
                self.white_count = white_count

            def as_dict(self):
                return {'red_count': self.red_count, 'blue_count': self.blue_count, 'white_count': self.white_count}

        def generate_split(legislators):
            red_count = blue_count = white_count = 0
            republican_party = Party.objects.get(abbreviation="R")
            democratic_party = Party.objects.get(abbreviation="D")
            independent_party = Party.objects.get(abbreviation="I")

            for legislator in legislators:
                legislator_party = legislator.party
                if legislator_party == republican_party:
                    red_count += 1
                elif legislator_party == democratic_party:
                    blue_count += 1
                elif legislator_party == independent_party:
                    white_count += 1
                else:
                    raise ValueError('Unexpected party encountered: {p}'.format(p=legislator_party))

            return SupportSplit(red_count=red_count, blue_count=blue_count, white_count=white_count)

        cosponsorship_split = generate_split(obj.co_sponsors.select_subclasses())
        sponsorship_split = generate_split(obj.sponsors.select_subclasses())

        return {'cosponsorship_split': cosponsorship_split.as_dict(), 'sponsorship_split': sponsorship_split.as_dict()}


class CommitteeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Committee
        fields = ('name', 'type', 'system_code', 'chamber')


class ActionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Action
        fields = ('committee', 'bill', 'action_text', 'action_type', 'action_date')


class VoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vote
        fields = ('yea', 'pk')
