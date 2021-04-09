"""
A Python wrapper to SMS-Activate's API.
"""
import requests
import time

def read_countries():
    """
    Read countries data from data/countries.txt
    """
    countries = {}
    with open("data/countries.txt", "r") as outfile:
        for line in outfile.readlines():
            data = line.split()
            countries[int(data[0])] = data[1]
    return countries


countries = read_countries()


class SMSActivate:
    def __init__(self, api_key, country=None):
        self.api_key = api_key
        self.country = country
        self.url = 'http://sms-activate.ru/stubs/handler_api.php'
        self.access_number = False
        self.activation_completed = False
        self.retries = 0

    def order_number(self):
        params = {
            'api_key': self.api_key,
            'action': 'getNumber',
            'service': 'tg',
            'country': self.country
        }
        r = requests.get(self.url, params)
        if 'ACCESS_NUMBER' in r.text:
            self.access_number = r.text.split(':')[1:]
            self.retries = 0
            return True

        if r.text == "NO_BALANCE" or r.text == 'NO_NUMBERS':
            if self.retries >= 10:
                raise Exception('retry_flood_order_number')
            self.retries = self.retries + 1
            print('Retrying to order number in 5 seconds')
            time.sleep(5)
            self.order_number()

    def change_status(self):
        params = {
            'api_key': self.api_key,
            'action': 'setStatus',
            'id': self.access_number[0],
            'status': 1
        }
        r = requests.get(self.url, params)
        if r.text == 'ACCESS_READY':
            return True
        else:
            time.sleep(5)
            self.change_status()

    def complete_activation(self):
        params = {
            'api_key': self.api_key,
            'action': 'setStatus',
            'id': self.access_number[0],
            'status': 6
        }
        r = requests.get(self.url, params)
        if r.text == 'ACCESS_ACTIVATION':
            self.activation_completed = True
            self.retries = 0
            return True
        else:
            if self.retries >= 10:
                # This is not fatal and we don't need to restart the work cycle
                return False
                # raise Exception('retry_flood_complete_activation_status')
            self.retries = self.retries + 1
            print('Retrying to complete activation status in 5 seconds')
            time.sleep(5)
            self.complete_activation()

    def deactivate_number(self):
        if self.activation_completed:
            return False
        params = {
            'api_key': self.api_key,
            'action': 'setStatus',
            'id': self.access_number[0],
            'status': 8
        }
        r = requests.get(self.url, params)
        if r.text == 'ACCESS_CANCEL':
            self.retries = 0
            return True
        else:
            if self.retries >= 10:
                raise Exception('retry_flood_cancel_activation_number')
            self.retries = self.retries + 1
            print('Retrying to cancel activation number in 5 seconds')
            time.sleep(5)
            self.deactivate_number()

    def get_activation_status(self):
        params = {
            'api_key': self.api_key,
            'action': 'getStatus',
            'id': self.access_number[0]
        }
        r = requests.get(self.url, params)

        if r.text == 'STATUS_CANCEL':
            raise Exception('activation_cancelled_from_server')

        if r.text == 'STATUS_WAIT_CODE':
            if self.retries >= 10:
                raise Exception('flood_retry_get_activation_status')
            time.sleep(10)
            print('Retrying to get activation code in 10 seconds')
            self.retries = self.retries + 1
            self.get_activation_status()

        if r.text == 'STATUS_WAIT_RESEND':
            # not sure how to handle for now
            # return False
            raise Exception('invalid_status_from_server')

        if 'STATUS_OK' in r.text:
            self.activation_code = r.text.split(':')[1]
            self.retries = 0
            return True
