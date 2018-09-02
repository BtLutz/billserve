from .http import HttpClient
from billserve.models import *
from .models.billdata import *
import xmltodict
import logging


class GovinfoClient:

    @staticmethod
    def create_bill_from_url(url):
        client = HttpClient()
        response = client.get(url)
        bill_data_raw = xmltodict.parse(response.data)
        bill_data = BillData(bill_data_raw, url)
        return Bill.objects.create_from_data(bill_data)
