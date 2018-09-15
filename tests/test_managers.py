from django.test import TestCase
from billserve.managers import *
from billserve.models import *
import json


class FixNameTestCase(TestCase):
    def setUp(self):
        self.known_values = [('bob', 'Bob'),
                             ('BLAIRE', 'Blaire'),
                             ('Billie', 'Billie')]

    def test_fix_name(self):
        for inp, expected in self.known_values:
            res = fix_name(inp)
            self.assertEqual(res, expected)

    def test_fix_name_bad_input(self):
        with self.assertRaises(AssertionError):
            fix_name('')

    def test_fix_name_int(self):
        with self.assertRaises(AssertionError):
            fix_name(123)


class LegislatorManagerTestCase(TestCase):
    fixtures = ['states.json', 'parties.json', 'districts.json']

    def setUp(self):
        self.manager = Legislator.objects
        self.senator = Senator.objects.create(
            first_name='Martin', last_name='Heinrich', state=State.objects.get(pk=32), party=Party.objects.get(pk=2))
        self.representative = Representative.objects.create(
            first_name='David', last_name='Joyce', state=State.objects.get(pk=36),
            party=Party.objects.get(pk=3), district=District.objects.get(pk=1))
        self.r_data = {'firstName': 'David',
                       'lastName': 'Joyce',
                       'party': 'R',
                       'state': 'OH',
                       'district': '14'
                       }
        self.s_data = {'firstName': 'Martin',
                       'party': 'D',
                       'state': 'NM',
                       'lastName': 'Heinrich',
                       'district': None
                       }

    def test_get_or_create_from_dict_representative_get(self):
        res = self.manager.get_or_create_from_dict(self.r_data)
        self.assertEqual(res, (self.representative, False))

    def test_get_or_create_from_dict_senator_get(self):
        res = self.manager.get_or_create_from_dict(self.s_data)
        self.assertEqual(res, (self.senator, False))

    def test_get_or_create_from_dict_representative_create(self):
        r_data = self.r_data
        r_data['firstName'] = 'Priya'
        res, created = self.manager.get_or_create_from_dict(r_data)
        rep_count = Representative.objects.all().count()
        self.assertEqual(rep_count, 2)
        self.assertEqual(created, True)

    def test_get_or_create_from_dict_senator_create(self):
        s_data = self.s_data
        s_data['firstName'] = 'Priya'
        res, created = self.manager.get_or_create_from_dict(s_data)
        sen_count = Senator.objects.all().count()
        self.assertEqual(sen_count, 2)
        self.assertEqual(created, True)


class BillSummaryManagerTestCase(TestCase):
    def setUp(self):
        self.data = {'text': 'Creating Higher Education Affordability Necessary to Compete Economically Act',
                     'name': 'Introduced in Senate',
                     'actionDate': '2017-05-01',
                     'actionDesc': 'Introduced in Senate'}
        self.manager = BillSummary.objects
        self.bill = Bill.objects.create(bill_url='http://google.com')
        self.summary = BillSummary.objects.create(
            text='Creating Higher Education Affordability Necessary to Compete Economically Act',
            name='Introduced in Senate',
            action_date=format_date('2017-05-01', BillSummary.action_date_format),
            action_description='Introduced in Senate',
            bill=self.bill)

    def test_get_or_create_from_dict_get(self):
        res, created = self.manager.get_or_create_from_dict(self.data, self.bill.pk)
        self.assertEqual(res, self.summary)
        self.assertEqual(created, False)

    def test_get_or_create_from_dict_create(self):
        data = self.data
        data['text'] = 'Fooing Objectivity or Obtusely Bringing Animal Replacements'
        res, created = self.manager.get_or_create_from_dict(data, self.bill.pk)
        summary_count = self.manager.all().count()
        self.assertEqual(summary_count, 2)
        self.assertEqual(created, True)


class CommitteeManagerTestCase(TestCase):
    fixtures = ['chambers.json', 'committees.json']

    def setUp(self):
        self.data = {'type': 'Standing',
                     'chamber': 'Senate',
                     'name': 'Health, Education, Labor and Pensions Committee',
                     }
        self.committee = Committee.objects.get(pk=1)
        self.manager = Committee.objects

    def test_get_or_create_from_dict_get(self):
        res, created = self.manager.get_or_create_from_dict(self.data)
        self.assertEqual(res, self.committee)
        self.assertEqual(created, False)

    def test_get_or_create_from_dict_create(self):
        data = self.data
        data['chamber'] = 'House of Representatives'
        res, created = self.manager.get_or_create_from_dict(data)
        committee_count = self.manager.all().count()
        self.assertEqual(committee_count, 2)
        self.assertEqual(created, True)


class PolicyAreaManagerTestCase(TestCase):
    fixtures = ['policy_areas.json']

    def setUp(self):
        self.data = {'name': 'Education'}
        self.policy_area = PolicyArea.objects.get(pk=1)
        self.manager = PolicyArea.objects

    def test_get_or_create_from_dict_get(self):
        res, created = self.manager.get_or_create_from_dict(self.data)
        self.assertEqual(res, self.policy_area)
        self.assertEqual(created, False)

    def test_get_or_create_from_dict_create(self):
        data = self.data
        data['name'] = 'Healthcare'
        res, created = self.manager.get_or_create_from_dict(data)
        policy_area_count = self.manager.all().count()
        self.assertEqual(policy_area_count, 2)
        self.assertEqual(created, True)


class LegislativeSubjectManagerTestCase(TestCase):
    def setUp(self):
        self.data = {'name': 'Higher education'}
        self.legislative_subject = LegislativeSubject.objects.create(name='Higher education')
        self.manager = LegislativeSubject.objects

    def test_get_or_create_from_dict_get(self):
        res, created = self.manager.get_or_create_from_dict(self.data)
        self.assertEqual(res, self.legislative_subject)
        self.assertEqual(created, False)

    def test_get_or_create_from_dict_create(self):
        data = self.data
        data['name'] = 'Student aid and college cost'
        res, created = self.manager.get_or_create_from_dict(data)
        legislative_subject_count = self.manager.all().count()
        self.assertEqual(legislative_subject_count, 2)
        self.assertEqual(created, True)


class ActionManagerTestCase(TestCase):
    fixtures = ['chambers.json', 'committees.json']

    def setUp(self):
        self.data = {'actionDate': '2017-05-01',
                     'committee': {'name': 'Health, Education, Labor and Pensions Committee'},
                     'text': 'Read twice and referred to the Committee on Health, Education, Labor, and Pensions.',
                     'type': 'IntroReferral',
                     }
        self.bill = Bill.objects.create(bill_url='http://google.com')
        self.action = Action.objects.create(
            action_date=format_date('2017-05-01', Action.action_date_format),
            committee=Committee.objects.get(pk=1),
            action_text='Read twice and referred to the Committee on Health, Education, Labor, and Pensions.',
            action_type='IntroReferral',
            bill=self.bill)
        self.manager = Action.objects

    def test_get_or_create_from_dict_get(self):
        res, created = self.manager.get_or_create_from_dict(self.data, self.bill.pk)
        self.assertEqual(res, self.action)
        self.assertEqual(created, False)

    def test_get_or_create_from_dict_create(self):
        data = self.data
        data['type'] = 'Vote'
        res, created = self.manager.get_or_create_from_dict(data, self.bill.pk)
        action_count = self.manager.all().count()
        self.assertEqual(action_count, 2)
        self.assertEqual(created, True)


class CosponsorshipManagerTestCase(TestCase):
    fixtures = ['parties.json', 'states.json', 'chambers.json']

    def setUp(self):
        self.r_data = {'firstName': 'David',
                       'lastName': 'Joyce',
                       'party': 'R',
                       'state': 'OH',
                       'district': '14',
                       'isOriginalCosponsor': 'True',
                       'sponsorshipDate': '2017-05-01'
                       }
        self.s_data = {'firstName': 'Martin',
                       'party': 'D',
                       'state': 'NM',
                       'lastName': 'Heinrich',
                       'district': None,
                       'isOriginalCosponsor': 'False',
                       'sponsorshipDate': '2017-05-02'
                       }
        self.oh_district = District.objects.create(state=State.objects.get(pk=36), number=14)
        self.senator = Senator.objects.create(
            first_name='Martin', last_name='Heinrich', state=State.objects.get(pk=32), party=Party.objects.get(pk=2))
        self.representative = Representative.objects.create(
            first_name='David', last_name='Joyce', state=State.objects.get(pk=36),
            party=Party.objects.get(pk=3), district=self.oh_district)
        self.bill = Bill.objects.create(bill_url='http://google.com')
        self.r_cosponsorship = Cosponsorship.objects.create(
            legislator=self.representative, is_original_cosponsor=True,
            cosponsorship_date=format_date('2017-05-01', Cosponsorship.cosponsorship_date_format), bill=self.bill)

        self.s_cosponsorship = Cosponsorship.objects.create(
            legislator=self.senator, is_original_cosponsor=False,
            cosponsorship_date=format_date('2017-05-02', Cosponsorship.cosponsorship_date_format), bill=self.bill)
        self.manager = Cosponsorship.objects

    def test_get_or_create_from_dict_get_representative(self):
        res, created = self.manager.get_or_create_from_dict(self.r_data, self.bill.pk)
        self.assertEqual(res, self.r_cosponsorship)
        self.assertEqual(created, False)

    def test_get_or_create_from_dict_get_senator(self):
        res, created = self.manager.get_or_create_from_dict(self.s_data, self.bill.pk)
        self.assertEqual(res, self.s_cosponsorship)
        self.assertEqual(created, False)

    def test_get_or_create_from_dict_create_representative(self):
        data = self.r_data
        data['firstName'] = 'Amy'
        res, created = self.manager.get_or_create_from_dict(data, self.bill.pk)
        cosponsorship_count = self.manager.all().count()
        self.assertEqual(cosponsorship_count, 3)
        self.assertEqual(created, True)

    def test_get_or_create_from_dict_create_senator(self):
        data = self.s_data
        data['firstName'] = 'Queena'
        res, created = self.manager.get_or_create_from_dict(data, self.bill.pk)
        cosponsorship_count = self.manager.all().count()
        self.assertEqual(cosponsorship_count, 3)
        self.assertEqual(created, True)


class BillManagerTestCase(TestCase):
    fixtures = ['states.json', 'parties.json', 'committees.json', 'chambers.json', 'policy_areas.json', 'bills.json',
                'legislative_subjects.json']

    def setUp(self):
        with open('billserve/tests/data/BILLSTATUS-115s996.json') as f:
            self.data = json.loads(f.read())
        self.manager = Bill.objects

    def test_create_from_dict(self):
        res = self.manager.create_from_dict(self.data)
        self.assertEqual(res.sponsors.count(), 1)
        self.assertEqual(res.cosponsors.count(), 2)
        self.assertIsNotNone(res.policy_area)
        self.assertEqual(res.legislative_subjects.count(), 2)
        self.assertEqual(res.committees.count(), 1)
        # self.assertEqual(res.related_bills.count(), 1) #  Async task doesn't complete in time for testing
        self.assertEqual(res.introduction_date, format_date(self.data['introducedDate'], Bill.introduction_date_format))
        self.assertEqual(res.actions.count(), 1)
        self.assertEqual(res.bill_summaries.count(), 1)

    def test_create_from_dict_original_cosponsors(self):
        # TODO: Test to make sure a bill doesn't have two original cosponsors.
        pass

