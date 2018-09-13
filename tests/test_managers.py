from django.test import TestCase
from billserve.managers import *
from billserve.models import Senator, Representative, Party, State, District


class LegislatorManagerTestCase(TestCase):

    def setUp(self):
        self.manager = LegislatorManager()
        self.r_party = Party.objects.create(abbreviation='R')
        self.d_party = Party.objects.create(abbreviation='D')
        self.nh_state = State.objects.create(abbreviation='NM')
        self.oh_state = State.objects.create(abbreviation='OH')
        self.oh_district = District.objects.create(state=self.oh_state, number=14)
        self.senator = Senator.objects.create(first_name='Martin', last_name='Heinrich', state=self.nh_state,
                                              party=self.d_party)
        self.representative = Representative.objects.create(first_name='David', last_name='Joyce', state=self.oh_state,
                                                            party=self.r_party, district=self.oh_district)
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