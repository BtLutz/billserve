from .http import HttpClient
import xmltodict
from .models.MagicDict import MagicDict


class GovinfoClient:

    @staticmethod
    def create_bill_from_url(url):
        from billserve.models import Bill
        client = HttpClient()
        response = client.get(url)
        bill_data = MagicDict(xmltodict.parse(response.data)).cleaned()
        bill_data['url'] = url
        return Bill.objects.create_from_dict(bill_data)

    @staticmethod
    def generate_bill_url(congress, bill_type, number):
        return \
            'https://www.govinfo.gov/bulkdata/BILLSTATUS/{congress}/{type}/BILLSTATUS-{congress}{type}{number}.xml' \
            .format(congress=congress, type=bill_type.lower(), number=number)

