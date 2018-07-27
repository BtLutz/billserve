from django.db import models
from model_utils.managers import InheritanceManager


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


class Legislator(models.Model):
    lis_id = models.IntegerField()
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    objects = InheritanceManager()

    def full_name(self):
        return '{first_name} {last_name}'.format(first_name=self.first_name, last_name=self.last_name)

    def sponsored_bills(self):
        return self.sponsored_bills.all()

    def co_sponsored_bills(self):
        return self.co_sponsored_bills.all()


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
    district = models.OneToOneField('District', related_name='representative', on_delete=models.SET_NULL, null=True)
    legislative_body = models.ForeignKey('LegislativeBody', related_name='representatives', on_delete=models.SET_NULL,
                                         null=True)
    state = models.ForeignKey('State', related_name='representatives', on_delete=models.SET_NULL, null=True)
    committees = models.ManyToManyField('Committee', related_name='representatives')

    def __str__(self):
        return 'Rep. {first_name} {last_name} [{party}-{district}]'.format(first_name=self.first_name,
                                                                           last_name=self.last_name,
                                                                           party=self.party.abbreviation,
                                                                           district=self.district)


# A big deal in the near future will be adding a boolean field to denote if a bill has already been voted on.
# This will entail some logic in the code to decide whether or not a bill has been voted on. Most likely
# if I find any content in the recordedVotes field I can mark the boolean (has_been_voted_on) as True and then save
# the corresponding votes. For right now I'm just going to focus on relaying the bill data to the user in a clean format
class Bill(models.Model):
    # TODO: add a way to track what stage the bill is at.
    # I can write a module that'll take Actions and analyze their type to find out how far it's gone
    sponsors = models.ManyToManyField('Legislator',
                                      through='Sponsorship',
                                      verbose_name='sponsors of the given bill',
                                      related_name='sponsored_bills')
    co_sponsors = models.ManyToManyField('Legislator',
                                         through='CoSponsorship',
                                         verbose_name='co-sponsors of the given bill',
                                         related_name='co_sponsored_bills')
    policy_area = models.ForeignKey('PolicyArea', on_delete=models.SET_NULL, null=True, related_name='bills')
    legislative_subjects = models.ManyToManyField('LegislativeSubject', related_name='bills')
    related_bills = models.ManyToManyField('Bill')
    committees = models.ManyToManyField('Committee')

    # I'm leaving off the latest_bill_summary field because it's unnecessary.
    # To get the most recent summary, query and then sort by date and only return the first to client.
    originating_body = models.ForeignKey('LegislativeBody', on_delete=models.SET_NULL, null=True)

    title = models.TextField(verbose_name='title of bill', null=True)

    introduction_date = models.DateTimeField(verbose_name='date bill was created', null=True)
    last_modified = models.DateTimeField(null=True)

    bill_number = models.IntegerField(verbose_name='bill number (relative to congressional session)', null=True)
    # The congress field is essential for rebuilding URLs (In case I don't have one) to the bill, and it's important
    # for differentiating bill 987 in the 115th congressional senate from bill 987 in the 114th congressional senate.
    congress = models.IntegerField(null=True)

    type = models.CharField(max_length=10, verbose_name='type of bill (S, HR, HRJRES, etc.)', null=True)

    cbo_cost_estimate = models.URLField(null=True)  # If CBO cost estimate in bill_status, then append it to the related bill
    bill_url = models.URLField()
    # NOTE: I'm adding in related_bills as a field for right now. This may be useful for later for if a user views
    # a bill and would like to see related bills through a query. I can provide an easy endpoints for the iOS controller
    # code that, after a bill is loaded in the view, can query all related bills asynchronously and add them to the view
    # as they come in.

    def __str__(self):
        return 'No. {bill_number}: {title}'.format(bill_number=self.bill_number, title=self.title)

    def co_sponsor_count(self):
        return self.co_sponsors.count()

    def sponsor_count(self):
        return self.sponsors.count()


class BillSummary(models.Model):
    name = models.CharField(max_length=50)
    text = models.TextField()
    action_description = models.TextField()
    action_date = models.DateField()
    bill = models.ForeignKey('Bill', on_delete=models.CASCADE, related_name='bill_summaries')

    def __str__(self):
        return '{bill}: {name} ({action_date})'.format(bill=self.bill.bill_number, name=self.name,
                                                       action_date=self.action_date)


class Committee(models.Model):
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=50, null=True)
    system_code = models.CharField(max_length=50)
    chamber = models.ForeignKey('LegislativeBody', on_delete=models.CASCADE, null=True)

    def __str__(self):
        return self.name


class PolicyArea(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class LegislativeSubject(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name


class Action(models.Model):
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
