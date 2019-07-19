import argparse
import json
from collections import defaultdict
from multiprocessing.dummy import Pool

import requests
import logging

from ya_courier_helpers.util import chunks, get_duplicates, post_request, \
    get_request, delete_request, get_mvrp_request, get_mvrp_solution, valid_date

FORMAT = '%(asctime)-15s %(levelname)-8s %(message)s'
logging.basicConfig(format=FORMAT, level=logging.INFO)


MAX_REF_LEN = 80


def get_routes(date):
    routes = get_request('routes?date={}'.format(date))
    return {x['number']: x for x in routes}


def get_orders(route_id):
    orders = get_request('orders?route_id={}'.format(route_id))
    return {x['number']: x for x in orders}


def upload_depot(depot, depot_address):
    data = {
        'number': depot.get('ref', str(depot['id'])),
        'name': depot.get('ref', str(depot['id'])),
        'address': depot_address,
        'lat': depot['point']['lat'],
        'lon': depot['point']['lon']
    }

    if 'service_duration_s' in depot:
        data['service_duration_s'] = depot['service_duration_s']

    if 'time_window' in depot:
        data['time_interval'] = depot['time_window']

    j = post_request('depots-batch', [data])
    assert j['inserted'] + j['updated'] == 1
    logging.info('Depot uploaded')


def upload_couriers(couriers):
    # j = post_request('couriers-batch', [{'number': c['ref'], 'name': c['ref']} for c in couriers])
    j = post_request('couriers-batch', [{'number': str(c['id']), 'name': c['ref']} for c in couriers])
    assert j['inserted'] + j['updated'] == len(couriers)
    logging.info('{} couriers uploaded'.format(len(couriers)))


def upload_routes(solution, depot):
    veh_dict = {
        v['id']: v for v in solution['vehicles']
    }

    j = post_request('routes-batch', [
        {
            'number': '{}-{}-{}'.format(veh_dict[r['vehicle_id']]['ref'], r['shift']['id'],
                                        solution['options']['date']),
            'date': solution['options']['date'],
            'depot_number': depot.get('ref', str(depot['id'])),
            # 'courier_number': veh_dict[r['vehicle_id']]['ref']
            'courier_number': str(r['vehicle_id'])
        } for r in solution['routes']
    ])
    assert j['inserted'] + j['updated'] == len(solution['routes'])
    logging.info('{} routes uploaded for date {}'.format(len(solution['routes']), solution['options']['date']))


def upload_orders(locations, solution, orders_dict, phone):
    loc2veh = {}
    loc2shift = {}
    loc2multi = {}
    for route in solution['routes']:
        for loc in route['route']:
            if loc['node']['type'] == 'location':
                loc2veh[loc['node']['value']['id']] = route['vehicle_id']
                loc2shift[loc['node']['value']['id']] = route['shift']['id']
                loc2multi[loc['node']['value']['id']] = loc['multi_order']

    veh_dict = {
        v['id']: v for v in solution['vehicles']
    }

    dropped_locations = {l['id']: l for l in solution['dropped_locations']}
    dropped_count = 0
    skipped_count = 0

    data = []
    for l in locations:
        if l['id'] in loc2veh and not l['ref'].startswith('respawn_') and not l['ref'].startswith('FAKE'):
            data.append({
                'number': l['ref'],
                'lat': l['point']['lat'],
                'lon': l['point']['lon'],
                'address': orders_dict[l['ref']].get('point_address', '-'),
                'phone': orders_dict[l['ref']].get('customer_phone', phone),
                'service_duration_s': 0 if loc2multi[l['id']] else l.get('service_duration_s', 0),
                'status': 'confirmed',
                'customer_name': orders_dict[l['ref']].get('customer_name', 'Клиентский сервис'),
                'weight': orders_dict[l['ref']].get('weight_kg', 0),
                'time_interval': l['time_window'],
                'route_number': '{}-{}-{}'.format(veh_dict[loc2veh[l['id']]]['ref'], loc2shift[l['id']],
                                                  solution['options']['date'])
            })
        elif l['id'] in dropped_locations:
            dropped_count += 1
            logging.error('Order {} is dropped. Skipping it.'.format(dropped_locations[l['id']]['ref']))
        else:
            skipped_count += 1
            logging.error('Order {} was skipped.'.format(l['ref']))

    j = post_request('orders-batch', data)
    assert j['inserted'] + j['updated'] == len(
        locations) - dropped_count - skipped_count, 'Requested: {}, Updated: {}, Inserted: {}'.format(len(locations),
                                                                                                      j['updated'],
                                                                                                      j['inserted'])
    logging.info('{} locations uploaded'.format(len(locations)))


def fix_orders(solution):
    veh_dict = {
        v['id']: v for v in solution['vehicles']
    }

    routes_dict = get_routes(solution['options']['date'])
    order_numbers_dict = get_request('order-numbers?date={}'.format(solution['options']['date']))

    for r in solution['routes']:
        route_number = '{}-{}-{}'.format(veh_dict[r['vehicle_id']]['ref'], r['shift']['id'],
                                         solution['options']['date'])
        route_id = routes_dict[route_number]['id']
        new_orders = [
            x['node']['value']['ref']
            for x in r['route']
            if x['node']['type'] == 'location'
            and not x['node']['value']['ref'].startswith('respawn_')
            and not x['node']['value']['ref'].startswith('FAKE')
        ]
        logging.info('Got {} new orders in route {}'.format(len(new_orders), route_number))

        j = get_request(
            url='orders?route_id={}'.format(route_id)
        )
        # logging.info([order_numbers_dict[str(x['id'])] for x in j])
        # logging.info(new_orders)
        old_orders = [
            order_numbers_dict[str(x['id'])]
            for x in j
            if order_numbers_dict[str(x['id'])] not in new_orders
        ]
        logging.info('Found {} old orders in route {}'.format(len(old_orders), route_number))

        try:
            delete_request(
                url='routes/{}/fix-orders'.format(route_id)
            )
            logging.info('Route {} was cleared from fixed orders'.format(route_number))
        except requests.HTTPError as e:
            if e.response.status_code in (422, 500):
                continue
            else:
                raise

        post_request(
            url='routes/{}/fix-orders'.format(route_id),
            data={'orders': old_orders + new_orders}
        )
        logging.info('Route {} with {}+{} orders was fixed'.format(route_number, len(old_orders), len(new_orders)))


def clear_fixed_orders(solution):
    veh_dict = {
        v['id']: v for v in solution['vehicles']
    }

    routes_dict = get_routes(solution['options']['date'])

    for r in solution['routes']:
        route_number = '{}-{}'.format(veh_dict[r['vehicle_id']]['ref'], solution['options']['date'])
        if route_number in routes_dict:
            route_id = routes_dict[route_number]['id']
            try:
                delete_request(
                    url='routes/{}/fix-orders'.format(route_id)
                )
                logging.info('Route {} was cleared from fixed orders'.format(route_number))
            except requests.HTTPError as e:
                if e.response.status_code in (422, 500):
                    continue
                else:
                    raise


def delete_route_and_orders(args):
    route_number, route = args
    orders_dict = get_orders(route['id'])

    for order_number, order in orders_dict.items():
        delete_request(
            url='orders/{}'.format(order['id'])
        )
    logging.info('{} orders from route {} were deleted'.format(len(orders_dict), route_number))

    delete_request(
        url='routes/{}'.format(route['id'])
    )
    logging.info('Route {} was deleted'.format(route_number))


def delete_routes_and_orders(date):
    routes_dict = get_routes(date)
    logging.info('Found {} routes for date {}'.format(len(routes_dict), date))

    with Pool(10) as p:
        p.map(delete_route_and_orders, routes_dict.items())

    logging.info('DATA DELETED SUCCESSFULLY')


def assert_solution(s):
    couriers_nums = [v['ref'] for v in s['vehicles']]
    duplicate_vehicle_nums = get_duplicates(couriers_nums)
    if duplicate_vehicle_nums:
        logging.error('Duplicate vehicles found: {}'.format(duplicate_vehicle_nums))
        for v in s['vehicles']:
            if v['ref'] == duplicate_vehicle_nums[0]:
                logging.error(json.dumps(v, indent=4))


def assert_request(r):
    orders_nums = [l['ref'] for l in r['locations']]
    duplicate_loc_nums = get_duplicates(orders_nums)
    if duplicate_loc_nums:
        logging.error('Duplicate locations found: {}'.format(duplicate_loc_nums))
        for l in r['locations']:
            if l['ref'] == duplicate_loc_nums[0]:
                logging.error(json.dumps(l, indent=4))


def upload_data(solver_request, solver_solution, orders_dict, depot_address, date=None, phone='+71111111111'):
    r = solver_request
    s = solver_solution

    assert_request(r)
    assert_solution(s)

    if date:
        s['options']['date'] = date
        r['options']['date'] = date

    logging.info('Uploading data for date: {}'.format(s['options']['date']))

    upload_depot(r['depot'], depot_address)
    upload_couriers([v for v in r['vehicles'] if v['id'] in [r['vehicle_id'] for r in s['routes']]])
    upload_routes(s, r['depot'])
    for chunk in chunks(r['locations'], 500):
        upload_orders(chunk, s, orders_dict, phone)
    fix_orders(s)

    logging.info('DATA UPLOADED SUCCESSFULLY')


def parse_args():
    parser = argparse.ArgumentParser(usage=usage())

    parser.add_argument('--task-id', required=True, help='Your MVRP task ID to upload to Ya.Courier')
    parser.add_argument('--date', type=valid_date, help='Upload data to this date')
    parser.add_argument('--clear', action='store_true', help='Clear ALL data for this date')

    return parser.parse_args()


def usage():
    return '\n\tYA_COURIER_TOKEN=<YA.COURIER TOKEN> YA_COURIER_COMPANY_ID=<YOUR COMPANY ID> ' + \
        'ya-courier-uploader --task-id <YOUR MVRP API TASK ID>\n\n' + \
        'This tool uploads MVRP solution to Ya.Courier Monitoring.\n\n' + \
        'For MVRP API documentation visit https://courier.common.yandex.ru/vrs/api/v1/doc\n' + \
        'For Ya.Courier API documentation visit https://courier.common.yandex.ru/api/v1/doc\n\n'


def main():
    args = parse_args()

    if args.clear:
        delete_routes_and_orders(args.date)
    else:
        req = get_mvrp_request(args.task_id)
        resp = get_mvrp_solution(args.task_id)

        assert len({loc['ref'] for loc in req['locations']}) == \
            len({loc['ref'][:MAX_REF_LEN] for loc in req['locations']}), \
            "Location ref length should be shorter than 80 characters"

        for loc in req['locations']:
            loc['ref'] = loc['ref'][:MAX_REF_LEN]

        for route in resp['result']['routes']:
            for node in route['route']:
                node['node']['value']['ref'] = node['node']['value']['ref'][:MAX_REF_LEN]

        upload_data(
            req,
            resp['result'],
            defaultdict(dict),
            req['depot'].get('ref', 'Склад'),
            date=args.date
        )


if __name__ == '__main__':
    main()
