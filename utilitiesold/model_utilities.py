from billserve.models import *


def parse_legislator_from_json(json, model_string, url, extra_fields=None):
    fields = ['firstName', 'lastName', 'fullName', ['identifiers', 'lisID'], 'state', 'party']

    # If a client has included extra fields they're expecting on the legislator, include them in required fields.
    if extra_fields:
        fields.extend(extra_fields)

    # District is present on representatives but not on senators. Therefore it's an optional field.
    optional_fields = ['district']
    legislator_fields = verify_fields_from_json(
        fields=fields, json=json, model_string=model_string, url=url, optional_fields=optional_fields)

    # Fixing certain fields so that they return to the client in the right format.
    legislator_fields['firstName'] = fix_name(legislator_fields['firstName'])
    legislator_fields['lastName'] = fix_name(legislator_fields['lastName'])
    legislator_fields['lisID'] = int(legislator_fields['lisID'])

    return legislator_fields


def find_party(party_abbreviation):
    """
    Looks up a political party based on its abbreviation. Soon to be deprecated in favor of initial data.
    :param party_abbreviation: A string containing a political party abbreviation
    :return: A Party model instance
    """
    # TODO: this -> https://docs.djangoproject.com/en/2.0/howto/initial-data/
    if party_abbreviation == 'R':
        return Party.objects.get_or_create(abbreviation='R', name='Republican')[0]
    elif party_abbreviation == 'D':
        return Party.objects.get_or_create(abbreviation='D', name='Democratic')[0]
    elif party_abbreviation == 'I':
        return Party.objects.get_or_create(abbreviation='I', name='Independent')[0]
    else:
        raise ValueError('Unexpected party abbreviation found: {p}'.format(p=party_abbreviation))


def find_state(state_abbreviation):
    """
    Looks up a state based on its abbreviation. Soon to be deprecated in favor of initial data.
    :param state_abbreviation: A string keyed in the state_dict dictionary
    :return: A state model instance
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
                  'PW': 'Palau'}
    try:
        state_name = state_dict[state_abbreviation]
    except KeyError as e:
        raise KeyError('Unknown state abbreviation found: {e}'.format(e=e))
    return State.objects.get_or_create(abbreviation=state_abbreviation, name=state_name)[0]


def get_legislator(lis_id, party, state, first_name, last_name, district_number=None):
    logging.info('Getting legislator {first_name} {last_name} {lis_id}'.format(first_name=first_name,
                                                                               last_name=last_name, lis_id=lis_id))
    if not district_number:
        legislative_body = LegislativeBody.objects.get_or_create(name='Senate', abbreviation='S')[0]
        senator, created = Senator.objects.get_or_create(lis_id=lis_id, party=party, state=state,
                                                         first_name=first_name,last_name=last_name,
                                                         legislative_body=legislative_body)
        if created:
            message = 'Created new senator: {senator}'.format(senator=senator)
        else:
            message = 'Got existing senator: {senator}'.format(senator=senator)
        logging.info(message)
        return senator
    else:
        legislative_body = LegislativeBody.objects.get_or_create(name='House of Representatives',
                                                                 abbreviation='S')[0]
        district = District.objects.get_or_create(number=district_number, state=state)[0]
        representative, created = Representative.objects.get_or_create(lis_id=lis_id, party=party, state=state,
                                                                       first_name=first_name, last_name=last_name,
                                                                       legislative_body=legislative_body,
                                                                       district=district)
        if created:
            message = 'Created new representative: {representative}'.format(representative=representative)
        else:
            message = 'Got existing representative: {representative}'.format(representative=representative)
        logging.info(message)
        return representative


def update_support_split(support_split, legislator):
    logging.info('Updating support split for {ls}'.format(ls=support_split.legislative_subject.name))
    democratic_party = find_party(party_abbreviation='D')
    republican_party = find_party(party_abbreviation='R')
    independent_party = find_party(party_abbreviation='I')

    legislator_party = legislator.party
    if legislator_party == democratic_party:
        support_split.blue_count += 1
    elif legislator_party == republican_party:
        support_split.red_count += 1
    elif legislator_party == independent_party:
        support_split.white_count += 1
    else:
        raise ValueError('Unexpected party encountered: {p}'.format(p=legislator_party))
    support_split.save()
