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

from unittest import TestCase

from hamcrest import assert_that, equal_to, only_contains, instance_of, raises

from storops.exception import UnityOneDnsPerNasServerError, \
    UnityResourceNotFoundError
from storops.unity.resource.dns_server import UnityFileDnsServerList, \
    UnityFileDnsServer
from storops.unity.resource.nas_server import UnityNasServer
from storops_test.unity.rest_mock import t_rest, patch_rest

__author__ = 'Cedric Zhuang'


class UnityFileDnsServerTest(TestCase):
    @patch_rest
    def test_get_properties(self):
        server = UnityFileDnsServer('dns_2', cli=t_rest())
        assert_that(server.existed, equal_to(True))
        assert_that(server.addresses, only_contains('10.244.209.72'))
        assert_that(server.domain, equal_to('win2012.dev'))
        assert_that(server.nas_server, instance_of(UnityNasServer))

    @patch_rest
    def test_get_all(self):
        servers = UnityFileDnsServerList(cli=t_rest())
        assert_that(len(servers), equal_to(1))

    @patch_rest
    def test_create_one_dns_each_nas_server(self):
        def f():
            UnityFileDnsServer.create(t_rest(), 'nas_2', 'emc.dev',
                                      ['2.2.2.2', '3.3.3.3'])

        assert_that(f, raises(UnityOneDnsPerNasServerError, 'Only one DNS'))

    @patch_rest
    def test_create_success(self):
        server = UnityNasServer.get(t_rest(), 'nas_4')
        dns = UnityFileDnsServer.create(t_rest(), server, 'emc.dev',
                                        ['2.2.2.2', '3.3.3.3'])
        assert_that(dns.addresses, only_contains('2.2.2.2', '3.3.3.3'))

    @patch_rest
    def test_delete_not_found(self):
        def f():
            UnityFileDnsServer.get(t_rest(), 'dns_30').delete()

        assert_that(f, raises(UnityResourceNotFoundError, 'does not exist'))
