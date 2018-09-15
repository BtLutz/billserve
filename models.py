from django.db import models
from polymorphic.models import PolymorphicModel
from .managers import *


class Party(models.Model):
    name = models.CharField(max_length=200)
    abbreviation = models.CharField(max_length=5)

    def __str__(self):
        return self.name


class Chamber(models.Model):
    name = models.CharField(max_length=200)
    abbreviation = models.CharField(max_length=5)

    def __str__(self):
        return self.name


class District(models.Model):
    number = models.IntegerField()
    state = models.ForeignKey('State', on_delete=models.CASCADE)

    def __str__(self):
        return '{state}-{number}'.format(state=self.state.abbreviation, number=self.number)


class Legislator(PolymorphicModel):
    members = ['firstName', 'lastName', 'state', 'party']
    optional_members = ['district', 'isOriginalCosponsor', 'sponsorshipDate']
    objects = LegislatorManager()

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)

    def full_name(self):
        return '{first_name} {last_name}'.format(first_name=self.first_name, last_name=self.last_name)

    def sponsored_bills(self):
        return self.sponsored_bills.all()

    def co_sponsored_bills(self):
        return self.co_sponsored_bills.all()


class LegislativeSubjectActivity(models.Model):
    activity_type = models.IntegerField(null=True)
    activity_count = models.IntegerField(default=1)
    bills = models.ManyToManyField('Bill')
    legislative_subject = models.ForeignKey('LegislativeSubject', related_name='activities',
                                            on_delete=models.CASCADE)
    legislator = models.ForeignKey('Legislator', related_name='legislative_subject_activities',
                                   on_delete=models.CASCADE)


class LegislativeSubjectSupportSplit(models.Model):
    red_count = models.IntegerField(default=0)
    blue_count = models.IntegerField(default=0)
    white_count = models.IntegerField(default=0)
    bills = models.ManyToManyField('Bill')
    legislative_subject = models.OneToOneField('LegislativeSubject', related_name='support_split',
                                               on_delete=models.CASCADE)


class Senator(Legislator):
    party = models.ForeignKey('Party', related_name='senators', on_delete=models.SET_NULL, null=True)
    legislative_body = models.ForeignKey('Chamber', related_name='senators', on_delete=models.SET_NULL,
                                         null=True)
    state = models.ForeignKey('State', related_name='senators', on_delete=models.SET_NULL, null=True)
    committees = models.ManyToManyField('Committee', related_name='senators')

    def __str__(self):
        return 'Sen. {first_name} {last_name} [{party}-{state}]'.format(first_name=self.first_name,
                                                                        last_name=self.last_name,
                                                                        party=self.party.abbreviation,
                                                                        state=self.state.abbreviation)


class Representative(Legislator):
    party = models.ForeignKey('Party', related_name='representatives', on_delete=models.SET_NULL, null=True)
    district = models.ForeignKey('District', related_name='representative', on_delete=models.SET_NULL, null=True)
    legislative_body = models.ForeignKey('Chamber', related_name='representatives', on_delete=models.SET_NULL,
                                         null=True)
    state = models.ForeignKey('State', related_name='representatives', on_delete=models.SET_NULL, null=True)
    committees = models.ManyToManyField('Committee', related_name='representatives')

    def __str__(self):
        return 'Rep. {first_name} {last_name} [{party}-{district}]'.format(first_name=self.first_name,
                                                                           last_name=self.last_name,
                                                                           party=self.party.abbreviation,
                                                                           district=self.district)


class Bill(models.Model):
    members = ['billType', 'subjects', 'policyArea', 'committees', 'introducedDate', 'actions', 'title', 'billNumber',
               'summaries', 'sponsors', 'congress', 'originChamber', 'cosponsors', 'relatedBills']
    optional_members = []
    introduction_date_format = '%Y-%m-%d'
    objects = BillManager()

    sponsors = models.ManyToManyField(
        'Legislator', verbose_name='sponsors of the given bill', related_name='sponsored_bills')
    cosponsors = models.ManyToManyField('Legislator',
                                        through='CoSponsorship',
                                        verbose_name='co-sponsors of the given bill',
                                        related_name='co_sponsored_bills')
    policy_area = models.ForeignKey('PolicyArea', on_delete=models.SET_NULL, null=True, related_name='bills')
    legislative_subjects = models.ManyToManyField('LegislativeSubject', related_name='bills')
    related_bills = models.ManyToManyField('Bill')
    committees = models.ManyToManyField('Committee')

    originating_body = models.ForeignKey('Chamber', on_delete=models.SET_NULL, null=True)

    title = models.TextField(verbose_name='title of bill', null=True)
    introduction_date = models.DateField(null=True)
    last_modified = models.DateTimeField(null=True)

    bill_number = models.IntegerField(verbose_name='bill number (relative to congressional session)', null=True)
    # The congress field is essential for rebuilding URLs (In case I don't have one) to the bill, and it's important
    # for differentiating bill 987 in the 115th congressional senate from bill 987 in the 114th congressional senate.
    congress = models.IntegerField(null=True)

    type = models.CharField(max_length=10, verbose_name='type of bill (S, HR, HRJRES, etc.)', null=True)

    cbo_cost_estimate = models.URLField(null=True)  # If CBO cost estimate in bill_status
    bill_url = models.URLField()

    def __str__(self):
        return 'No. {bill_number}: {title}'.format(bill_number=self.bill_number, title=self.title)

    def co_sponsor_count(self):
        return self.co_sponsors.all().count()

    def sponsor_count(self):
        return self.sponsors.all().count()


class BillSummary(models.Model):
    members = ['name', 'actionDate', 'text', 'actionDesc']
    optional_members = []
    action_date_format = '%Y-%m-%d'
    objects = BillSummaryManager()

    name = models.CharField(max_length=50)
    text = models.TextField()
    action_description = models.TextField()
    action_date = models.DateField()
    bill = models.ForeignKey('Bill', on_delete=models.CASCADE, related_name='bill_summaries')

    def __str__(self):
        return '{bill}: {name} ({action_date})'.format(bill=self.bill.bill_number, name=self.name,
                                                       action_date=self.action_date)


class Committee(models.Model):
    members = ['name', 'type', 'chamber', 'systemCode']
    optional_members = []
    objects = CommitteeManager()

    name = models.CharField(max_length=100)
    type = models.CharField(max_length=50, null=True)
    chamber = models.ForeignKey('Chamber', on_delete=models.CASCADE, null=True)

    def __str__(self):
        return self.name


class PolicyArea(models.Model):
    members = ['name']
    optional_members = []
    objects = PolicyAreaManager()

    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class LegislativeSubject(models.Model):
    members = ['name']
    optional_members = []
    objects = LegislativeSubjectManager()

    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

    def delete(self):
        self.activities.all().delete()
        super.delete()


class Action(models.Model):
    members = ['actionDate', 'committee', 'text', 'type']
    optional_members = []
    action_date_format = '%Y-%m-%d'
    objects = ActionManager()

    committee = models.ForeignKey('Committee', on_delete=models.CASCADE, null=True)
    bill = models.ForeignKey('Bill', on_delete=models.CASCADE, related_name='actions')
    action_text = models.TextField(verbose_name='text of the action')
    action_type = models.TextField()
    action_date = models.DateField()

    def __str__(self):
        return '{bill}: {action_text} ({action_date})'.format(bill=self.bill, action_text=self.action_text,
                                                              action_date=self.action_date)


class Cosponsorship(models.Model):
    cosponsorship_date_format = '%Y-%m-%d'
    objects = CosponsorshipManager()

    legislator = models.ForeignKey('Legislator', on_delete=models.CASCADE)
    bill = models.ForeignKey('Bill', on_delete=models.CASCADE)
    is_original_cosponsor = models.BooleanField()
    cosponsorship_date = models.DateField()

    def __str__(self):
        return '{legislator} - {bill}'.format(legislator=self.legislator, bill=self.bill)


class Sponsorship(models.Model):
    legislator = models.ForeignKey('Legislator', on_delete=models.CASCADE)
    bill = models.ForeignKey('Bill', on_delete=models.CASCADE)

    def __str__(self):
        return '{legislator} - {bill}'.format(legislator=self.legislator, bill=self.bill)


class State(models.Model):
    name = models.CharField(max_length=50, null=True)
    abbreviation = models.CharField(max_length=2)

    def __str__(self):
        return self.abbreviation


class Vote(models.Model):
    legislator = models.ForeignKey('Legislator', on_delete=models.CASCADE)
    bill = models.ForeignKey('Bill', on_delete=models.CASCADE)
    yea = models.BooleanField()

    def __str__(self):
        vote = 'yea' if self.yea else 'nay'
        return '{legislator} voted {vote} on {bill}'.format(legislator=self.legislator, vote=vote, bill=self.bill)
