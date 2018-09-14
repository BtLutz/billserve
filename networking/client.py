from .http import HttpClient
import xmltodict
from .models.MagicDict import MagicDict


class GovinfoClient:

    @staticmethod
    def create_bill_from_url(url):
        """
        Creates a bill instance from a baby URL.
        :param url: THe URL of the bill you'd like to create
        :return: The created bill
        """
        from billserve.models import Bill
        client = HttpClient()
        response = client.get(url)
        bill_data = MagicDict(xmltodict.parse(response.data)).cleaned()
        bill_data['url'] = url
        return Bill.objects.create_from_dict(bill_data)

    @staticmethod
    def generate_bill_url(congress, bill_type, number):
        """
        Generates a govinfo bill URL with the required components.
        :param congress: The congress of the bill (115, 114, 113, etc.)
        :param bill_type: The type of the bill (S, HR, SJ, HRJ, etc.)
        :param number: The number of the bill in its congress (987, 314, etc.)
        :return: A URL that points towards the bill's location on GovInfo.
        """
        return \
            'https://www.govinfo.gov/bulkdata/BILLSTATUS/{congress}/{type}/BILLSTATUS-{congress}{type}{number}.xml' \
            .format(congress=congress, type=bill_type.lower(), number=number)

