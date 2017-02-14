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

from hamcrest import equal_to, assert_that, instance_of, raises

from storops.exception import UnityNfsAlreadyEnabledError, \
    UnityResourceNotFoundError
from storops.unity.resource.interface import UnityFileInterfaceList
from storops.unity.resource.nas_server import UnityNasServer
from storops.unity.resource.nfs_server import UnityNfsServer, \
    UnityNfsServerList
from storops_test.unity.rest_mock import t_rest, patch_rest

__author__ = 'Cedric Zhuang'


class UnityNfsServerTest(TestCase):
    @patch_rest
    def test_get_properties(self):
        server = UnityNfsServer('nfs_2', t_rest())
        assert_that(server.id, equal_to('nfs_2'))
        assert_that(server.nfs_v4_enabled, equal_to(True))
        assert_that(server.is_secure_enabled, equal_to(False))
        assert_that(server.is_extended_credentials_enabled, equal_to(False))
        assert_that(server.nas_server, instance_of(UnityNasServer))
        assert_that(server.file_interfaces,
                    instance_of(UnityFileInterfaceList))
        assert_that(str(server.credentials_cache_ttl), equal_to('0:15:00'))

    @patch_rest
    def test_get_all(self):
        servers = UnityNfsServerList(cli=t_rest())
        assert_that(len(servers), equal_to(1))

    @patch_rest
    def test_create_success(self):
        server = UnityNfsServer.create(t_rest(), 'nas_5', nfs_v4_enabled=True)
        assert_that(server.id, equal_to('nfs_3'))
        assert_that(server.nfs_v4_enabled, equal_to(True))

    @patch_rest
    def test_create_existed(self):
        def f():
            UnityNfsServer.create(t_rest(), 'nas_5', nfs_v4_enabled=False)

        assert_that(f, raises(UnityNfsAlreadyEnabledError, 'already enabled'))

    @patch_rest
    def test_delete_success(self):
        server = UnityNfsServer(_id='nfs_3', cli=t_rest())
        resp = server.delete()
        assert_that(resp.is_ok(), equal_to(True))

    @patch_rest
    def test_delete_not_found(self):
        def f():
            server = UnityNfsServer(_id='nfs_5', cli=t_rest())
            server.delete()

        assert_that(f, raises(UnityResourceNotFoundError))
