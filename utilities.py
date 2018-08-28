import logging
import datetime
from pytz import utc


def parse_without_coercion(fields, data, url=''):
    """
    Parses nested data from a dictionary without converting the resultant raw data to a list type at the end.
    :param fields: A list of strings to sequentially use as keys to drill into the data dictionary
    :param data: A dictionary object
    :param url: The URL at which the data parameter was parsed from
    :return: The value of the data dictionary after being sequentially keyed by the strings in fields
    """
    assert fields and data, ('Either fields or data not present in call to parse_without_coercion for {url}'
                             'fields: {fields} data: {data}'.format(fields=fields, data=data, url=url))
    if not isinstance(fields, [].__class__):
        fields = [fields]
    raw = data
    try:
        for field in fields:
            raw = raw[field]
    except KeyError as e:
        raise KeyError('Error parsing field from {url}: {e}. Are you sure it\'s there? all fields: {fields}'
                       .format(url=url, e=e, fields=fields))
    except TypeError as e:
        logging.warning(('I encountered an empty dictionary entry for a field in {fields} in {url}. '
                         'Most likely it\'s just not a listed attribute for this bill.').format(fields=fields,
                                                                                                url=url))
        return None
    return raw


def parse_and_coerce_to_list(fields, data, url=''):
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
    if not isinstance(fields, [].__class__):
        fields = [fields]
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


def format_date(string, date_format, date_name, url=''):
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
                          'Most likely I encountered an unexpected date format')
                         .format(date_name=date_name, url=url, string=string))


def fix_name(n):
    """
    Convert all uppercase string to have the first letter capitalized and the rest of the letters lowercase.
    :param n: The string to convert
    :return: The formalized string
    """
    assert isinstance(n, ''.__class__), 'parameter n is not a string: {n}'.format(n=n)
    return "{0}{1}".format(n[0].upper(), n[1:].lower())


def verify_fields_from_json(fields, json, model_string, url='', optional_fields=None):
    d = {}
    try:
        for field in fields:
            field_name = field if isinstance(field, ''.__class__) else field[-1]
            d[field_name] = parse_without_coercion(field, json, url)
    except KeyError as e:
        raise KeyError('Error parsing field from {model_string} at {url}: {field}'
                       .format(model_string=model_string, url=url, field=field))
    if optional_fields:
        try:
            for field in optional_fields:
                d[field] = parse_without_coercion(field, json, url)
        except KeyError:
            d[field] = None
    return d
