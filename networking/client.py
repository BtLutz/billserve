from .http import HttpClient
import xmltodict
import logging


class GovinfoClient:

    @staticmethod
    def create_bill_from_url(url):
        from .models.billdata import BillData
        from billserve.models import Bill
        client = HttpClient()
        response = client.get(url)
        bill_data_raw = xmltodict.parse(response.data)
        bill_data = BillData(bill_data_raw, url)
        return Bill.objects.create_from_data(bill_data)

    @staticmethod
    def generate_bill_url(congress, bill_type, number):
        return \
            'https://www.govinfo.gov/bulkdata/BILLSTATUS/{congress}/{type}/BILLSTATUS-{congress}{type}{number}.xml' \
            .format(congress=congress, type=bill_type.lower(), number=number)
