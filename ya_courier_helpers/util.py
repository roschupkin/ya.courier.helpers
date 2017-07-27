import argparse
import contextlib
import json
import warnings
from functools import partialmethod

from datetime import datetime, timedelta
import requests

from ya_courier_helpers.config import ORDERS_BATCH_API_URL, ORDERS_LIST_API_URL


def date_parser(date_str):
    try:
        return datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        raise argparse.ArgumentTypeError("Invalid date ({0}). Please, use format YYYY-MM-DD.".format(date_str))


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


def orders_list_by_date(company_id, token, date):
    with no_ssl_verification():
        return requests.get(url=ORDERS_LIST_API_URL.format(company_id, date),
                            headers=get_auth_header(token))


def parse_time(str_time):
    """
    Parses time in "15", "15:40", "15:40:01" formats.
    Returns timedelta object
    """
    sep_count = str_time.count(':')
    if sep_count == 2:
        t = datetime.strptime(str_time, '%H:%M:%S')
    elif sep_count == 1:
        t = datetime.strptime(str_time, '%H:%M')
    else:
        t = datetime.strptime(str_time, '%H')
    return timedelta(hours=t.hour, minutes=t.minute, seconds=t.second)


def parse_interval_sec(time_interval):
    """
    Parses time interval string separated by minus: "15:00 - 15:30".
    Time format can be any supported by parse_time.
    Returns (timedelta1, timedelta2) tuple.
    """
    t = time_interval.split('-')
    t = [v.strip() for v in t]
    return parse_time(t[0]).seconds, parse_time(t[1]).seconds
