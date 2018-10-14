from django.db.models import Manager
import datetime
from pytz import utc
from .networking.client import GovinfoClient
from .chains import RelatedBillChain
from polymorphic.managers import PolymorphicManager
from itertools import chain


def fix_name(n):
    """
    Convert all uppercase string to have the first letter capitalized and the rest of the letters lowercase.
    :param n: The string to convert
    :return: The formalized string
    """
    assert isinstance(n, ''.__class__), 'parameter n is not a string: {n}'.format(n=n)
    assert len(n) > 0, 'parameter n is < 1 length'
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
        """
        Gets or creates a Legislator instance from a serialized dictionary instance.
        :param data: A dictionary containing a serialized Legislator instance
        :return: A tuple containing the object and a boolean indicator telling whether it was created or not
        """
        from .models import Representative, Senator, District, State, Party
        first_name = data['firstName']
        last_name = data['lastName']
        state = data['state']
        party = data['party']

        if 'district' in data:
            district = data['district']
        else:
            district = None

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
    def create_from_dict(self, data):
        """
        Get or create a Bill instance (and all its related instances) from a serialized dictionary instance.
        :param data: A dictionary containing a serialized Bill instance
        :return: The freshly created Bill instance
        """
        from .models import Bill, PolicyArea, Legislator, Cosponsorship, BillSummary, LegislativeSubject, Action,\
            Committee

        url = data['url']
        bill = self.create(bill_url=url)

        bill.type = data['billType']
        bill.bill_number = int(data['billNumber'])
        bill.title = data['title']
        bill.congress = int(data['congress'])
        bill.introduction_date = format_date(data['introducedDate'], Bill.introduction_date_format)
        bill.save()

        if 'policyArea' in data:
            policy_area_data = data['policyArea']
            policy_area, created = PolicyArea.objects.get_or_create_from_dict(policy_area_data)
            bill.policy_area = policy_area
        else:
            bill.policy_area = None

        for sponsor_data in data['sponsors']:
            sponsor, created = Legislator.objects.get_or_create_from_dict(sponsor_data)
            bill.sponsors.add(sponsor)

        if data['cosponsors']:
            for cosponsor_data in data['cosponsors']:
                Cosponsorship.objects.get_or_create_from_dict(cosponsor_data, bill.pk)

        if data['relatedBills']:
            for related_data in data['relatedBills']:
                related_bill_type = related_data['type']
                related_bill_congress = related_data['congress']
                related_bill_number = related_data['number']

                related_bill_url = GovinfoClient.generate_bill_url(
                    related_bill_congress, related_bill_type, related_bill_number)

                RelatedBillChain.execute(related_bill_url, bill.pk)

        if data['summaries']['billSummaries']:
            for bill_summary_data in data['summaries']['billSummaries']:
                BillSummary.objects.get_or_create_from_dict(bill_summary_data, bill.pk)

        if data['subjects']['billSubjects']['legislativeSubjects']:
            for legislative_subject_data in data['subjects']['billSubjects']['legislativeSubjects']:
                legislative_subject, created = LegislativeSubject.objects.get_or_create_from_dict(
                    legislative_subject_data)
                bill.legislative_subjects.add(legislative_subject)

        for committee_data in data['committees']['billCommittees']:
            committee, created = Committee.objects.get_or_create_from_dict(committee_data)
            bill.committees.add(committee)

        # for action_data in data['actions']:
        #     Action.objects.get_or_create_from_dict(action_data, bill.pk)

        bill.save()

        return bill

    @staticmethod
    def add_related_bill(bill_pk, related_bill_pk):
        """
        Adds a related bill to a bill's related bills, and vice versa.
        :param bill_pk: The primary key of the first related bill
        :param related_bill_pk: The primary key of the second related bill
        """
        from .models import Bill

        related_bill = Bill.objects.get(pk=related_bill_pk)
        bill = Bill.objects.get(pk=bill_pk)

        related_bill.related_bills.add(bill)
        related_bill.save()

        bill.related_bills.add(related_bill)
        bill.save()


class BillSummaryManager(Manager):
    def get_or_create_from_dict(self, data, bill_pk):
        """
        Get or create a Bill Summary instance from a serialized dictionary instance.
        :param data: A dictionary containing the serialized bill summary
        :param bill_pk: The primary key of the bill of which this summary is related
        :return: A tuple containing the bill summary and a boolean indicator of whether it was created
        """
        from .models import BillSummary, Bill

        name = data['name']
        action_date_string = data['actionDate']
        text = data['text']
        description = data['actionDesc']

        action_date = format_date(action_date_string, BillSummary.action_date_format)

        bill = Bill.objects.get(pk=bill_pk)

        return self.get_or_create(name=name, action_date=action_date, text=text, action_description=description,
                                  bill=bill)


class CommitteeManager(Manager):
    def get_or_create_from_dict(self, data):
        """
        Gets or creates a committee instance from a serialized dictionary.
        :param data: A dictionary containing a serialized committee instance
        :return: A tuple containing the committee and a boolean indicator of whether it was created
        """
        from .models import Chamber

        name = data['name']
        c_type = data['type']
        chamber = data['chamber']
        system_code = data['systemCode']
        chamber = Chamber.objects.get(name=chamber)

        return self.update_or_create(name=name, type=c_type, chamber=chamber, system_code=system_code)


class PolicyAreaManager(Manager):
    def get_or_create_from_dict(self, data):
        """
        Gets or creates a policy area instance from a serialized dictionary.
        :param data: A dictionary containing a serialized policy area instance
        :return: A tuple containing the policy area and a boolean indicator of whether it was created
        """
        name = data['name']
        return self.get_or_create(name=name)


class LegislativeSubjectManager(Manager):
    def get_or_create_from_dict(self, data):
        """
        Gets or creates a legislative subject from a serialized model instance.
        :param data: A dictionary containing the serialized legislative subject instance
        :return: A tuple containing the legislative subject and a boolean indicator specifying whether it was created
        """
        name = data['name']

        return self.get_or_create(name=name)


class ActionManager(Manager):
    def get_or_create_from_dict(self, data, bill_pk):
        """
        Gets or creates an action from a serialized model instance.
        :param data: A dictionary containing the serialized action instance
        :param bill_pk: The primary key of the bill to which this action is related
        :return: A tuple containing the action and a boolean indicator specifying whether it was created
        """
        from .models import Action, Committee, Bill

        if 'committee' in data and data['committee']:
            committee_name = data['committee']['name']
            committee_system_code = data['committee']['systemCode']
        else:
            committee_name = None

        text = data['text']
        atype = data['type']
        action_date_string = data['actionDate']

        date = format_date(action_date_string, Action.action_date_format)

        if committee_name and committee_system_code:
            committee = Committee.objects.get(system_code=committee_system_code)
        else:
            committee = None

        bill = Bill.objects.get(pk=bill_pk)

        return self.get_or_create(committee=committee, bill=bill, action_text=text, action_type=atype, action_date=date)


class CosponsorshipManager(Manager):
    def get_or_create_from_dict(self, data, bill_pk):
        """
        Gets or creates a cosponsorship from a serialized model instance.
        :param data: A dictionary containing the serialized cosponsorship instance
        :param bill_pk: The primary key of the bill to which this cosponsorship is related
        :return: A tuple containing the cosponsorship and a boolean indicator specifying whether it was created
        """
        from .models import Legislator, Cosponsorship, Bill

        legislator, created = Legislator.objects.get_or_create_from_dict(data)
        cosponsorship_date_string = data['sponsorshipDate']
        is_original_cosponsor_string = data['isOriginalCosponsor']

        cosponsorship_date = format_date(cosponsorship_date_string, Cosponsorship.cosponsorship_date_format)

        if is_original_cosponsor_string not in {'True', 'False'}:
            raise ValueError('Unexpected isOriginalCosponsor: {v}'.format(v=is_original_cosponsor_string))

        is_original_cosponsor = 'True' if is_original_cosponsor_string == 'True' else False

        bill = Bill.objects.get(pk=bill_pk)

        return self.get_or_create(legislator=legislator, bill=bill, is_original_cosponsor=is_original_cosponsor,
                                  cosponsorship_date=cosponsorship_date)


class LegislativeSubjectSupportSplitManager(Manager):
    def rebuild(self):
        """
        Destroys and then rebuilds all legislative subject support split objects.
        """
        from .models import LegislativeSubject, LegislativeSubjectSupportSplit

        independent_party_pk = 1
        democratic_party_pk = 2
        republican_party_pk = 3

        self.all().delete()

        for legislative_subject in LegislativeSubject.objects.all():
            legislative_subject_support_split = LegislativeSubjectSupportSplit(legislative_subject=legislative_subject)
            for bill in legislative_subject.bills.all():
                legislators = list(chain(bill.sponsors.all(), bill.cosponsors.all()))
                for legislator in legislators:
                    if legislator.party.pk == independent_party_pk:
                        legislative_subject_support_split.white_count += 1
                    elif legislator.party.pk == democratic_party_pk:
                        legislative_subject_support_split.blue_count += 1
                    elif legislator.party.pk == republican_party_pk:
                        legislative_subject_support_split.red_count += 1
            legislative_subject_support_split.save()
