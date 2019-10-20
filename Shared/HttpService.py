#!/usr/bin/env python3
import requests


class HttpService(object):
    @staticmethod
    def post(url: str, data: str):
        return requests.post(url=url,
                             data=data,
                             headers={'content-type': 'application/json'})

    @staticmethod
    def get(url: str, params=None):
        return requests.get(url=url, params=params)
