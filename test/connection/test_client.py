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

import unittest

from hamcrest import assert_that, calling, equal_to, raises
import mock
from requests import exceptions

from storops.connection import client
from storops.connection import exceptions as storops_ex


class MockResponse(object):
    def __init__(self, text, status_code):
        self.text = text
        self.status_code = status_code


def _request_side_effect(method, url, **kwargs):
    response_map = {'right_url': MockResponse('OK', 200),
                    'right_url_json': MockResponse('{"id": "id_123"}', 200),
                    'bad_url': MockResponse('Failed', 404),
                    'bad_url_raise': MockResponse('Failed', 401)}
    return response_map[url]


class ClientModuleTest(unittest.TestCase):
    def test_on_error_callback_true(self):
        result = client._on_error_callback(exceptions.RequestException())
        assert_that(True, equal_to(result))

    def test_on_error_callback_false(self):
        result = client._on_error_callback(ValueError())
        assert_that(False, equal_to(result))

    def test_wait_callback(self):
        assert_that(8, equal_to(client._wait_callback(4)))


class HTTPClientTest(unittest.TestCase):

    def setUp(self):
        self.client = client.HTTPClient('https://10.10.10.10', {})

    def test_set_request_options_insecure_true(self):
        options = client.HTTPClient._set_request_options(insecure=False,
                                                         auth=None,
                                                         timeout=None,
                                                         ca_cert_path=None)
        assert_that(options, equal_to({'verify': True,
                                       'auth': None}))

    def test_set_request_options_insecure_true_path(self):
        options = client.HTTPClient._set_request_options(
            insecure=False, auth=None, timeout=None, ca_cert_path='/tmp.crt')
        assert_that(options, equal_to({'verify': '/tmp.crt',
                                       'auth': None}))

    def test_set_request_options_insecure_false(self):
        options = client.HTTPClient._set_request_options(
            insecure=True, auth=None, timeout=None, ca_cert_path='/tmp.crt')
        assert_that(options, equal_to({'verify': False,
                                       'auth': None}))

    def test_request_content_json(self):
        self.client.session.request = mock.MagicMock(
            side_effect=_request_side_effect)
        self.client.headers['Content-Type'] = 'application/json'

        resp, body = self.client.request('right_url_json', 'GET',
                                         body={"k_abc": "v_abc"})

        self.client.session.request.assert_called_with(
            'GET', 'right_url_json', auth=None, verify=True,
            headers={'Content-Type': 'application/json'},
            data='{"k_abc": "v_abc"}')
        assert_that(resp.status_code, equal_to(200))
        assert_that(body, equal_to({'id': 'id_123'}))

    def test_request_content_plain(self):
        self.client.session.request = mock.MagicMock(
            side_effect=_request_side_effect)

        resp, body = self.client.request('right_url', 'GET',
                                         body='{"k_abc": "v_abc"}')

        self.client.session.request.assert_called_with(
            'GET', 'right_url', auth=None, verify=True, headers={},
            data='{"k_abc": "v_abc"}')
        assert_that(resp.status_code, equal_to(200))
        assert_that(body, equal_to('OK'))

    def test_request_content_404(self):
        self.client.session.request = mock.MagicMock(
            side_effect=_request_side_effect)

        resp, body = self.client.request('bad_url', 'GET',
                                         body='{"k_abc": "v_abc"}')

        self.client.session.request.assert_called_with(
            'GET', 'bad_url', auth=None, verify=True, headers={},
            data='{"k_abc": "v_abc"}')
        assert_that(resp.status_code, equal_to(404))
        assert_that(body, equal_to('Failed'))

    @mock.patch('storops.connection.exceptions.from_response')
    def test_request_content_raise(self, mocked_from_response):
        self.client.session.request = mock.MagicMock(
            side_effect=_request_side_effect)
        mocked_from_response.return_value = storops_ex.HttpError()

        def _tmp_func():
            self.client.request('bad_url_raise', 'GET',
                                body='{"k_abc": "v_abc"}')
        assert_that(calling(_tmp_func),
                    raises(storops_ex.HttpError))

        self.client.session.request.assert_called_with(
            'GET', 'bad_url_raise', auth=None, verify=True,
            headers={},
            data='{"k_abc": "v_abc"}')

    @mock.patch(
        'storops.connection.client.HTTPClient._cs_request_with_retries')
    def test_cs_request(self, mocked_cs_request_with_retries):
        self.client.base_url = 'https://10.10.10.10'
        self.client._cs_request('/api/types/instance', 'GET')

        mocked_cs_request_with_retries.assert_called_with(
            'https://10.10.10.10/api/types/instance',
            'GET')

    def test_get_limit(self):
        self.client.retries = 99
        assert_that(99, equal_to(self.client._get_limit()))

    @mock.patch(
        'storops.connection.client.HTTPClient._cs_request')
    def test_get(self, mocked_cs_request):
        self.client.get('/api/types/instance')

        mocked_cs_request.assert_called_with(
            '/api/types/instance',
            'GET')

    @mock.patch(
        'storops.connection.client.HTTPClient._cs_request')
    def test_post(self, mocked_cs_request):
        self.client.post('/api/types/instance')

        mocked_cs_request.assert_called_with(
            '/api/types/instance',
            'POST')

    @mock.patch(
        'storops.connection.client.HTTPClient._cs_request')
    def test_put(self, mocked_cs_request):
        self.client.put('/api/types/instance')

        mocked_cs_request.assert_called_with(
            '/api/types/instance',
            'PUT')

    @mock.patch(
        'storops.connection.client.HTTPClient._cs_request')
    def test_delete(self, mocked_cs_request):
        self.client.delete('/api/types/instance')

        mocked_cs_request.assert_called_with(
            '/api/types/instance',
            'DELETE')
