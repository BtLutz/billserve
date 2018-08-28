from django.test import TestCase
import xmltodict
from billserve.networking.models.billdata import *
from pdb import set_trace


class BillDataTestCase(TestCase):

    @staticmethod
    def ordered_keys(k):
        return OrderedDict.fromkeys(k).keys()

    def setUp(self):
        with open('billserve/tests/data/example_bill.xml') as f:
            raw = f.read()
        self.data = xmltodict.parse(raw)
        self.bill_data = BillData(self.data)

    def test_bill_data_nested_data(self):
        self.assertEqual(self.bill_data.type, 'S')
        self.assertEqual(self.bill_data.number, '119')
        self.assertEqual(self.bill_data.title, 'Sunshine for Regulatory Decrees and Settlements Act of 2017')
        self.assertEqual(self.bill_data.congress, '115')
        self.assertEqual(self.bill_data.introduction_date, '2017-01-12')

    def test_bill_data_policy_area_keys(self):
        policy_area_keys = BillDataTestCase.ordered_keys(PolicyArea.members)
        self.assertEqual(self.bill_data.policy_area.data.keys(), policy_area_keys)

    def test_bill_data_policy_area_content(self):
        policy_area = self.data['billStatus']['bill']['policyArea']
        self.assertEqual(self.bill_data.policy_area.data, policy_area)

    def test_bill_data_summaries_length(self):
        summaries_length = 1
        self.assertEqual(len(self.bill_data.summaries), summaries_length)

    def test_bill_data_summaries_keys(self):
        summary_keys = BillDataTestCase.ordered_keys(BillSummary.members)
        self.assertEqual(self.bill_data.summaries[0].keys(), summary_keys)

    def test_bill_data_summaries_content(self):
        summary = OrderedDict(self.data['billStatus']['bill']['summaries']['billSummaries']['item'])
        self.assertEqual(self.bill_data.summaries[0], summary)
