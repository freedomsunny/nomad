#!/usr/bin/env python

from setuptools import setup, find_packages

setup(
    name="ops_nd",
    version='0.1',
    description="ops_nd lib",
    author="halfss",
    install_requires=[
        "SQLAlchemy",
        "psycopg2",
        "tornado",
        "eventlet",
        "redis",
        "requests",
        "netaddr",
    ],

    scripts=[
        "bin/ops_nd_api",
        "bin/ops_admin.py",
    ],

    packages=find_packages(),
    data_files=[
        ('/etc/ops_nd', ['etc/ops_nd.conf']),
        ('/var/log/ops_nd', []),
    ],
)
