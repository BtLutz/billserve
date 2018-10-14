import urllib3
import certifi


class HttpClient:
    __pool = urllib3.PoolManager(cert_reqs='CERT_REQUIRED', ca_certs=certifi.where())
    __headers = {'Accept-Encoding': 'gzip, deflate, br',
                 'Accept-Language': 'en-US,en;q=0.5',
                 'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
                 }

    @staticmethod
    def get(url):
        """
        Requests a webpage with the headers that http://govinfo.gov/ requires.
        :param url: The URL you'd like to request
        :return: The response from the remote server
        """
        response = HttpClient.__pool.request('GET', url, headers=HttpClient.__headers)
        if response.status != 200:
            raise urllib3.exceptions.HTTPError('Bad status encountered while requesting url {url}: {status}'
                                               .format(url=url, status=response.status))
        return response
