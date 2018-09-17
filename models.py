from django.db.models import Model
from django.db.models import CharField, BooleanField, DateTimeField, DateField, IntegerField, TextField, URLField
from django.db.models import ForeignKey, OneToOneField, ManyToManyField
from django.db.models import CASCADE, SET_NULL
from django.db.models import Sum, Case, When
from polymorphic.models import PolymorphicModel
from .managers import *


class Party(Model):
    name = CharField(max_length=200)
    abbreviation = CharField(max_length=5)

    def __str__(self):
        return self.name


class Chamber(Model):
    name = CharField(max_length=200)
    abbreviation = CharField(max_length=5)

    def __str__(self):
        return self.name


class District(Model):
    number = IntegerField()
    state = ForeignKey('State', on_delete=CASCADE)

    def __str__(self):
        return '{state}-{number}'.format(state=self.state.abbreviation, number=self.number)


class Legislator(PolymorphicModel):
    members = ['firstName', 'lastName', 'state', 'party']
    optional_members = ['district', 'isOriginalCosponsor', 'sponsorshipDate']
    objects = LegislatorManager()

    first_name = CharField(max_length=100)
    last_name = CharField(max_length=100)

    def full_name(self):
        return '{first_name} {last_name}'.format(first_name=self.first_name, last_name=self.last_name)

    def sponsored_bills(self):
        return self.sponsored_bills.all()

    def co_sponsored_bills(self):
        return self.co_sponsored_bills.all()


class LegislativeSubjectActivity(Model):
    activity_type = IntegerField(null=True)
    activity_count = IntegerField(default=1)
    bills = ManyToManyField('Bill')
    legislative_subject = ForeignKey('LegislativeSubject', related_name='activities', on_delete=CASCADE)
    legislator = ForeignKey('Legislator', related_name='legislative_subject_activities', on_delete=CASCADE)


class LegislativeSubjectSupportSplit(Model):
    objects = LegislativeSubjectSupportSplitManager()
    red_count = IntegerField(default=0)
    blue_count = IntegerField(default=0)
    white_count = IntegerField(default=0)
    legislative_subject = OneToOneField('LegislativeSubject', related_name='support_split',
                                               on_delete=CASCADE)

    def __str_(self):
        return '{legislative_subject} - red_count: {rc} blue_count: {bc} white_count: {wc}'\
            .format(legislative_subject=self.legislative_subject, rc=self.red_count, bc=self.blue_count,
                    wc=self.white_count)


class Senator(Legislator):
    party = ForeignKey('Party', related_name='senators', on_delete=SET_NULL, null=True)
    legislative_body = ForeignKey('Chamber', related_name='senators', on_delete=SET_NULL, null=True)
    state = ForeignKey('State', related_name='senators', on_delete=SET_NULL, null=True)
    committees = ManyToManyField('Committee', related_name='senators')

    def __str__(self):
        return 'Sen. {first_name} {last_name} [{party}-{state}]'.format(first_name=self.first_name,
                                                                        last_name=self.last_name,
                                                                        party=self.party.abbreviation,
                                                                        state=self.state.abbreviation)


class Representative(Legislator):
    party = ForeignKey('Party', related_name='representatives', on_delete=SET_NULL, null=True)
    district = ForeignKey('District', related_name='representative', on_delete=SET_NULL, null=True)
    legislative_body = ForeignKey('Chamber', related_name='representatives', on_delete=SET_NULL, null=True)
    state = ForeignKey('State', related_name='representatives', on_delete=SET_NULL, null=True)
    committees = ManyToManyField('Committee', related_name='representatives')

    def __str__(self):
        return 'Rep. {first_name} {last_name} [{party}-{district}]'.format(first_name=self.first_name,
                                                                           last_name=self.last_name,
                                                                           party=self.party.abbreviation,
                                                                           district=self.district)


class Bill(Model):
    members = ['billType', 'subjects', 'policyArea', 'committees', 'introducedDate', 'actions', 'title', 'billNumber',
               'summaries', 'sponsors', 'congress', 'originChamber', 'cosponsors', 'relatedBills']
    optional_members = []
    introduction_date_format = '%Y-%m-%d'
    objects = BillManager()

    sponsors = ManyToManyField('Legislator', related_name='sponsored_bills')
    cosponsors = ManyToManyField('Legislator', through='Cosponsorship', related_name='cosponsored_bills')
    policy_area = ForeignKey('PolicyArea', on_delete=SET_NULL, null=True, related_name='bills')
    legislative_subjects = ManyToManyField('LegislativeSubject', related_name='bills')
    related_bills = ManyToManyField('Bill')
    committees = ManyToManyField('Committee')

    originating_body = ForeignKey('Chamber', on_delete=SET_NULL, null=True)

    title = TextField(verbose_name='title of bill', null=True)
    introduction_date = DateField(null=True)
    last_modified = DateTimeField(null=True)

    bill_number = IntegerField(null=True)
    congress = IntegerField(null=True)

    type = CharField(max_length=10, verbose_name='type of bill (S, HR, HRJRES, etc.)', null=True)

    cbo_cost_estimate = URLField(null=True)  # If CBO cost estimate in bill_status
    bill_url = URLField()

    def __str__(self):
        return 'No. {bill_number}: {title}'.format(bill_number=self.bill_number, title=self.title)

    def co_sponsor_count(self):
        return self.cosponsors.all().count()

    def sponsor_count(self):
        return self.sponsors.all().count()


class BillSummary(Model):
    members = ['name', 'actionDate', 'text', 'actionDesc']
    optional_members = []
    action_date_format = '%Y-%m-%d'
    objects = BillSummaryManager()

    name = CharField(max_length=50)
    text = TextField()
    action_description = TextField()
    action_date = DateField()
    bill = ForeignKey('Bill', on_delete=CASCADE, related_name='bill_summaries')

    def __str__(self):
        return '{bill}: {name} ({action_date})'.format(bill=self.bill, name=self.name,
                                                       action_date=self.action_date)


class Committee(Model):
    members = ['name', 'type', 'chamber', 'systemCode']
    optional_members = []
    objects = CommitteeManager()

    name = CharField(max_length=100)
    type = CharField(max_length=50, null=True)
    system_code = CharField(max_length=50)
    chamber = ForeignKey('Chamber', on_delete=CASCADE, null=True)

    def __str__(self):
        return self.name


class PolicyArea(Model):
    members = ['name']
    optional_members = []
    objects = PolicyAreaManager()

    name = CharField(max_length=100)

    def __str__(self):
        return self.name


class LegislativeSubject(Model):
    members = ['name']
    optional_members = []
    objects = LegislativeSubjectManager()

    name = CharField(max_length=100)

    def __str__(self):
        return self.name

    def top_legislators(self):
        sponsors_count = \
            Sum(
                Case(
                    When(sponsored_bills__legislative_subjects__pk=self.pk, then=1),
                    output_field=IntegerField()
                )
            )

        cosponsors_count = \
            Sum(
                Case(
                    When(cosponsored_bills__legislative_subjects__pk=self.pk, then=1),
                    output_field=IntegerField()
                )
            )

        top_sponsors = Legislator.objects.annotate(count=sponsors_count)
        top_sponsors = top_sponsors.filter(count__isnull=False)
        top_sponsors = top_sponsors.order_by('-count')
        top_sponsors = top_sponsors[:5]

        top_cosponsors = Legislator.objects.annotate(count=cosponsors_count)
        top_cosponsors = top_cosponsors.filter(count__isnull=False)
        top_cosponsors = top_cosponsors.order_by('-count')
        top_cosponsors = top_cosponsors[:5]

        return top_sponsors, top_cosponsors


class Action(Model):
    members = ['actionDate', 'committee', 'text', 'type']
    optional_members = []
    action_date_format = '%Y-%m-%d'
    objects = ActionManager()

    committee = ForeignKey('Committee', on_delete=CASCADE, null=True)
    bill = ForeignKey('Bill', on_delete=CASCADE, related_name='actions')
    action_text = TextField(verbose_name='text of the action')
    action_type = TextField()
    action_date = DateField()

    def __str__(self):
        return '{bill}: {action_text} ({action_date})'.format(bill=self.bill, action_text=self.action_text,
                                                              action_date=self.action_date)


class Cosponsorship(Model):
    cosponsorship_date_format = '%Y-%m-%d'
    objects = CosponsorshipManager()

    legislator = ForeignKey('Legislator', on_delete=CASCADE, related_name='cosponsorships')
    bill = ForeignKey('Bill', on_delete=CASCADE)
    is_original_cosponsor = BooleanField()
    cosponsorship_date = DateField()

    def __str__(self):
        return '{legislator} - {bill}'.format(legislator=self.legislator, bill=self.bill)


class Sponsorship(Model):
    legislator = ForeignKey('Legislator', on_delete=CASCADE)
    bill = ForeignKey('Bill', on_delete=CASCADE)

    def __str__(self):
        return '{legislator} - {bill}'.format(legislator=self.legislator, bill=self.bill)


class State(Model):
    name = CharField(max_length=50, null=True)
    abbreviation = CharField(max_length=2)

    def __str__(self):
        return self.abbreviation


class Vote(Model):
    legislator = ForeignKey('Legislator', on_delete=CASCADE)
    bill = ForeignKey('Bill', on_delete=CASCADE)
    yea = BooleanField()

    def __str__(self):
        vote = 'yea' if self.yea else 'nay'
        return '{legislator} voted {vote} on {bill}'.format(legislator=self.legislator, vote=vote, bill=self.bill)
