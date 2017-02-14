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

from storops.exception import UnityException, UnityIpAddressUsedError, \
    UnityResourceNotFoundError
from storops.unity.enums import IpProtocolVersionEnum, FileInterfaceRoleEnum
from storops.unity.resource.health import UnityHealth
from storops.unity.resource.interface import UnityFileInterface, \
    UnityFileInterfaceList, UnityPreferredInterfaceSettings, \
    UnityPreferredInterfaceSettingsList
from storops.unity.resource.nas_server import UnityNasServer
from storops.unity.resource.port import UnityIpPort
from storops_test.unity.rest_mock import t_rest, patch_rest

__author__ = 'Cedric Zhuang'


class UnityFileInterfaceTest(TestCase):
    @patch_rest
    def test_get_properties(self):
        fi = UnityFileInterface('if_16', cli=t_rest())
        assert_that(fi.existed, equal_to(True))
        assert_that(fi.nas_server, instance_of(UnityNasServer))
        assert_that(fi.ip_port, instance_of(UnityIpPort))
        assert_that(fi.health, instance_of(UnityHealth))
        assert_that(fi.ip_address, equal_to('10.244.220.120'))
        assert_that(fi.ip_protocol_version,
                    equal_to(IpProtocolVersionEnum.IPv4))
        assert_that(fi.netmask, equal_to('255.255.255.0'))
        assert_that(fi.gateway, equal_to('10.244.220.1'))
        assert_that(fi.mac_address, equal_to('00:60:16:5C:08:E1'))
        assert_that(fi.name, equal_to('8_FNM00151200215'))
        assert_that(fi.role, equal_to(FileInterfaceRoleEnum.PRODUCTION))
        assert_that(fi.is_preferred, equal_to(True))
        assert_that(fi.is_disabled, equal_to(False))

    @patch_rest
    def test_get_all(self):
        fi_list = UnityFileInterfaceList(cli=t_rest())
        assert_that(len(fi_list), equal_to(1))

    @patch_rest
    def test_create_error_nas_server_not_found(self):
        def f():
            UnityFileInterface.create(
                t_rest(), 'nas_1', 'spa_eth2', '1.1.1.1',
                role=FileInterfaceRoleEnum.PRODUCTION)

        assert_that(f, raises(UnityException, 'Cannot find'))

    @patch_rest
    def test_create_success(self):
        fi = UnityFileInterface.create(
            t_rest(), 'nas_2', 'spa_eth2', '1.1.1.1',
            role=FileInterfaceRoleEnum.PRODUCTION)
        assert_that(fi.ip_address, equal_to('1.1.1.1'))

    @patch_rest
    def test_ip_address_in_use(self):
        def f():
            UnityFileInterface.create(
                t_rest(), 'nas_2', 'spa_eth2', '1.1.1.2',
                role=FileInterfaceRoleEnum.PRODUCTION)

        assert_that(f, raises(UnityIpAddressUsedError, 'already in use'))

    @patch_rest
    def test_delete_success(self):
        fi = UnityFileInterface(_id='if_20', cli=t_rest())
        resp = fi.delete()
        assert_that(resp.is_ok(), equal_to(True))

    @patch_rest
    def test_delete_not_found(self):
        def f():
            fi = UnityFileInterface(_id='if_25', cli=t_rest())
            fi.delete()

        assert_that(f, raises(UnityResourceNotFoundError, 'does not exist'))


class UnityPreferredInterfaceSettingsTest(TestCase):
    @patch_rest
    def test_get_properties(self):
        pis = UnityPreferredInterfaceSettings('preferred_if_2', cli=t_rest())
        assert_that(pis.existed, equal_to(True))
        assert_that(pis.nas_server, instance_of(UnityNasServer))

    @patch_rest
    def test_get_all(self):
        pis_list = UnityPreferredInterfaceSettingsList(cli=t_rest())
        assert_that(len(pis_list), equal_to(1))
