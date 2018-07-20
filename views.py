from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt

from rest_framework.parsers import JSONParser
from rest_framework.renderers import JSONRenderer

from billserve.models import *
from billserve.serializers import *

import urllib3
import json
import logging
from pdb import set_trace
import xmltodict
import datetime
from pytz import utc

# Note: Possible ways to make money...
# 1. Sell wholesale yearly access to congresspeople (i.e. $20K for unlimited queries)
# 2. Sell per-unit queries (i.e. $0.05 per record accessed / $5 per query / etc.)

# Process:
# 1. Roll Call, Politico, Glenn Kessler @ WP would know if something like this has already been done
# 2. Voting records

# Features:
# 1. Legislator reference page. Fancy vote counter

# Important references:
# 1. House of Representative voting example: http://clerk.house.gov/evs/2018/roll297.xml
# 2. Senate voting example: https://www.senate.gov/legislative/LIS/roll_call_votes/vote1141/vote_114_1_00067.xml
# It seems like the House of Representatives votes on a lot more bills than the senate...


@csrf_exempt
def bill_list(request):
    """
    Retrieve all bills.
    :param request: A request object
    :return: A JSON dump of all bills
    """
    if request.method == 'GET':
        bills = Bill.objects.all()
        serializer = BillSerializer(bills, many=True)
        return JsonResponse(serializer.data, safe=False)


@csrf_exempt
def bill_congress_list(request, congress):
    """
    List all Bill objects with the corresponding congress number.
    :param request: A request to the billserve/<c>/ endpoint
    :param congress: The congress that you'd like to parse Bills from
    :return: A JSON response with a list of all Bills proposed within the given congress
    """
    if request.method == 'GET':
        bills = Bill.objects.filter(congress=congress)
        serializer = BillSerializer(bills, many=True)
        return JsonResponse(serializer.data, safe=False)


@csrf_exempt
def bill_congress_detail(request, congress, bill_number):
    """
    Retrieve a Bill.
    :param request: A request object
    :param congress: The congress number of the bill you'd like to return
    :param bill_number: The bill number of the bill you'd like to return
    :return: A JSON response containing a bill with a corresponding congress and bill_number, if it exists
    """
    try:
        bill = Bill.objects.get(congress=congress, bill_number=bill_number)
    except Bill.DoesNotExist:
        return HttpResponse(status=404)

    if request.method == 'GET':
        serializer = BillSerializer(bill)
        return JsonResponse(serializer.data)


@csrf_exempt
def bill_subject_list(request, legislative_subject_pk):
    """
    Retrieve all bills associated to a legislative subject with the given primary key.
    :param request: A request object
    :param legislative_subject_pk: the primary key of the legislative subject to look up
    :return: A JSON response containing a dump of all bills with the legislative subject listed as related
    """
    if request.method == 'GET':
        try:
            legislative_subject = LegislativeSubject.objects.get(pk=legislative_subject_pk)
        except LegislativeSubject.DoesNotExist:
            return HttpResponse(status=404)
        bills = legislative_subject.bills.all()
        serializer = BillSerializer(bills, many=True)
        return JsonResponse(serializer.data, safe=False)


@csrf_exempt
def bill_subject_congress_list(request, legislative_subject_pk, congress):
    """
    Retrieve all bills associated to a legislative subject with the given primary key proposed within a given congress.
    :param request: A request object
    :param legislative_subject_pk: The primary key of the given legislative subject to look up
    :param congress: The number of the congressional session to look for bills in
    :return: A response containing a list of all bills associated with the given legislative subject and congress
    """
    if request.method == 'GET':
        try:
            legislative_subject = LegislativeSubject.objects.get(pk=legislative_subject_pk)
        except LegislativeSubject.DoesNotExist:
            # TODO: Add better error responding to all endpoints that currently can return a 404 error.
            # A good place to start would be placing info in the body informing the client exactly why they got a 404.
            return HttpResponse(status=404)
        bills = legislative_subject.bills.filter(congress=congress)
        serializer = BillSerializer(bills, many=True)
        return JsonResponse(serializer.data, safe=False)


@csrf_exempt
def subject_list(request):
    """
    Retrieve all legislative subjects.
    :param request: A request to the /billserve/subjects/ endpoint
    :return: A list of all legislative subjects
    """
    if request.method == 'GET':
        legislative_subjects = LegislativeSubject.objects.all()
        serializer = LegislativeSubjectSerializer(legislative_subjects, many=True)
        return JsonResponse(serializer.data, safe=False)


def index(request):
    return HttpResponse("Hello, world! You're at the bill serve index.")


def update(request):
    """
    Updates the database with new data from govinfo.
    :param request: A request object
    :return: None
    """
    def fix_name(n):
        """
        Convert all uppercase string to have the first letter capitalized and the rest of the letters lowercase.
        :param n: The string to convert
        :return: The formalized string
        """
        assert isinstance(n, ''.__class__), 'parameter n is not a string: {n}'.format(n=n)
        return "{0}{1}".format(n[0].upper(), n[1:].lower())

    def find_party(pa):
        """
        Looks up a political party based on its abbreviation. Soon to be deprecated in favor of initial data.
        :param pa:
        :return:
        """
        # TODO: this -> https://docs.djangoproject.com/en/2.0/howto/initial-data/
        if pa == 'R':
            return Party.objects.get_or_create(abbreviation='R', name='Republican')[0]
        elif pa == 'D':
            return Party.objects.get_or_create(abbreviation='D', name='Democratic')[0]
        else:
            logging.warning('Encountered unknown party abbreviation: {n}. Logging as Independent.'.format(n=pa))
            return Party.objects.get_or_create(abbreviation='I', name='Independent')[0]

    def find_state(sa):
        """
        Looks up a state based on its abbreviation. Soon to be deprecated in favor of initial data.
        :param sa:
        :return:
        """
        # TODO: this -> https://docs.djangoproject.com/en/2.0/howto/initial-data/
        state_dict = {'AL': 'Alabama',
                      'AK': 'Alaska',
                      'AZ': 'Arizona',
                      'AR': 'Arkansas',
                      'CA': 'California',
                      'CO': 'Colorado',
                      'CT': 'Connecticut',
                      'DE': 'Delaware',
                      'DC': 'District of Columbia',
                      'FL': 'Florida',
                      'GA': 'Georgia',
                      'HI': 'Hawaii',
                      'ID': 'Idaho',
                      'IL': 'Illinois',
                      'IN': 'Indiana',
                      'IA': 'Iowa',
                      'KS': 'Kansas',
                      'KY': 'Kentucky',
                      'LA': 'Louisiana',
                      'ME': 'Maine',
                      'MD': 'Maryland',
                      'MA': 'Massachusetts',
                      'MI': 'Michigan',
                      'MN': 'Minnesota',
                      'MS': 'Mississippi',
                      'MO': 'Missouri',
                      'MT': 'Montana',
                      'NE': 'Nebraska',
                      'NV': 'Nevada',
                      'NH': 'New Hampshire',
                      'NJ': 'New Jersey',
                      'NM': 'New Mexico',
                      'NY': 'New York',
                      'NC': 'North Carolina',
                      'ND': 'North Dakota',
                      'OH': 'Ohio',
                      'OK': 'Oklahoma',
                      'OR': 'Oregon',
                      'PA': 'Pennsylvania',
                      'RI': 'Rhode Island',
                      'SC': 'South Carolina',
                      'SD': 'South Dakota',
                      'TN': 'Tennessee',
                      'TX': 'Texas',
                      'UT': 'Utah',
                      'VT': 'Vermont',
                      'VA': 'Virginia',
                      'WA': 'Washington',
                      'WV': 'West Virginia',
                      'WI': 'Wisconsin',
                      'WY': 'Wyoming',
                      'MP': 'Northern Mariana Islands',
                      'AS': 'American Samoa',
                      'GU': 'Guam',
                      'PR': 'Puerto Rico',
                      'VI': 'U.S. Virgin Islands',
                      'UM': 'U.S. Minor Outlying Islands',
                      'FM': 'Micronesia',
                      'MH': 'Marshall Island',
                      'PW': 'Palau',}
        try:
            state_name = state_dict[sa]
        except KeyError as e:
            raise KeyError('Unknown state abbreviation found: {e}'.format(e=e))
        return State.objects.get_or_create(abbreviation=sa, name=state_name)[0]

    def parse_without_coercion_2(fields, data, url):
        # TODO: Rename after I delete the deprecated method
        """
        Parses nested data from a dictionary without converting the resultant raw data to a list type at the end.
        :param fields: A list of strings to sequentially use as keys to drill into the data dictionary
        :param data: A dictionary object
        :param url: The URL at which the data parameter was parsed from
        :return: The value of the data dictionary after being sequentially keyed by the strings in fields
        """
        assert fields and data, ('Either fields or data not present in call to parse_without_coercion for {url}'
                                 'fields: {fields} data: {data}'.format(fields=fields, data=data, url=url))
        raw = data
        try:
            for field in fields:
                raw = raw[field]
        except KeyError as e:
            raise KeyError('Error parsing field from {ur}: {e}. Are you sure it\s there? all fields: {fields}'
                           .format(url=url, e=e, fields=fields))
        except TypeError as e:
            logging.warning(('I encountered an empty dictionary entry for a field in {fields} in {url}. '
                             'Most likely it\'s just not a listed attribute for this bill.').format(fields=fields,
                                                                                                    url=url))
            return None
        return raw

    def parse_and_coerce_to_list_2(fields, data, url):
        # TODO: Rename after I delete the deprecated method
        """
        Parses nested data from a dictionary and places the resultant raw data into a list object, if it isn't already
        a list.
        :param fields: A list of strings to sequentially use as keys to drill down into the data dictionary
        :param data: A dictionary object
        :param url: The URL at which the data parameter was parsed from
        :return: The value of the data dictionary after being sequentially keyed by the strings in fields, in a list
        if it wasn't already a list when we found it.
        """
        assert fields and data, ('Either fields or data not present in call to parse_and_coerce_to_list for {url}. '
                                 'fields: {fields}, data: {data}'.format(fields=fields, data=data, url=url))
        raw = data
        try:
            for field in fields:
                raw = raw[field]
            raw = raw['item']
        except KeyError as e:
            raise KeyError('Error parsing field from {url}: {e}. All fields: {fields}'.format(url=url, e=e,
                                                                                              fields=fields))
        except TypeError as e:
            logging.warning(('I encountered an empty dictionary entry for a field in {fields} in {url}. '
                             'Most likely it\'s just not a listed attribute for this bill.').format(fields=fields,
                                                                                                    url=url))
            return []
        return raw if isinstance(raw, [].__class__) else [raw]

    def parse_and_coerce_to_list(field, data, url):
        # TODO: Delete and refactor
        try:
            raw = data[field]['item']
            return raw if isinstance(raw, [].__class__) else [raw]
        except KeyError as e:
            raise KeyError('KeyError parsing {field} from {url}: {e}'.format(field, url=url, e=e))
        except TypeError as e:
            # In this case, the field was most likely just missing from this particular bill. We log something to keep
            # track of and for QA (just in case I did actually miss something).
            logging.warning('NoneType passed into parse_and_coerce_from_list for field {field} on {url}'
                            .format(field=field, url=url))
            return []

    def parse_without_coercion(field, data, url):
        # TODO: Delete and refactor
        try:
            return data[field]
        except KeyError as e:
            raise KeyError('Error parsing {field} from {url}: {e}'.format(field,field, url=url, e=e))

    def format_date(string, date_format, date_name, url):
        """
        Formats the given string into a Datetime object based on the given format.
        :param string: A string to format into a date
        :param date_format: A string containing the date format
        :param date_name: A string containing the type of date we're trying to format
        :param url: A URL to the page from which we found our string
        :return: A datetime object set to the date and time represented by our string
        """
        try:
            return datetime.datetime.strptime(string, date_format).astimezone(utc)
        except ValueError:
            raise ValueError(('Error parsing date {date_name} from {url}. I received the string {string}.'
                              'Most likely I encountered an unexpected date format').format(date_name=date_name,
                                                                                            url=url, string=string))

    def get_legislator(lis_id, party, state, first_name, last_name, district_number=None):
        # TODO: this -> https://docs.djangoproject.com/en/2.0/howto/initial-data/
        if not district_number:
            legislative_body = LegislativeBody.objects.get_or_create(name='Senate', abbreviation='S')[0]
            return Senator.objects.get_or_create(lis_id=lis_id, party=party, state=state, first_name=first_name,
                                                 last_name=last_name, legislative_body=legislative_body)[0]
        else:
            legislative_body = LegislativeBody.objects.get_or_create(name='House of Representatives',
                                                                     abbreviation='S')[0]
            district = District.objects.get_or_create(number=district_number, state=state)[0]
            return Representative.objects.get_or_create(lis_id=lis_id, party=party, state=state, first_name=first_name,
                                                        last_name=last_name, legislative_body=legislative_body,
                                                        district=district)[0]

    def populate_bill(url, b=None, last_modified_string=None):
        """
        Populates a bill object with data.
        :param url: The URL at which the bill data can be found
        :param b: The bill object to populate, if it already exists
        :param last_modified_string: A string representing the last time a bill was modified on govinfo
        :return: The updated bill
        """
        # Coerce the last_modified_string into a Date object to see if we actually need to process this update.
        logging.info('Populating bill at {url}'.format(url=url))
        last_modified_date = format_date(last_modified_string, '%d-%b-%Y %H:%M', 'lastModifiedDate', url) \
            if last_modified_string else None

        # If we don't have a bill yet, look to see if one exists at this url. If it does and doesn't need updating,
        # just return it.
        if not b:
            b, created = Bill.objects.get_or_create(url=url)
            if not created and b.last_modified == last_modified_date:
                logging.info('Found existing bill {number} to return'.format(number=b.bill_number))
                # return b

        # In this case, the bill either didn't already exist or it needs updating. We need to request
        # the bill's URL and update all fields and related models. In this case the method runs to completion.
        bill_status_response = http.request('GET', url)
        if bill_status_response.status != 200:
            raise urllib3.exceptions.HTTPError('Bad status encountered during fetch for {url}: {status}'
                                               .format(url=url, status=bill_status_response.status))

        # Parse the entirety of the bill data from XML to OrderedDicts
        try:
            bill_data = xmltodict.parse(bill_status_response.data)['billStatus']['bill']
        except KeyError as e:
            raise ValueError('Improperly formatted XML was found when parsing {url}'.format(url=url))

        # Parse the data we'll use to update our Bill object
        bill_type = parse_without_coercion('billType', bill_data, url)
        bill_number = parse_without_coercion('billNumber', bill_data, url)
        bill_title = parse_without_coercion('title', bill_data, url)
        bill_congress = parse_without_coercion('congress', bill_data, url)

        introduction_date_string = parse_without_coercion('introducedDate', bill_data, url)
        introduction_date = format_date(introduction_date_string, '%Y-%m-%d', 'introducedDate', url)

        # Update the Bill objects with the data we parsed
        b.type = bill_type
        b.bill_number = bill_number
        b.title = bill_title
        b.congress = bill_congress
        b.introduction_date = introduction_date
        b.last_modified = last_modified_date

        # Parse related object data from the converted XML
        sponsors = parse_and_coerce_to_list('sponsors', bill_data, url)
        co_sponsors = parse_and_coerce_to_list('cosponsors', bill_data, url)
        related_bills = parse_and_coerce_to_list('relatedBills', bill_data, url)
        actions = parse_and_coerce_to_list('actions', bill_data, url)

        # These are special case fields that are buried further in the XML doc than the other related models.
        bill_summaries = parse_and_coerce_to_list_2(['summaries', 'billSummaries'], bill_data, url)
        committees = parse_and_coerce_to_list_2(['committees', 'billCommittees'], bill_data, url)
        policy_area = parse_without_coercion_2(['subjects', 'billSubjects', 'policyArea', 'name'], bill_data, url)
        legislative_subjects = parse_and_coerce_to_list_2(['subjects', 'billSubjects', 'legislativeSubjects'],
                                                          bill_data, url)

        for sponsor in sponsors:
            try:
                first_name = fix_name(sponsor['firstName'])
                last_name = fix_name(sponsor['lastName'])
                full_name = sponsor['fullName']
                lis_id = int(sponsor['identifiers']['lisID'])
                state_abbreviation = sponsor['state']
                party_abbreviation = sponsor['party']
            except KeyError as e:
                raise KeyError('Error parsing data from sponsor in {url}: {e}'.format(url=url, e=e))
            except TypeError as e:
                raise TypeError('Most likely a missing field on sponsor in {url}: {e}'.format(url=url, e=e))

            try:
                district_number = sponsor['district']
            except KeyError:
                district_number = None

            logging.info('Done parsing info for sponsor {full_name}. Moving to gather related objects.'
                         .format(full_name=full_name))

            state = find_state(state_abbreviation)
            party = find_party(party_abbreviation)

            legislator = get_legislator(lis_id, party, state, first_name, last_name, district_number)

            if not Sponsorship.objects.filter(legislator=legislator, bill=b).exists():
                Sponsorship.objects.create(legislator=legislator, bill=b)

        for co_sponsor in co_sponsors:
            # Parse field from dict
            try:
                first_name = co_sponsor['firstName']
                last_name = co_sponsor['lastName']
                full_name = co_sponsor['fullName']
                lis_id = co_sponsor['identifiers']['lisID']
                state_string = co_sponsor['state']
                party_string = co_sponsor['party']
                is_original_co_sponsor_string = co_sponsor['isOriginalCosponsor']
                co_sponsorship_date_string = co_sponsor['sponsorshipDate']
            except KeyError as e:
                raise KeyError('Error parsing field from co_sponsor at {url}: {e}'.format(url=url, e=e))

            try:
                district_number = co_sponsor['district']
            except KeyError:
                district_number = None
            logging.info('Done parsing info for cosponsor {full_name}. Moving to gather related objects.'
                         .format(full_name=full_name))

            # Lookups based on fields
            try:
                state = find_state(state_string)
            except KeyError as e:
                raise KeyError('Error parsing state from cosponsor {full_name} on {url}'.format(full_name=full_name,
                                                                                                url=url))
            party = find_party(party_string)
            co_sponsorship_date = format_date(co_sponsorship_date_string, '%Y-%m-%d', 'cosponsorshipDate', url)

            if is_original_co_sponsor_string not in {'True', 'False'}:
                raise ValueError('Unexpected string found for isOriginalCosponsor in {url}: {string}'
                                 .format(url=url,string=is_original_co_sponsor_string))
            is_original_co_sponsor = True if is_original_co_sponsor_string == 'True' else False

            legislator = get_legislator(lis_id, party, state, first_name, last_name, district_number)

            if not CoSponsorship.objects.filter(legislator=legislator, bill=b,
                                                co_sponsorship_date=co_sponsorship_date,
                                                is_original_cosponsor=is_original_co_sponsor).exists():
                CoSponsorship.objects.create(legislator=legislator, bill=b,
                                             co_sponsorship_date=co_sponsorship_date,
                                             is_original_cosponsor=is_original_co_sponsor)

        for action in actions:
            try:
                action_date_string = action['actionDate']
                committee_name_string = parse_without_coercion_2(['committee', 'name'], action, url)
                committee_system_code = parse_without_coercion_2(['committee', 'systemCode'], action, url)
                action_text = action['text']
                action_type = action['type']
            except KeyError as e:
                raise KeyError('Error parsing field from action at {url}: {e}'.format(url=url, e=e))
            action_date = format_date(action_date_string, '%Y-%m-%d', 'actionDate', url)

            committee = Committee.objects.get_or_create(
                name=committee_name_string, system_code=committee_system_code)[0] \
                if committee_name_string else None

            if not Action.objects.filter(committee=committee, bill=b, action_text=action_text,
                                         action_type=action_type, action_date=action_date):
                Action.objects.create(committee=committee, bill=b, action_text=action_text,
                                      action_type=action_type, action_date=action_date)

        for related_bill in related_bills:
            try:
                related_bill_type = related_bill['type']
                related_bill_congress = related_bill['congress']
                related_bill_number = related_bill['number']
            except KeyError as e:
                raise KeyError('Error parsing field from related_bill in {url}: {e}'.format(url=url, e=e))

            related_bill_url = \
                'https://www.govinfo.gov/bulkdata/BILLSTATUS/{congress}/{type}/BILLSTATUS-{congress}{type}{number}.xml'\
                .format(congress=related_bill_congress, type=related_bill_type.lower(), number=related_bill_number)
            related_bill, created = Bill.objects.get_or_create(url=related_bill_url)

            if created:
                related_bill = populate_bill(related_bill_url, b=related_bill)

            b.related_bills.add(related_bill)
            related_bill.related_bills.add(b)

        for committee in committees:
            try:
                committee_name = committee['name']
                committee_type = committee['type']
                committee_chamber_string = committee['chamber']
                committee_system_code = committee['systemCode']
            except KeyError as e:
                raise KeyError('Error parsing field from committee at {url}: {e}'.format(url=url, e=e))

            chamber = LegislativeBody.objects.get_or_create(name=committee_chamber_string)[0]

            defaults = {'chamber': chamber, 'type': committee_type}
            committee = Committee.objects.update_or_create(defaults=defaults, system_code=committee_system_code)[0]
            b.committees.add(committee)

        for legislative_subject in legislative_subjects:
            try:
                legislative_subject_name = legislative_subject['name']
            except KeyError as e:
                raise KeyError('Error parsing name from legislativeSubject at {url}'.format(url=url))
            b.legislative_subjects.add(LegislativeSubject.objects.get_or_create(name=legislative_subject_name)[0])

        b.policy_area = PolicyArea.objects.get_or_create(name=policy_area)[0] if policy_area else None

        for bill_summary in bill_summaries:
            try:
                bill_summary_name = bill_summary['name']
                bill_summary_action_date_string = bill_summary['actionDate']
                bill_summary_text = bill_summary['text']
                bill_summary_action_description = bill_summary['actionDesc']
            except KeyError as e:
                raise KeyError('Error parsing field from bill_summary at {url}: {e}'.format(url=url, e=e))

            action_date = format_date(bill_summary_action_date_string, '%Y-%m-%d', 'actionDate', url)

            if not BillSummary.objects.filter(name=bill_summary_name, bill=b, action_date=action_date).exists():
                BillSummary.objects.create(name=bill_summary_name, text=bill_summary_text,
                                           action_description=bill_summary_action_description,
                                           action_date=action_date, bill=b)

        # Adding originating body to the bill. This is relevant for any queries that might want to look up all bills
        # currently on the floor of the senate.
        if bill_type in {'S', 'SJRES', 'SRES', 'SCONRES'}:
            b.originating_body = LegislativeBody.objects.get_or_create(name='Senate', abbreviation='S')[0]
        elif bill_type in {'HR', 'HRES', 'HJRES', 'HCONRES'}:
            b.originating_body = LegislativeBody.objects.get_or_create(name='House of Representatives',
                                                                       abbreviation='HR')[0]
        # Is it improper/unsafe to only save once this late in the view?
        b.save()
        logging.info('Saved or updated new bill {number} at url {url}.'.format(number=b.bill_number, url=b.url))
        return b

    # Setup and request for main bill directory. The headers are necessary for a request to the main directory,
    # otherwise I get a 406 error. That has to do with the Accept headers on the request, so I added them all in
    # to be safe.
    originating_url = 'https://www.govinfo.gov/bulkdata/json/BILLSTATUS/115/s'
    http = urllib3.PoolManager()
    headers = {'Accept-Encoding': 'gzip, deflate, br',
               'Accept-Language': 'en-US,en;q=0.5',
               'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'}
    response = http.request('GET', originating_url, headers=headers)

    # Processing response (error checking and formatting)
    if response.status != 200:
        logging.warning('Error fetching {url): {status}'.format(url=originating_url, status=response.status))
        return
    response_data = json.loads(response.data)

    # Iterating through bills listed in response
    for file in response_data['files']:
        # bill_status_url = parse_without_coercion('link', file, url)
        # TODO: Don't forget to switch back to the previous statement from this link below!!!
        bill_status_url = 'https://www.govinfo.gov/bulkdata/BILLSTATUS/115/s/BILLSTATUS-115s987.xml'
        last_modified_string = parse_without_coercion('formattedLastModifiedTime', file, originating_url)
        populate_bill(url=bill_status_url, last_modified_string=last_modified_string)

        return HttpResponse('OK')

