import logging
from billserve.models import PolicyArea, Legislator, Bill, BillSummary, Action, Committee, LegislativeSubject
from pdb import set_trace
from collections import OrderedDict


class NestedData:
    name = ''
    fields = []
    members = []
    optional_members = []
    data = None

    def __init__(self, name, fields, model=None):
        assert isinstance(name, ''.__class__)
        assert isinstance(fields, [].__class__)

        self.name = name
        self.fields = fields
        if model:
            self.members = model.members
            self.optional_members = model.optional_members

    def parse(self, data, fields):
        logging.info('Parsing data for {n}'.format(n=self.name))
        raw = data
        try:
            for field in self.fields:
                raw = raw[field]
        except KeyError as e:
            raise KeyError('Error parsing field: {e}'.format(e=field))
        except TypeError:
            logging.warning(('Encountered an empty dict in {e}'.format(e=self.fields)))

        if isinstance(raw, OrderedDict):
            self.__verify(raw)
            self.__add_optionals(raw)
            self.__strip(raw)

        self.data = raw
        return raw

    def parse_to_list(self, data):
        res = self.parse(data)
        if not isinstance(res, [].__class__):
            res = [res]
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

    type = NestedData('billType', type_path)
    number = NestedData('billNumber', number_path)
    title = NestedData('billTitle', title_path)
    congress = NestedData('congress', congress_path)
    introduction_date = NestedData('introducedDate', introduction_date_path)
    policy_area = NestedData('policyArea', policy_area_path, PolicyArea)
    sponsors = NestedDataList('sponsors', sponsors_path, Legislator)
    cosponsors = NestedDataList('cosponsors', cosponsors_path, Legislator)
    related_bills = NestedDataList('relatedBills', related_bills_path, Bill)
    actions = NestedDataList('actions', actions_path, Action)
    summaries = NestedDataList('billSummaries', summaries_path, BillSummary)
    committees = NestedDataList('committees', committees_path, Committee)
    legislative_subjects = NestedDataList('legislativeSubjects', legislative_subjects_path, LegislativeSubject)

    def __init__(self, data):
        try:
            data = data['billStatus']['bill']
        except KeyError:
            raise KeyError('Malformed XML data found in data.')
        self.type.parse(data)
        self.number.parse(data)
        self.title.parse(data)
        self.congress.parse(data)
        self.introduction_date.parse(data)
        self.policy_area.parse(data)

        self.sponsors.parse_to_list(data)
        self.cosponsors.parse_to_list(data)
        self.related_bills.parse_to_list(data)
        self.actions.parse_to_list(data)
        self.summaries.parse_to_list(data)
        self.committees.parse_to_list(data)
        self.legislative_subjects.parse_to_list(data)
