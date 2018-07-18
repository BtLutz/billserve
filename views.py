from django.shortcuts import render
from django.http import HttpResponse
from billserve.models import *
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
def index(request):
    return HttpResponse("Hello, world! You're at the bill serve index.")


def update(request):
    def fix_name(n):
        """ A little helper method for fixing the all-caps naming convention used in the bill status response """
        return "{0}{1}".format(n[0], n[1:].lower())

    def find_party(pa):
        if pa == 'R':
            return Party.objects.get_or_create(abbreviation='R', name='Republican')[0]
        elif pa == 'D':
            return Party.objects.get_or_create(abbreviation='D', name='Democratic')[0]
        else:
            logging.warning('Encountered unknown party abbreviation: {n}. Logging as Independent.'.format(n=pa))
            return Party.objects.get_or_create(abbreviation='I', name='Independent')[0]

    def find_state(sa):
        # TODO: Abstract this state_dict into a separate file
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
        assert fields, data
        raw = data
        try:
            for field in fields:
                raw = raw[field]
        except KeyError as e:
            raise KeyError('Error parsing field from {ur}: {e}. Are you sure it\s there? all fields: {fields}'
                           .format(url=url, e=e, fields=fields))
        except TypeError as e:
            logging.warning(('I encountered an empty dictionary entry for the field {e} in {url}. '
                             'Most likely it\'s just not a listed attribute for this bill.').format(e=e, url=url))
            return None
        return raw

    def parse_and_coerce_to_list_2(fields, data, url):
        assert fields, data
        raw = data
        try:
            for field in fields:
                raw = raw[field]
            raw = raw['item']
        except KeyError as e:
            raise KeyError('Error parsing field from {url}: {e}. All fields: {fields}'.format(url=url, e=e,
                                                                                              fields=fields))
        except TypeError as e:
            logging.warning(('I encountered an empty dictionary entry for the field {e} in {url}. '
            'Most likely it\'s just not a listed attribute for this bill.').format(e=e, url=url))
            return []
        return raw if isinstance(raw, [].__class__) else [raw]

    def parse_and_coerce_to_list(field, data, url):
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
        try:
            return data[field]
        except KeyError as e:
            raise KeyError('Error parsing {field} from {url}: {e}'.format(field,field, url=url, e=e))

    def populate_bill(url, b=None, last_modified_string=None):
        # Coerce the last_modified_string into a Date object to see if we actually need to process this update.
        logging.info('Populating bill at {url}'.format(url=url))
        if last_modified_string:
            try:
                last_modified_date = datetime.datetime.strptime(last_modified_string, '%d-%b-%Y %H:%M').astimezone(utc)
            except ValueError as e:
                raise ValueError('Invalid date format encountered when stripping {last_modified_string} from {url}: {e}'
                                 .format(last_modified_string=last_modified_string, url=url, e=e))
        else:
            last_modified_date = None

        # If we don't have a bill yet, look to see if one exists at this url. If it does and doesn't need updating,
        # just return it.
        if not b:
            b, created = Bill.objects.get_or_create(url=url)
            if not created and b.last_modified == last_modified_date:
                logging.info('Found existing bill {number} to return'.format(number=b.bill_number))
                return b

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

        # Update the Bill object itself with new data
        bill_type = parse_without_coercion('billType', bill_data, url)
        bill_number = parse_without_coercion('billNumber', bill_data, url)
        bill_title = parse_without_coercion('title', bill_data, url)
        introduction_date_string = parse_without_coercion('introducedDate', bill_data, url)
        try:
            introduction_date = datetime.datetime.strptime(introduction_date_string, '%Y-%m-%d').astimezone(utc)
        except ValueError as e:
            raise ValueError('Error converting bill introducedDate on {url}: {e}'.format(url=url, e=e))

        b.type = bill_type
        b.bill_number = bill_number
        b.title = bill_title
        b.introduction_date = introduction_date
        b.save()

        logging.info('Saved new bill {number} at url {url}'.format(number=b.bill_number, url=b.url))

        # Parse related object data from the converted XML
        sponsors = parse_and_coerce_to_list('sponsors', bill_data, url)
        co_sponsors = parse_and_coerce_to_list('cosponsors', bill_data, url)
        related_bills = parse_and_coerce_to_list('relatedBills', bill_data, url)
        actions = parse_and_coerce_to_list('actions', bill_data, url)

        # These are special case fields that are buried further in the XML doc than the other related models.
        # I need further exception handling in case I run into a KeyError before calling parse_and_coerce.
        bill_summaries = parse_and_coerce_to_list_2(['summaries', 'billSummaries'], bill_data, url)
        committees = parse_and_coerce_to_list_2(['committees', 'billCommittees'], bill_data, url)
        policy_area = parse_without_coercion_2(['subjects', 'billSubjects', 'policyArea', 'name'])
        legislative_subjects = parse_and_coerce_to_list_2(['subjects', 'billSubjects', 'legislativeSubjects'],
                                                          bill_data, url)
        # try:
        #     committees = parse_and_coerce_to_list('billCommittees', bill_data['committees'], url)
        # except KeyError:
        #     raise KeyError('Error parsing billCommittees from {url} on key \'committees\'. Is it present?'
        #                    .format(url=url))
        # try:
        #     policy_area = bill_data['subjects']['billSubjects']['policyArea']['name']
        # except KeyError as e:
        #     logging.warning(('KeyError on field {e} for PolicyArea on {url}. Most likely the field is missing from'
        #                      'this particular bill').format(e=e, url=url))
        #     policy_area = None
        # try:
        #     legislative_subjects = parse_and_coerce_to_list('legislativeSubjects',
        #                                                     bill_data['subjects']['billSubjects'],
        #                                                     url)
        # except KeyError as e:
        #     raise KeyError('Error parsing billSubjects from {url} on key: {e}'.format(url=url, e=e))

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
                is_senator = False
            except KeyError:
                is_senator = True

            logging.info('Done parsing info for sponsor {full_name}. Moving to gather related objects.'
                         .format(full_name=full_name))

            state = find_state(state_abbreviation)
            party = find_party(party_abbreviation)

            if is_senator:
                legislative_body = LegislativeBody.objects.get_or_create(name='Senate', abbreviation='S',
                                                                         title='Sen')[0]
                legislator = Senator.objects.get_or_create(lis_id=lis_id, party=party, state=state,
                                                           first_name=first_name, last_name=last_name,
                                                           legislative_body=legislative_body)[0]
            else:
                legislative_body = LegislativeBody.objects.get_or_create(name='House of Representatives',
                                                                         abbreviation='HR', title='Rep')[0]
                district = District.objects.get_or_create(number=district_number, state=state)[0]
                legislator = Representative.objects.get_or_create(lis_id=lis_id, party=party, state=state,
                                                                  first_name=first_name, last_name=last_name,
                                                                  legislative_body=legislative_body,
                                                                  district=district)[0]

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
                is_senator = False
            except KeyError:
                is_senator = True
            logging.info('Done parsing info for cosponsor {full_name}. Moving to gather related objects.'
                         .format(full_name=full_name))

            # Lookups based on fields
            try:
                state = find_state(state_string)
            except KeyError as e:
                raise KeyError('Error parsing state from cosponsor {full_name} on {url}'.format(full_name=full_name,
                                                                                                url=url))
            party = find_party(party_string)

            try:
                co_sponsorship_date = datetime.datetime.strptime(co_sponsorship_date_string, '%Y-%m-%d').date()
            except ValueError as e:
                raise ValueError('Error parsing co_sponsorship_date at {url}: {e}'.format(url=url, e=e))

            if is_original_co_sponsor_string not in {'True', 'False'}:
                raise ValueError('Unexpected string found for isOriginalCosponsor in {url}: {string}'
                                 .format(url=url,string=is_original_co_sponsor_string))
            is_original_co_sponsor = True if is_original_co_sponsor_string == 'True' else False

            if is_senator:
                legislative_body = LegislativeBody.objects.get_or_create(name='Senate', abbreviation='S',
                                                                         title='Sen')[0]
                legislator = Senator.objects.get_or_create(lis_id=lis_id, party=party, state=state,
                                                           first_name=first_name, last_name=last_name,
                                                           legislative_body=legislative_body)[0]
            else:
                legislative_body = LegislativeBody.objects.get_or_create(name='House of Representatives',
                                                                         abbreviation='HR', title='Rep')[0]
                district = District.objects.get_or_create(number=district_number, state=state)[0]
                legislator = Representative.objects.get_or_create(lis_id=lis_id, party=party, state=state,
                                                                  first_name=first_name, last_name=last_name,
                                                                  legislative_body=legislative_body,
                                                                  district=district)[0]

            if not CoSponsorship.objects.filter(legislator=legislator, bill=b,
                                                co_sponsorship_date=co_sponsorship_date,
                                                is_original_cosponsor=is_original_co_sponsor).exists():
                CoSponsorship.objects.create(legislator=legislator, bill=b,
                                             co_sponsorship_date=co_sponsorship_date,
                                             is_original_cosponsor=is_original_co_sponsor)

        for action in actions:
            try:
                action_date_string = action['actionDate']
                committee_string = action['committee']['name']
                # TODO: Add system_code as a field to the Committee model
                committee_system_code = action['committee']['systemCode']
                action_text = action['text']
                action_type = action['type']
            except KeyError as e:
                raise KeyError('Error parsing field from action at {url}: {e}'.format(url=url, e=e))
            try:
                action_date = datetime.datetime.strptime(action_date_string, '%Y-%m-%d')
            except ValueError as e:
                raise ValueError(('Error parsing action_date from action in {url}. Most likely the strptime() function'
                                  ' encountered a different format than expected: {e}').format(url=url, e=e))

            committee = Committee.objects.get_or_create(name=committee_string)[0] if committee_string else None
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
            # TODO: Committees
            pass

        for legislative_subject in legislative_subjects:
            # TODO: Legislative Subjects
            pass

        # TODO: Policy Area

        # TODO: Bill Summaries
        # for bill_summary in bill_summaries:


        # TODO: Originating Bodies
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
