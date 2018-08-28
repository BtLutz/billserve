from __future__ import absolute_import, unicode_literals
from celery import shared_task

from .utilities import *

from billserve.networking.http import HttpClient
from .enumerations import LegislativeSubjectActivityType
from billserve.models import *
from billserve.utilitiesold.model_utilities import *
import json
import xmltodict


@shared_task
def populate_legislative_subjects_and_legislators_for_bill(bill_pk, legislative_subjects, sponsors, cosponsors, url):
    def get_or_create_legislative_subjects_from_raw(raw):
        """
        Creates a list of Legislative Subject model instances from a serialized dictionary.
        :param raw: A dictionary containing serialized Legislative Subject instances
        :return: A list of deserialized Legislative Subject objects
        """
        ls = []
        fields = ['name']

        for legislative_subject_raw in raw:
            legislative_subject_raw = verify_fields_from_json(
                fields=fields, json=legislative_subject_raw, model_string='LegislativeSubject', url=url)

            legislative_subject_name = legislative_subject_raw['name']
            legislative_subject = LegislativeSubject.objects.get_or_create(name=legislative_subject_name)[0]
            ls.append(legislative_subject)

        return ls

    def get_or_create_sponsors_from_raw(raw):
        """
        Creates a list of Legislator model instances from a serialized dictionary.
        :param raw: A dictionary containing serialized Legislator instances
        :return: A list of deserialized Legislator objects
        """
        s = []
        for sponsor_raw in raw:
            sponsor_raw = parse_legislator_from_json(json=sponsor_raw, model_string='Legislator', url=url)

            first_name = sponsor_raw['firstName']
            last_name = sponsor_raw['lastName']
            lis_id = sponsor_raw['lisID']
            state_abbreviation = sponsor_raw['state']
            party_abbreviation = sponsor_raw['party']
            district_number = sponsor_raw['district']

            state = find_state(state_abbreviation=state_abbreviation)
            party = find_party(party_abbreviation=party_abbreviation)

            legislator = get_legislator(lis_id, party, state, first_name, last_name, district_number)
            s.append(legislator)

        return s

    def get_or_create_cosponsors_from_raw(raw):
        """
        Creates a list of legislator model instances from a serialized dictionary.
        :param raw: A dictionary containing serialized legislator instances with added cosponsors fields
        :return: A list of tuples in the format (legislator, cosponsorship_date, is_original_cosponsor)
        """
        c = []
        extra_fields = ['isOriginalCosponsor', 'sponsorshipDate']
        is_original_cosponsor_lookup = {'True': True, 'False': False}

        for cosponsor_raw in raw:
            cosponsor_raw = parse_legislator_from_json(
                json=cosponsor_raw, model_string='cosponsor', url=url, extra_fields=extra_fields)

            first_name = cosponsor_raw['firstName']
            last_name = cosponsor_raw['lastName']
            lis_id = cosponsor_raw['lisID']
            state_abbreviation = cosponsor_raw['state']
            party_abbreviation = cosponsor_raw['party']
            district_number = cosponsor_raw['district']
            is_original_cosponsor_string = cosponsor_raw['isOriginalCosponsor']
            cosponsorship_date_string = cosponsor_raw['sponsorshipDate']

            state = find_state(state_abbreviation=state_abbreviation)
            party = find_party(party_abbreviation=party_abbreviation)

            cosponsorship_date = format_date(cosponsorship_date_string, '%Y-%m-%d', 'cosponsorshipDate', url)

            if is_original_cosponsor_string not in is_original_cosponsor_lookup:
                raise ValueError('Unexpected result found for isOriginalCosponsor in {url}: {r}'
                                 .format(url=url, r=is_original_cosponsor_string))
            is_original_cosponsor = is_original_cosponsor_lookup[is_original_cosponsor_string]

            legislator = get_legislator(lis_id=lis_id, party=party, state=state, first_name=first_name,
                                        last_name=last_name, district_number=district_number)

            c.append((legislator, cosponsorship_date, is_original_cosponsor))

        return c

    def add_legislative_subjects_to_bill(b, ls):
        """
        Adds a list of legislative subjects to a given bill.
        :param b: A bill model instance
        :param ls: A list of legislative subject instances
        :return: None
        """
        for legislative_subject in ls:
            b.legislative_subjects.add(legislative_subject)

    def add_sponsors_to_bill(b, s):
        """
        Adds a list of legislators to a given bill as sponsors.
        :param b: A bill model instance
        :param s: A list of legislator instances
        :return: None
        """
        for l in s:
            if not Sponsorship.objects.filter(legislator=l, bill=b).exists():
                Sponsorship.objects.create(legislator=l, bill=b)

    def add_cosponsors_to_bill(b, c):
        """
        Adds a list of legislators to a given bill as cosponsors.
        :param b: A bill model instance
        :param c: A list of tuples of the format (legislator, cosponsorship_date, is_original_cosponsor)
        :return: None
        """
        for l in c:
            legislator = l[0]
            cosponsorship_date = l[1]
            is_original_cosponsor = l[2]

            if not CoSponsorship.objects.filter(legislator=legislator, co_sponsorship_date=cosponsorship_date,
                                                is_original_cosponsor=is_original_cosponsor, bill=b):
                CoSponsorship.objects.create(legislator=legislator, co_sponsorship_date=cosponsorship_date,
                                             is_original_cosponsor=is_original_cosponsor, bill=b)

    def update_legislative_subject_activities_for_bill(b):
        """
        Updates the legislative subject activities for a given bill.
        :param b:
        :return:
        """
        def update_legislative_subject_activity(legislative_subject, legislator, activity_type, b):
            legislative_subject_activity, created = LegislativeSubjectActivity.objects.get_or_create(
                legislative_subject=legislative_subject, legislator=legislator, activity_type=activity_type)
            if not created or b not in legislative_subject_activity.bills.all():
                legislative_subject_activity.bills.add(b)
                legislative_subject_activity.activity_count += 1
                legislative_subject_activity.save()

        ls = b.legislative_subjects.all()
        s = b.sponsors.all()
        c = b.sponsors.all()

        s_activity_type = LegislativeSubjectActivityType.sponsorship.value
        c_activity_type = LegislativeSubjectActivityType.cosponsorship.value

        for legislative_subject in ls:
            for l in s:
                update_legislative_subject_activity(
                    legislative_subject=legislative_subject, legislator=l, activity_type=s_activity_type, b=b)
            for l in c:
                update_legislative_subject_activity(
                    legislative_subject=legislative_subject, legislator=l, activity_type=c_activity_type, b=b)

    def update_legislative_subject_support_splits_for_bill(b):
        def update_support_split(support_split, legislator, bill):
            if bill in support_split.bills.all():
                return
            support_split.bills.add(b)
            democratic_party = find_party(party_abbreviation='D')
            republican_party = find_party(party_abbreviation='R')
            independent_party = find_party(party_abbreviation='I')

            legislator_party = l.party
            if legislator_party == democratic_party:
                ss.blue_count += 1
            elif legislator_party == republican_party:
                ss.red_count += 1
            elif legislator_party == independent_party:
                ss.white_count += 1
            else:
                raise ValueError('Unexpected party encountered while updating support split: {p}'
                                 .format(p=legislator_party))
            ss.save()

        ls = b.legislative_subjects.all()
        s = b.sponsors.all()
        c = b.co_sponsors.all()

        for legislative_subject in ls:
            for l in s:
                ss, created = LegislativeSubjectSupportSplit.objects.get_or_create(
                    legislative_subject=legislative_subject)
                update_support_split(ss, l, b)
            for l in c:
                ss, created = LegislativeSubjectSupportSplit.objects.get_or_create(
                    legislative_subject=legislative_subject)
                update_support_split(ss, l, b)

    bill = Bill.objects.get(pk=bill_pk)

    legislative_subjects = get_or_create_legislative_subjects_from_raw(raw=legislative_subjects)
    sponsors = get_or_create_sponsors_from_raw(raw=sponsors)
    cosponsors = get_or_create_cosponsors_from_raw(raw=cosponsors)

    add_legislative_subjects_to_bill(b=bill, ls=legislative_subjects)
    add_sponsors_to_bill(b=bill, s=sponsors)
    add_cosponsors_to_bill(b=bill, c=cosponsors)
    update_legislative_subject_activities_for_bill(b=bill)
    update_legislative_subject_support_splits_for_bill(b=bill)

    bill.save()


@shared_task
def populate_related_bills_for_bill(bill_pk, related_bills, url, depth):
    bill = Bill.objects.get(pk=bill_pk)
    fields = ['type', 'congress', 'number']
    for related_bill_data in related_bills:
        related_bill = verify_fields_from_json(fields, related_bill_data, 'related bill', url)

        related_bill_type = related_bill['type']
        related_bill_congress = related_bill['congress']
        related_bill_number = related_bill['number']
        related_bill_url = \
            'https://www.govinfo.gov/bulkdata/BILLSTATUS/{congress}/{type}/BILLSTATUS-{congress}{type}{number}.xml' \
            .format(congress=related_bill_congress, type=related_bill_type.lower(), number=related_bill_number)
        related_bill, created = Bill.objects.get_or_create(bill_url=related_bill_url)

        bill.related_bills.add(related_bill)
        related_bill.related_bills.add(bill)

        if created:
            populate_bill.delay(related_bill_url, bill_pk=related_bill.pk, depth=depth + 1)

    bill.save()


@shared_task
def populate_bill_summaries_for_bill(bill_pk, bill_summaries, url):
    bill = Bill.objects.get(pk=bill_pk)
    fields = ['name', 'actionDate', 'text', 'actionDesc']
    for bill_summary_data in bill_summaries:
        bill_summary = verify_fields_from_json(fields, bill_summary_data, 'bill summary', url)

        bill_summary_name = bill_summary['name']
        bill_summary_action_date_string = bill_summary['actionDate']
        bill_summary_text = bill_summary['text']
        bill_summary_action_description = bill_summary['actionDesc']

        action_date = format_date(bill_summary_action_date_string, '%Y-%m-%d', 'actionDate', url)

        if not BillSummary.objects.filter(name=bill_summary_name, bill=bill, action_date=action_date).exists():
            BillSummary.objects.create(name=bill_summary_name, text=bill_summary_text,
                                       action_description=bill_summary_action_description, action_date=action_date, bill=bill)
    bill.save()


@shared_task
def populate_policy_area_for_bill(bill_pk, policy_area_name, url):
    policy_areas = PolicyArea.objects.all
    bill = Bill.objects.get(pk=bill_pk)
    policy_area = PolicyArea.objects.get_or_create(name=policy_area_name)[0] if policy_area_name else None
    bill.policy_area = policy_area
    bill.save()
    return policy_area_name


@shared_task
def populate_bill(url, bill_pk=None, last_modified_string=None, depth=0):
    http = HttpClient()

    last_modified_date = format_date(last_modified_string, '%d-%b-%Y %H:%M', 'lastModifiedDate', url) \
        if last_modified_string else None

    if not bill_pk:
        b, created = Bill.objects.get_or_create(bill_url=url)
        if not created and b.last_modified == last_modified_date:
            return
    else:
        b = Bill.objects.get(pk=bill_pk)

    bill_status_response = http.get(url)

    bill_data_raw = xmltodict.parse(bill_status_response.data)
    bill_data = parse_without_coercion(['billStatus', 'bill'], bill_data_raw, url)

    bill_type = parse_without_coercion('billType', bill_data, url)
    bill_number = parse_without_coercion('billNumber', bill_data, url)
    bill_title = parse_without_coercion('title', bill_data, url)
    bill_congress = parse_without_coercion('congress', bill_data, url)

    introduction_date_string = parse_without_coercion('introducedDate', bill_data, url)
    introduction_date = format_date(introduction_date_string, '%Y-%m-%d', 'introducedDate', url)

    b.type = bill_type
    b.bill_number = bill_number
    b.title = bill_title
    b.congress = bill_congress
    b.introduction_date = introduction_date
    b.last_modified = last_modified_date

    b.save()

    if depth == 5:
        return

    sponsors = parse_and_coerce_to_list('sponsors', bill_data, url)
    cosponsors = parse_and_coerce_to_list('cosponsors', bill_data, url)
    related_bills = parse_and_coerce_to_list('relatedBills', bill_data, url)
    actions = parse_and_coerce_to_list('actions', bill_data, url)

    bill_summaries = parse_and_coerce_to_list(['summaries', 'billSummaries'], bill_data, url)
    committees = parse_and_coerce_to_list(['committees', 'billCommittees'], bill_data, url)
    policy_area = parse_without_coercion(['policyArea', 'name'], bill_data, url)
    legislative_subjects = parse_and_coerce_to_list(['subjects', 'billSubjects', 'legislativeSubjects'], bill_data, url)

    populate_legislative_subjects_and_legislators_for_bill.delay(
        bill_pk=b.pk, legislative_subjects=legislative_subjects, sponsors=sponsors, cosponsors=cosponsors, url=url)
    populate_related_bills_for_bill.delay(b.pk, related_bills, url, depth)
    populate_bill_summaries_for_bill.delay(b.pk, bill_summaries, url)
    populate_policy_area_for_bill.delay(b.pk, policy_area, url)
    # TODO: committees, actions and policy areas


@shared_task
def update(origin_url):
    http = HttpClient()

    response = http.get(origin_url)
    response_data = json.loads(response.data)

    for bill in response_data['files']:
        # bill_status_url = parse_without_coercion('link', file, url)
        bill_status_url = 'https://www.govinfo.gov/bulkdata/BILLSTATUS/115/s/BILLSTATUS-115s987.xml'
        bill_last_modified_string = parse_without_coercion('formattedLastModifiedTime', bill, origin_url)
        populate_bill.delay(url=bill_status_url, last_modified_string=bill_last_modified_string)
        return
