from setuptools import find_packages, setup

setup(
    name='ya-courier-helpers',
    version='0.0.2',
    packages=find_packages(),
    url='https://github.com/roschupkin/ya.courier.helpers',
    license='Apache License 2.0',
    author='Yandex B2BGeo Team',
    author_email='b2bgeo@yandex-team.ru',
    description='Ya.Courier helper scripts',
    install_requires=[
        'requests',
        ],
    entry_points={
        'console_scripts': [
            'ya-courier-service-duration-uploader=ya_courier_helpers.order_service_duration_uploader:main',
            'ya-courier-multiorder-timeinterval-fixer=ya_courier_helpers.multiorder_time_interval_fixer:main',
        ]
    }
)
