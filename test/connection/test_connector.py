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

import mock

from storops.connection import connector


class UnityRESTConnectorTest(unittest.TestCase):

    @mock.patch('storops.connection.client.HTTPClient')
    def test_new_connector_verify_false(self, mocked_httpclient):

        connector.UnityRESTConnector('10.10.10.10',
                                     verify=False)

        mocked_httpclient.assert_called_with(
            base_url='https://10.10.10.10:443',
            headers=connector.UnityRESTConnector.HEADERS,
            auth=('admin', ''),
            insecure=True,
            ca_cert_path=None)

    @mock.patch('storops.connection.client.HTTPClient')
    def test_new_connector_verify_true(self, mocked_httpclient):

        connector.UnityRESTConnector('10.10.10.10',
                                     verify=True)

        mocked_httpclient.assert_called_with(
            base_url='https://10.10.10.10:443',
            headers=connector.UnityRESTConnector.HEADERS,
            auth=('admin', ''),
            insecure=False,
            ca_cert_path=None)

    @mock.patch('storops.connection.client.HTTPClient')
    def test_new_connector_verify_path(self, mocked_httpclient):

        connector.UnityRESTConnector('10.10.10.10',
                                     verify='/tmp/ca_cert.crt')

        mocked_httpclient.assert_called_with(
            base_url='https://10.10.10.10:443',
            headers=connector.UnityRESTConnector.HEADERS,
            auth=('admin', ''),
            insecure=False,
            ca_cert_path='/tmp/ca_cert.crt')
