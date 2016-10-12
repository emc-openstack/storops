# coding=utf-8
# Copyright (c) 2015 EMC Corporation.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
from __future__ import unicode_literals

import functools
import json
import logging
import os

from mock import patch

from storops.exception import MockFileNotFoundError
from storops.lib.common import cache, allow_omit_parentheses
from storops.unity.client import UnityClient
from storops.unity.resource.system import UnitySystem
from test.utils import ConnectorMock, read_test_file

__author__ = 'Cedric Zhuang'

log = logging.getLogger(__name__)


@cache
def t_rest():
    """ get the test unity client

    :return: unity client singleton
    """
    return UnityClient('10.244.223.61', 'admin', 'Password123!')


@cache
def t_unity():
    return UnitySystem('10.244.223.66', 'admin', 'Password123!')


class MockRestClient(ConnectorMock):
    base_folder = os.path.join('unity', 'rest_data')

    @classmethod
    def get_folder_from_url(cls, url):
        try:
            pos = url.index('?')
            url = url[:pos]
        except ValueError:
            pass
        return url.strip('/').split('/')[2]

    def get(self, url, **kwargs):
        return self._get_mock_output(url, kwargs)

    def post(self, url, **kwargs):
        return self._get_mock_output(url, kwargs)

    def delete(self, url, **kwargs):
        return self._get_mock_output(url, kwargs)

    @classmethod
    def get_folder(cls, inputs):
        url, body = inputs
        return os.path.join(cls.base_folder, cls.get_folder_from_url(url))

    @classmethod
    def get_filename(cls, inputs):
        url, body = inputs
        string_indices = cls.read_index(cls.get_folder(inputs))
        indices = json.loads(string_indices, encoding='utf-8')
        for index in indices.get('indices', []):
            if url.lower() != index['url'].lower():
                continue
            elif body and body != index.get('body', None):
                continue
            response = index['response']
            break
        else:
            raise MockFileNotFoundError('cannot find response for url: {}, \n'
                                        'body: {}'.format(url, body))
        return response

    @staticmethod
    @cache
    def read_index(folder):
        return read_test_file(folder, 'index.json')

    def _get_mock_output(self, url, kwargs):
        body = kwargs.get('body', '')
        resp_body = self.get_mock_output([url, body])
        if len(resp_body) > 0:
            ret = json.loads(resp_body)
        else:
            ret = None
        return ret


@allow_omit_parentheses
def patch_rest(output=None, mock_map=None):
    rest = MockRestClient(output, mock_map)

    def decorator(func):
        @functools.wraps(func)
        @patch(target='storops.connection.connector.UnityRESTConnector.get',
               new=rest.get)
        @patch(target='storops.connection.connector.UnityRESTConnector.post',
               new=rest.post)
        @patch(target='storops.connection.connector.UnityRESTConnector.delete',
               new=rest.delete)
        def func_wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        return func_wrapper

    return decorator
