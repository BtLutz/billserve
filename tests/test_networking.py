from django.test import TestCase
import xmltodict
from billserve.networking import *
from billserve.networking.models.billdata import *
from pdb import set_trace


class BillDataTestCase(TestCase):
    def setUp(self):
        with open('billserve/tests/data/example_bill.xml') as f:
            raw = f.read()
        self.data = xmltodict.parse(raw)
        self.bill_data = BillData(self.data)

    def test_bill_data_summaries_length(self):
        expected_summaries_length = 1
        self.assertEqual(len(self.bill_data.summaries), expected_summaries_length)

    def test_bill_data_summaries_content(self):
        expected_summary = OrderedDict(self.data['billStatus']['bill']['summaries']['billSummaries']['item'])
        self.assertEqual(self.bill_data.summaries[0], expected_summary)
