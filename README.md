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
