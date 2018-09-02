from django.db import models
from polymorphic.models import PolymorphicModel
import datetime
from pytz import utc
from .chains import RelatedBillChain
import celery

from .networking.client import GovinfoClient


def fix_name(n):
    """
    Convert all uppercase string to have the first letter capitalized and the rest of the letters lowercase.
    :param n: The string to convert
    :return: The formalized string
    """
    assert isinstance(n, ''.__class__), 'parameter n is not a string: {n}'.format(n=n)
    return "{0}{1}".format(n[0].upper(), n[1:].lower())


def format_date(string, date_format):
    """
    Formats the given string into a Datetime object based on the given format.
    :param string: A string to format into a date
    :param date_format: A string containing the date format
    :return: A datetime object set to the date and time represented by our string
    """
    return datetime.datetime.strptime(string, date_format).astimezone(utc)


class Party(models.Model):
    name = models.CharField(max_length=200)
    abbreviation = models.CharField(max_length=5)

    def __str__(self):
        return self.name


class LegislativeBody(models.Model):
    name = models.CharField(max_length=200)
    abbreviation = models.CharField(max_length=5)
    title = models.CharField(max_length=5)

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
    cosponsorship_date_format = '%Y-%m-%d'

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
    legislative_body = models.ForeignKey('LegislativeBody', related_name='senators', on_delete=models.SET_NULL,
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
    legislative_body = models.ForeignKey('LegislativeBody', related_name='representatives', on_delete=models.SET_NULL,
                                         null=True)
    state = models.ForeignKey('State', related_name='representatives', on_delete=models.SET_NULL, null=True)
    committees = models.ManyToManyField('Committee', related_name='representatives')

    def __str__(self):
        return 'Rep. {first_name} {last_name} [{party}-{district}]'.format(first_name=self.first_name,
                                                                           last_name=self.last_name,
                                                                           party=self.party.abbreviation,
                                                                           district=self.district)


class BillManager(models.Manager):
    def create_from_data(self, bill_data):
        url = bill_data.url
        bill = self.create(bill_url=url)

        bill.type = bill_data.type
        bill.bill_number = int(bill_data.number)
        bill.title = bill_data.title
        bill.congress = int(bill_data.congress)
        bill.introduction_date = format_date(bill_data.introduction_date, Bill.introduction_date_format)
        bill.save()

        bill.process_policy_area(bill_data.policy_area)
        bill.process_sponsors(bill_data.sponsors)
        bill.process_cosponsors(bill_data.cosponsors)
        bill.process_related_bills(bill_data.related_bills)
        # bill.__process_actions(bill_data.actions)
        # bill.__process_summaries(bill_data.summaries)
        # bill.__process_committees(bill_data.committees)
        bill.process_legislative_subjects(bill_data.legislative_subjects)

        return bill

    @staticmethod
    def add_related_bill(bill_pk, related_bill_pk):
        related_bill = Bill.objects.get(pk=related_bill_pk)
        bill = Bill.objects.get(pk=bill_pk)

        related_bill.related_bills.add(bill)
        related_bill.save()

        bill.related_bills.add(related_bill)
        bill.save()


class Bill(models.Model):
    members = ['type', 'congress', 'number']
    optional_members = []
    introduction_date_format = '%Y-%m-%d'
    objects = BillManager()

    sponsors = models.ManyToManyField(
        'Legislator', verbose_name='sponsors of the given bill', related_name='sponsored_bills')
    co_sponsors = models.ManyToManyField('Legislator',
                                         through='CoSponsorship',
                                         verbose_name='co-sponsors of the given bill',
                                         related_name='co_sponsored_bills')
    policy_area = models.ForeignKey('PolicyArea', on_delete=models.SET_NULL, null=True, related_name='bills')
    legislative_subjects = models.ManyToManyField('LegislativeSubject', related_name='bills')
    related_bills = models.ManyToManyField('Bill')
    committees = models.ManyToManyField('Committee')

    originating_body = models.ForeignKey('LegislativeBody', on_delete=models.SET_NULL, null=True)

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

    def process_policy_area(self, policy_area_data):
        policy_area_name = policy_area_data.data['name']
        policy_area = PolicyArea.objects.get_or_create(name=policy_area_name)[0]
        self.policy_area = policy_area
        self.save()

    def process_sponsors(self, sponsor_data_list):
        for sponsor_data in sponsor_data_list:
            first_name = sponsor_data['firstName']
            last_name = sponsor_data['lastName']
            state = sponsor_data['state']
            party = sponsor_data['party']
            district = sponsor_data['district']

            state = State.objects.get(abbreviation=state)
            party = Party.objects.get(abbreviation=party)

            if district:
                district = District.objects.get_or_create(number=district, state=state)[0]
                legislator = Representative.objects.get_or_create(
                    first_name=first_name, last_name=last_name, state=state, party=party, district=district)[0]
            else:
                legislator = Senator.objects.get_or_create(
                    first_name=first_name, last_name=last_name, state=state, party=party)[0]
            self.sponsors.add(legislator)
        self.save()

    def process_cosponsors(self, cosponsor_data_list):
        for cosponsor_data in cosponsor_data_list:
            first_name = cosponsor_data['firstName']
            last_name = cosponsor_data['lastName']
            state = cosponsor_data['state']
            party = cosponsor_data['party']
            district = cosponsor_data['district']
            is_original_cosponsor_string = cosponsor_data['isOriginalCosponsor']
            cosponsorship_date_string = cosponsor_data['sponsorshipDate']

            cosponsorship_date = format_date(cosponsorship_date_string, Legislator.cosponsorship_date_format)

            if is_original_cosponsor_string not in {'True', 'False'}:
                raise ValueError('Unexpected isOriginalCosponsor value: {v}'.format(v=is_original_cosponsor_string))

            is_original_cosponsor = True if is_original_cosponsor_string == 'True' else False

            state = State.objects.get(abbreviation=state)
            party = Party.objects.get(abbreviation=party)

            if district:
                district = District.objects.get_or_create(number=district, state=state)[0]
                legislator = Representative.objects.get_or_create(
                    first_name=first_name, last_name=last_name, state=state, party=party, district=district)[0]
            else:
                legislator = Senator.objects.get_or_create(
                    first_name=first_name, last_name=last_name, state=state, party=party)[0]

            if not CoSponsorship.objects.filter(bill=self, legislator=legislator).exists():
                CoSponsorship.objects.create(bill=self, legislator=legislator, co_sponsorship_date=cosponsorship_date,
                                             is_original_cosponsor=is_original_cosponsor)

    def process_related_bills(self, related_bill_data_list):
        for related_bill_data in related_bill_data_list:
            related_bill_type = related_bill_data['type']
            related_bill_congress = related_bill_data['congress']
            related_bill_number = related_bill_data['number']

            related_bill_url = GovinfoClient.generate_bill_url(
                related_bill_congress, related_bill_type, related_bill_number)

            RelatedBillChain.execute(related_bill_url, self.pk)

    def process_legislative_subjects(self, legislative_subject_data_list):
        for legislative_subject_data in legislative_subject_data_list:
            name = legislative_subject_data['name']
            legislative_subject = LegislativeSubject.objects.get_or_create(name=name)[0]
            self.legislative_subjects.add(legislative_subject)
        self.save()

    def __str__(self):
        return 'No. {bill_number}: {title}'.format(bill_number=self.bill_number, title=self.title)

    def co_sponsor_count(self):
        return self.co_sponsors.all().count()

    def sponsor_count(self):
        return self.sponsors.all().count()


class BillSummary(models.Model):
    members = ['name', 'actionDate', 'text', 'actionDesc']
    optional_members = []

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

    name = models.CharField(max_length=100)
    type = models.CharField(max_length=50, null=True)
    system_code = models.CharField(max_length=50)
    chamber = models.ForeignKey('LegislativeBody', on_delete=models.CASCADE, null=True)

    def __str__(self):
        return self.name


class PolicyArea(models.Model):
    members = ['name']
    optional_members = []

    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class LegislativeSubject(models.Model):
    members = ['name']
    optional_members = []

    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

    def delete(self):
        self.activities.all().delete()
        super.delete()


class Action(models.Model):
    members = ['actionDate', 'committee', 'text', 'type']
    optional_members = []

    committee = models.ForeignKey('Committee', on_delete=models.CASCADE, null=True)
    bill = models.ForeignKey('Bill', on_delete=models.CASCADE)
    action_text = models.TextField(verbose_name='text of the action')
    action_type = models.TextField()
    action_date = models.DateField()

    def __str__(self):
        return '{bill}: {action_text} ({action_date})'.format(bill=self.bill, action_text=self.action_text,
                                                              action_date=self.action_date)


class CoSponsorship(models.Model):
    legislator = models.ForeignKey('Legislator', on_delete=models.CASCADE)
    bill = models.ForeignKey('Bill', on_delete=models.CASCADE)
    is_original_cosponsor = models.BooleanField()
    co_sponsorship_date = models.DateField()

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
