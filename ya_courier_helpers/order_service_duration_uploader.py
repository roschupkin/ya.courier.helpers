import argparse
import sys

from ya_courier_helpers.util import orders_batch_upload
from ya_courier_helpers.config import ORDERS_BATCH_API_URL

DELIMITER = '\t'
LINE_FORMAT = '<order_number>{}<service_duration_in_seconds>'.format(DELIMITER)


def parse_args():
    parser = argparse.ArgumentParser(usage=usage())

    parser.add_argument('--company-id', required=True, type=int, help='Your company ID in Ya.Courier')
    parser.add_argument('--token', required=True, help='Your Oauth token in Ya.Courier')

    return parser.parse_args()


def usage():
    return '\n\tcat input.txt | ya-courier-service-duration-uploader \\\n' + \
        '\t--token <YA.COURIER TOKEN> --company-id <YOUR COMPANY ID>\n\n' + \
        'Input file format for each line:\n' + \
        '{}\n\n'.format(LINE_FORMAT) + \
        'For Ya.Courier API documentation visit https://courier.common.yandex.ru/api/v1/howto\n\n'


def get_request_data(stream):
    number_duration_pairs = [line.split(DELIMITER) for line in stream]
    request_data = []

    for i, pair in enumerate(number_duration_pairs):
        if len(pair) == 2:
            request_data.append({'number': pair[0], 'service_duration_s': pair[1]})
        else:
            print('Line {} has incorrect format and is skipped. Format: {}'.format(i, LINE_FORMAT))

    return request_data


def get_api_url(company_id):
    return ORDERS_BATCH_API_URL.format(company_id)


def main():
    args = parse_args()
    request_data = get_request_data(sys.stdin)

    if request_data:
        response = orders_batch_upload(args.company_id, args.token, request_data)

        if response.status_code == 200:
            print('Data uploaded successfully:\n\tOrders updated: {updated}'.format(**response.json()))
        else:
            print('Nothing was changed. Error uploading data:')
            response_text = response.text
            print(response_text)
            if 'psycopg2.IntegrityError' in response_text:
                print('Most probably some orders were not created in Ya.Courier')
    else:
        print('Empty input data. No data was uploaded.')


if __name__ == '__main__':
    main()
