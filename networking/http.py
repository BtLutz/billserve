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
        Requests a web page from Govinfo.
        :param url: The URL you'd like to request
        :return: The response from the remote server
        """
        # The request headers provided are required to access Govinfo resources. I couldn't figure out exactly which
        # Accept header was required, so I included all three.
        response = HttpClient.__pool.request('GET', url, headers=HttpClient.__headers)
        if response.status != 200:
            raise urllib3.exceptions.HTTPError('Bad status encountered while requesting url {url}: {status}'
                                               .format(url=url, status=response.status))
        return response

    @staticmethod
    def http_to_https(url):
        """
        Convert a URL that only has 'http://' as its protocol to 'https://'.
        :param url: The non-HTTPS url
        :return: the URl with 'HTTPS' instead of 'HTTP'
        """
        return 'https://' + url[7:]  # If a URL is prefixed with 'http://' its actual resource locator starts at index 7
