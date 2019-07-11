import os


def is_int(s):
    try:
        int(s)
        return True
    except ValueError:
        return False


API_URL = 'https://courier.common.yandex.ru/api/v1'

YA_COURIER_TOKEN = os.environ.get('YA_COURIER_TOKEN')
if not YA_COURIER_TOKEN:
    raise ValueError('YA_COURIER_TOKEN environment variable is required')

COMPANY_ID = os.environ.get('YA_COURIER_COMPANY_ID')
if not COMPANY_ID or not is_int(COMPANY_ID):
    raise ValueError('COMPANY_ID environment variable is requried')
else:
    COMPANY_ID = int(COMPANY_ID)


YA_COURIER_URL = '{}/companies/{}'.format(API_URL, COMPANY_ID)
ORDERS_BATCH_API_URL = API_URL + '/companies/{}/orders-batch'
ORDERS_LIST_API_URL = API_URL + '/companies/{}/orders?date={}'
TIMEOUT = 60
MVRP_LOG_URL = 'https://courier.common.yandex.ru/vrs/api/v1/log/{}/{}'
