import contextlib
import json
import warnings
from functools import partialmethod

import requests

from ya_courier_helpers.config import ORDERS_BATCH_API_URL


@contextlib.contextmanager
def no_ssl_verification():
    old_request = requests.Session.request
    requests.Session.request = partialmethod(old_request, verify=False)
    warnings.filterwarnings('ignore', 'Unverified HTTPS request')
    yield
    warnings.resetwarnings()
    requests.Session.request = old_request


def get_auth_header(token):
    return {
        'Authorization': 'Auth {}'.format(token),
        'Content-Type': 'application/json'
    }


def orders_batch_upload(company_id, token, data):
    with no_ssl_verification():
        return requests.post(url=ORDERS_BATCH_API_URL.format(company_id),
                             data=json.dumps(data),
                             headers=get_auth_header(token))
