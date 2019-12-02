import argparse
from collections import defaultdict

from ya_courier_helpers.util import orders_batch_upload, orders_list_by_date, date_parser, parse_interval_sec


def parse_args():
    parser = argparse.ArgumentParser(usage=usage())

    parser.add_argument('--company-id', required=True, type=int, help='Your company ID in Ya.Courier')
    parser.add_argument('--token', required=True, help='Your Oauth token in Ya.Courier')

    parser.add_argument('--date', required=True, type=date_parser, help='The date you want to fix')

    return parser.parse_args()


def usage():
    return '\n\tya-courier-multiorder-timeinterval-fixer \\\n' + \
        '\t--token <YA.COURIER TOKEN> --company-id <YOUR COMPANY ID> --date YYYY-MM-DD\n\n' + \
        'This tool gets a list of orders for the date and searches for orders with the same phone number.\n If ' + \
        'these orders have different time intervals, it chooses the minimum one and change other orders with it.\n\n' +\
        'For Ya.Courier API documentation visit https://courier.yandex.ru/api/v1/howto\n\n'


def fix_time_intervals(orders):
    # We want different orders for one customer (identified by phone) to have the same time interval so
    # we group orders by phones

    orders_by_phones = defaultdict(list)
    for order in orders:
        if order['phone']:
            orders_by_phones[order['phone']].append({
                'number': order['number'],
                'time_interval': order['time_interval']
            })

    fixed_orders = []
    for phone, orders in orders_by_phones.items():
        if len(orders) == 1:
            pass
        else:
            # One customer has a few orders. Let's check their time intervals.
            # Do nothing if they are already the same.

            time_intervals = {order['time_interval'] for order in orders}
            if len(time_intervals) == 1:
                pass
            else:
                # Let's get the earliest time interval
                min_time_interval = sorted(time_intervals, key=parse_interval_sec)[0]

                for order_time in orders:
                    if order_time['time_interval'] != min_time_interval:
                        print('{}: {} -> {}'.format(order_time['number'], order_time['time_interval'], min_time_interval))
                        order_time['time_interval'] = min_time_interval
                        fixed_orders.append(order_time)

    return fixed_orders


def main():
    args = parse_args()
    response = orders_list_by_date(args.company_id, args.token, args.date)

    if response.status_code == 200:
        fixed_orders = fix_time_intervals(response.json())

        if fixed_orders:
            response = orders_batch_upload(args.company_id, args.token, fixed_orders)

            if response.status_code == 200:
                print('Data uploaded successfully:\n\tOrders updated: {updated}'.format(**response.json()))
            else:
                print('Nothing was changed. Error uploading data:')
                response_text = response.text
                print(response_text)
                if 'psycopg2.IntegrityError' in response_text:
                    print('Most probably some orders were not created in Ya.Courier')

        else:
            print('Empty input data. No multiorders detected.')

    else:
        print('Error occured while getting orders by date:')
        print(response.status_code)
        print(response.text)


if __name__ == '__main__':
    main()
