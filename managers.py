from django.db.models import Manager
import datetime
from pytz import utc
from .networking.client import GovinfoClient
from .chains import RelatedBillChain
from polymorphic.managers import PolymorphicManager


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


class LegislatorManager(PolymorphicManager):
    def get_or_create_from_dict(self, data):
        from .models import Representative, Senator, District, State, Party

        first_name = data['firstName']
        last_name = data['lastName']
        state = data['state']
        party = data['party']
        district = data['district']

        first_name, last_name = fix_name(first_name), fix_name(last_name)

        state = State.objects.get(abbreviation=state)
        party = Party.objects.get(abbreviation=party)

        if district:
            district = District.objects.get_or_create(number=int(district), state=state)[0]
            legislator = Representative.objects.get_or_create(first_name=first_name, last_name=last_name, state=state,
                                                              party=party, district=district)
        else:
            legislator = Senator.objects.get_or_create(first_name=first_name, last_name=last_name, state=state,
                                                       party=party)

        return legislator


class BillManager(Manager):
    def create_from_dict(self, bill_data):
        from .models import Bill, PolicyArea, Legislator, Cosponsorship, BillSummary, LegislativeSubject, Action,\
            Committee

        url = bill_data['url']
        bill = self.create(bill_url=url)

        bill.type = bill_data['type']
        bill.bill_number = int(bill_data['number'])
        bill.title = bill_data['title']
        bill.congress = int(bill_data['congress'])
        bill.introduction_date = format_date(bill_data['introducedDate'], Bill.introduction_date_format)
        bill.save()

        if 'policyArea' in bill_data:
            policy_area_data = bill_data['policyArea']
            policy_area = PolicyArea.ojects.get_or_create_from_dict(policy_area_data)
            bill.policy_area = policy_area
        else:
            bill.policy_area = None

        for sponsor_data in bill_data['sponsors']:
            sponsor = Legislator.objects.get_or_create_from_dict(sponsor_data)
            bill.sponsors.add(sponsor)

        for cosponsor_data in bill_data['cosponsors']:
            Cosponsorship.objects.create_from_dict(cosponsor_data)

        for related_bill_data in bill_data['relatedBills']:
            related_bill_type = related_bill_data['type']
            related_bill_congress = related_bill_data['congress']
            related_bill_number = related_bill_data['number']

            related_bill_url = GovinfoClient.generate_bill_url(
                related_bill_congress, related_bill_type, related_bill_number)

            RelatedBillChain.execute(related_bill_url, self.pk)

        for bill_summary_data in bill_data['summaries']['billSummaries']:
            BillSummary.objects.create_from_dict(bill_summary_data, bill)

        for legislative_subject_data in bill_data['subjects']['billSubjects']['legislativeSubjects']:
            legislative_subject = LegislativeSubject.objects.get_or_create_from_dict(legislative_subject_data)
            bill.legislative_subjects.add(legislative_subject)

        for action_data in bill_data['actions']:
            action = Action.objects.get_or_create_from_dict(action_data)
            bill.actions.add(action)

        for committee_data in bill_data['committees']['billCommittees']:
            committee = Committee.objects.get_or_create_from_dict(committee_data)
            bill.committees.add(committee)

        bill.save()

        return bill

    @staticmethod
    def add_related_bill(bill_pk, related_bill_pk):
        from .models import Bill

        related_bill = Bill.objects.get(pk=related_bill_pk)
        bill = Bill.objects.get(pk=bill_pk)

        related_bill.related_bills.add(bill)
        related_bill.save()

        bill.related_bills.add(related_bill)
        bill.save()


class BillSummaryManager(Manager):
    def get_or_create_from_dict(self, data, bill_pk):
        from .models import BillSummary, Bill

        name = data['name']
        action_date_string = data['actionDate']
        text = data['text']
        description = data['actionDesc']

        action_date = format_date(action_date_string, BillSummary.action_date_format)

        bill = Bill.objects.get(pk=bill_pk)

        return self.get_or_create(name=name, action_date=action_date, text=text, description=description,
                                  bill=bill)


class CommitteeManager(Manager):
    def get_or_create_from_dict(self, data):
        from .models import Chamber

        name = data['name']
        c_type = data['type']
        chamber = data['chamber']

        chamber = Chamber.objects.get_or_create(name=chamber)

        return self.get_or_create(name=name, type=c_type, chamber=chamber)


class PolicyAreaManager(Manager):
    def get_or_create_from_dict(self, data):
        name = data['name']
        return self.get_or_create(name=name)


class LegislativeSubjectManager(Manager):
    def get_or_create_from_dict(self, data):
        name = data['name']

        return self.get_or_create(name=name)


class ActionManager(Manager):
    def get_or_create_from_dict(self, data, bill_pk):
        from .models import Action, Committee, Bill

        committee_name = data['name']
        text = data['text']
        atype = data['type']
        action_date_string = data['actionDate']

        date = format_date(action_date_string, Action.action_date_format)

        committee = Committee.objects.get_or_create(name=committee_name)
        bill = Bill.objects.get(pk=bill_pk)

        return self.get_or_create(committee=committee, bill=bill, action_text=text, action_type=atype, action_date=date)


class CosponsorshipManager(Manager):
    def get_or_create_from_dict(self, data):
        from .models import Legislator, Cosponsorship

        legislator = Legislator.objects.get_or_create_from_dict(data)
        cosponsorship_date_string = data['sponsorshipDate']
        is_original_cosponsor_string = data['isOriginalCosponsor']

        cosponsorship_date = format_date(cosponsorship_date_string, Cosponsorship.cosponsorship_date_format)

        if is_original_cosponsor_string not in {'True', 'False'}:
            raise ValueError('Unexpected isOriginalCosponsor: {v}'.format(v=is_original_cosponsor_string))

        is_original_cosponsor = bool(is_original_cosponsor_string)

