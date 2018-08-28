import http
from billserve.models import Bill
import xmltodict


class GovinfoClient:

    @staticmethod
    def create_bill_from_url(self, url):
        bill_data = xmltodict.parse(http.get(url).data)
        return Bill(bill_data)
