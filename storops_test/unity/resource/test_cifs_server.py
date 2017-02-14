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

import logging
from unittest import TestCase
from hamcrest import assert_that, equal_to, none, instance_of, only_contains, \
    raises

from storops.exception import UnityException, \
    UnityOneSmbServerPerNasServerError, UnityResourceNotFoundError, \
    UnityNetBiosNameExistedError
from storops.unity.resource.cifs_server import UnityCifsServer, \
    UnityCifsServerList
from storops.unity.resource.health import UnityHealth
from storops.unity.resource.interface import UnityFileInterfaceList
from storops.unity.resource.nas_server import UnityNasServer
from storops_test.unity.rest_mock import t_rest, patch_rest

__author__ = 'Cedric Zhuang'

log = logging.getLogger(__name__)


class UnityCifsServerTest(TestCase):
    @patch_rest
    def test_get_properties(self):
        server = UnityCifsServer('cifs_2', t_rest())
        assert_that(server.existed, equal_to(True))
        assert_that(server.name, equal_to('nas1130'))
        assert_that(server.description, none())
        assert_that(server.netbios_name, equal_to('NAS1130'))
        assert_that(server.domain, equal_to('win2012.dev'))
        assert_that(server.last_used_organizational_unit,
                    equal_to('ou=Computers,ou=EMC VNX'))
        assert_that(server.workgroup, none())
        assert_that(server.is_standalone, equal_to(False))
        assert_that(server.health, instance_of(UnityHealth))
        assert_that(server.nas_server, instance_of(UnityNasServer))
        assert_that(server.file_interfaces,
                    instance_of(UnityFileInterfaceList))
        assert_that(len(server.file_interfaces), equal_to(1))
        assert_that(server.smbca_supported, equal_to(True))
        assert_that(server.smb_multi_channel_supported, equal_to(True))
        assert_that(server.smb_protocol_versions,
                    only_contains('1.0', '2.0', '2.1', '3.0'))

    @patch_rest
    def test_get_all(self):
        servers = UnityCifsServerList(cli=t_rest())
        assert_that(len(servers), equal_to(1))

    @patch_rest
    def test_create_domain_not_specified(self):
        def f():
            UnityCifsServer.create(t_rest(), 'nas_2', name='c_server1')

        assert_that(f, raises(UnityException, 'domain has not been specified'))

    @patch_rest
    def test_create_password_criteria(self):
        def f():
            UnityCifsServer.create(t_rest(), 'nas_2', name='c_server1',
                                   workgroup='CEDRIC',
                                   local_password='password')

        assert_that(f, raises(UnityException, 'not meet the password policy'))

    @patch_rest
    def test_create_one_smb_server_allowed(self):
        def f():
            UnityCifsServer.create(t_rest(), 'nas_2', name='c_server1',
                                   workgroup='CEDRIC',
                                   local_password='Password123!')

        assert_that(f, raises(UnityOneSmbServerPerNasServerError,
                              'Only one SMB server'))

    @patch_rest
    def test_create_success(self):
        server = UnityCifsServer.create(t_rest(), 'nas_5', name='c_server1',
                                        workgroup='CEDRIC',
                                        local_password='Password123!')
        assert_that(server.workgroup, equal_to('CEDRIC'))

    @patch_rest
    def test_create_name_existed(self):
        def f():
            UnityCifsServer.create(t_rest(), 'nas_5', name='NAS1130',
                                   workgroup='CEDRIC',
                                   local_password='Password123!')

        assert_that(f, raises(UnityNetBiosNameExistedError, 'already exists'))

    @patch_rest
    def test_delete_cifs3(self):
        server = UnityCifsServer(_id='cifs_3', cli=t_rest())
        resp = server.delete(skip_domain_unjoin=True)
        assert_that(resp.is_ok(), equal_to(True))

    @patch_rest
    def test_delete_not_found(self):
        def f():
            server = UnityCifsServer(_id='cifs_10', cli=t_rest())
            server.delete()

        assert_that(f, raises(UnityResourceNotFoundError))

    @patch_rest
    def test_create_cifs_share_success(self):
        server = UnityCifsServer.get(_id='cifs_2', cli=t_rest())
        share = server.create_cifs_share('cs1', 'fs_8')
        assert_that(share.name, equal_to('cs1'))
        assert_that(share.existed, equal_to(True))

    @patch_rest
    def test_get_cifs_server_from_nas_server(self):
        server = UnityNasServer(_id='nas_2', cli=t_rest())
        server = UnityCifsServer.get(t_rest(), server)
        assert_that(server, instance_of(UnityCifsServer))
        assert_that(server.domain, equal_to('win2012.dev'))

    @patch_rest
    def test_get_from_id(self):
        server = UnityCifsServer.get(cli=t_rest(), _id='cifs_2')
        assert_that(server, instance_of(UnityCifsServer))
        assert_that(server.domain, equal_to('win2012.dev'))

    @patch_rest
    def test_get_from_cifs_server(self):
        cifs_2 = UnityCifsServer(_id='cifs_2', cli=t_rest())
        server = UnityCifsServer.get(cli=t_rest(), _id=cifs_2)
        assert_that(server.domain, equal_to('win2012.dev'))

    @patch_rest
    def test_cifs_server(self):
        server = UnityCifsServer(_id='cifs_2', cli=t_rest())
        log.debug('netbios name: {}'.format(server.netbios_name))
        return server
