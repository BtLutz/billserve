import logging
from billserve.models import PolicyArea, Legislator, Bill, BillSummary, Action, Committee, LegislativeSubject
from pdb import set_trace
from collections import OrderedDict


class NestedData:
    name = ''
    members = []
    optional_members = []
    data = None

    def __init__(self, name='', model=None):
        assert isinstance(name, ''.__class__)

        self.name = name
        if model:
            self.members = model.members
            self.optional_members = model.optional_members

    @staticmethod
    def parse_to_raw(data, fields):
        raw = data
        try:
            for field in fields:
                raw = raw[field]
        except KeyError as e:
            raise KeyError('Error parsing field: {e}'.format(e=fields))
        except TypeError:
            logging.warning(('Encountered an empty dict in {e}'.format(e=fields)))
        return raw

    def parse(self, data, fields):
        res = NestedData.parse_to_raw(data, fields)
        if isinstance(res, OrderedDict):
            self.__verify(res)
            self.__add_optionals(res)
            self.__strip(res)
        elif isinstance(res, list):
            for nested in res:
                self.__verify(nested)
                self.__add_optionals(nested)
                self.__strip(nested)
        self.data = res

    def parse_to_list(self, data, fields):
        res = self.parse_to_raw(data, fields)
        if not isinstance(res, [].__class__):
            res = [res]
        for nested in res:
            self.__verify(nested)
            self.__add_optionals(nested)
            self.__strip(nested)
        self.data = res
        return res

    def __verify(self, data):
        def test(d):
            if isinstance(d, ''.__class__):
                return
            d = set(d.keys())
            members = set(self.members)
            if not members <= d:
                fields = members - d
                name = self.name
                raise KeyError('Expected fields {fields} missing from {name} instance.'
                               .format(fields=fields, name=name))
        if isinstance(data, [].__class__):
            for nested in data:
                test(nested)
        else:
            test(data)

    def __add_optionals(self, data):
        if isinstance(data, [].__class__):
            for nested in data:
                for optional in self.optional_members:
                    if optional not in nested:
                        nested[optional] = None
        else:
            for optional in self.optional_members:
                if optional not in data:
                    data[optional] = None

    def __strip(self, data):
        data_keys = set(data.keys())
        member_keys = set(self.members).union(set(self.optional_members))
        diff = data_keys - member_keys
        for key in diff:
            del data[key]


class NestedDataList(NestedData):
    def __getitem__(self, item):
        return self.data[item]

    def __len__(self):
        return len(self.data)


class BillData:
    type = ''
    number = ''
    title = ''
    congress = ''
    introduction_date = ''
    policy_area = NestedData('policyArea', PolicyArea)
    sponsors = NestedDataList('sponsors', Legislator)
    cosponsors = NestedDataList('cosponsors', Legislator)
    related_bills = NestedDataList('relatedBills', Bill)
    actions = NestedDataList('actions', Action)
    summaries = NestedDataList('billSummaries', BillSummary)
    committees = NestedDataList('committees', Committee)
    legislative_subjects = NestedDataList('legislativeSubjects', LegislativeSubject)

    def __init__(self, data):
        try:
            data = data['billStatus']['bill']
        except KeyError:
            raise KeyError('Malformed XML data found in data.')

        type_path = ['billType']
        number_path = ['billNumber']
        title_path = ['title']
        congress_path = ['congress']
        introduction_date_path = ['introducedDate']
        policy_area_path = ['policyArea']
        sponsors_path = ['sponsors', 'item']
        cosponsors_path = ['cosponsors', 'item']
        related_bills_path = ['relatedBills', 'item']
        actions_path = ['actions', 'item']
        summaries_path = ['summaries', 'billSummaries', 'item']
        committees_path = ['committees', 'billCommittees', 'item']
        legislative_subjects_path = ['subjects', 'billSubjects', 'legislativeSubjects', 'item']

        self.type = NestedData.parse_to_raw(data, type_path)
        self.number = NestedData.parse_to_raw(data, number_path)
        self.title = NestedData.parse_to_raw(data, title_path)
        self.congress = NestedData.parse_to_raw(data, congress_path)
        self.introduction_date = NestedData.parse_to_raw(data, introduction_date_path)

        self.policy_area.parse(data, policy_area_path)
        self.sponsors.parse_to_list(data, sponsors_path)
        self.cosponsors.parse_to_list(data, cosponsors_path)
        self.related_bills.parse_to_list(data, related_bills_path)
        self.actions.parse_to_list(data, actions_path)
        self.summaries.parse_to_list(data, summaries_path)
        self.committees.parse_to_list(data, committees_path)
        self.legislative_subjects.parse_to_list(data, legislative_subjects_path)
