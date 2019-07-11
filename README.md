# Ya.Courier helper scripts

## Prerequisites
- Python 3
- virtualenv usage is recommended 

## Installation

```sh
$ pip3 install git+https://github.com/roschupkin/ya.courier.helpers.git
```

## Usage

- Follow the embedded documentation:

```sh
$ ya-courier-service-duration-uploader -h
usage: 
        cat input.txt | ya-courier-service-duration-uploader \
        --token <YA.COURIER TOKEN> --company-id <YOUR COMPANY ID>

This tool gets from stdin a list of orders with service duration in secs and uploads it to Ya.Courier.

Input file format for each line:
<order_number>  <service_duration_in_seconds>

For Ya.Courier API documentation visit https://courier.common.yandex.ru/api/v1/howto

optional arguments:
  -h, --help            show this help message and exit
  --company-id COMPANY_ID
                        Your company ID in Ya.Courier
  --token TOKEN         Your Oauth token in Ya.Courier
```

```sh
$ ya-courier-multiorder-timeinterval-fixer -h                  
usage: 
        ya-courier-multiorder-timeinterval-fixer \
        --token <YA.COURIER TOKEN> --company-id <YOUR COMPANY ID> --date YYYY-MM-DD

This tool gets a list of orders for the date and searches for orders with the same phone number.
 If these orders have different time intervals, it chooses the minimum one and change other orders with it.

For Ya.Courier API documentation visit https://courier.common.yandex.ru/api/v1/howto

optional arguments:
  -h, --help            show this help message and exit
  --company-id COMPANY_ID
                        Your company ID in Ya.Courier
  --token TOKEN         Your Oauth token in Ya.Courier
  --date DATE           The date you want to fix
```

```sh
YA_COURIER_TOKEN=AQAA YA_COURIER_COMPANY_ID=1 ya-courier-solution-uploader -h 
usage: 
        YA_COURIER_TOKEN=<YA.COURIER TOKEN> YA_COURIER_COMPANY_ID=<YOUR COMPANY ID> ya-courier-uploader --task-id <YOUR MVRP API TASK ID>

This tool uploads MVRP solution to Ya.Courier Monitoring.

For MVRP API documentation visit https://courier.common.yandex.ru/vrs/api/v1/doc
For Ya.Courier API documentation visit https://courier.common.yandex.ru/api/v1/doc

optional arguments:
  -h, --help         show this help message and exit
  --task-id TASK_ID  Your MVRP task ID to upload to Ya.Courier
  --date DATE        Upload data to this date
  --clear            Clear ALL data for this date
```
