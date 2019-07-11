import argparse
import contextlib
import json
import logging
import warnings
from functools import partialmethod
from datetime import datetime, timedelta
import requests
from retrying import retry

from ya_courier_helpers.config import ORDERS_BATCH_API_URL, ORDERS_LIST_API_URL, YA_COURIER_TOKEN, YA_COURIER_URL, \
    MVRP_LOG_URL


SESSION = requests.Session()


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


def chunks(l, n):
    for i in range(0, len(l), n):
        yield l[i:i + n]


def get_duplicates(l):
    seen = {}
    dupes = []

    for x in l:
        if x not in seen:
            seen[x] = 1
        else:
            if seen[x] == 1:
                dupes.append(x)
            seen[x] += 1

    return dupes


def get_mvrp_solution(solution_id):
    return request(MVRP_LOG_URL.format('response', solution_id), 'get')


def get_mvrp_request(solution_id):
    return request(MVRP_LOG_URL.format('request', solution_id), 'get')


@retry(retry_on_exception=lambda x: isinstance(x, (requests.exceptions.Timeout,
                                                   requests.exceptions.ConnectionError)),
       wait_random_min=0,
       wait_random_max=2000,
       stop_max_attempt_number=3
       )
def request(url, method, data=None):
    r = SESSION.request(
        url=url,
        method=method,
        data=json.dumps(data) if data else None,
        headers=get_auth_header(YA_COURIER_TOKEN)
    )
    if r.status_code >= 400:
        logging.error(r.text)
    r.raise_for_status()
    return r.json()


def get_ya_courier_url(url):
    return '{}/{}'.format(YA_COURIER_URL, url)


def post_request(url, data):
    return request(get_ya_courier_url(url), 'post', data)


def get_request(url):
    return request(get_ya_courier_url(url), 'get')


def delete_request(url):
    return request(get_ya_courier_url(url), 'delete')


def valid_date(s):
    if not s:
        return None
    try:
        if datetime.strptime(s, '%Y-%m-%d'):
            return s
        else:
            raise ValueError()
    except ValueError:
        msg = "Not a valid date: '{0}'.".format(s)
        raise argparse.ArgumentTypeError(msg)
