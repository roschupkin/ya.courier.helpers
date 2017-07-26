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
        cat input.txt | ya-courier-uploader \
        --token <YA.COURIER TOKEN> --company-id <YOUR COMPANY ID>

Input file format for each line:
<order_number> <service_duration_in_seconds>

For Ya.Courier API documentation visit https://courier.common.yandex.ru/api/v1/howto

optional arguments:
  -h, --help            show this help message and exit
  --company-id COMPANY_ID
                        Your company ID in Ya.Courier
  --token TOKEN         Your Oauth token in Ya.Courier
```
