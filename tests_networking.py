from django.test import TestCase
import xmltodict
from billserve.networking import *


class BillDataTestCase(TestCase):
    def setUp(self):
        with open('testing_data/example_bill.xml') as f:
            raw = f.read()
        self.data = xmltodict.parse(raw)