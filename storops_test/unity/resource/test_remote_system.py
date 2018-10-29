# Copyright (c) 2018 Dell Inc. or its subsidiaries.
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
import unittest

import ddt
import hamcrest as hc

import storops
from storops.unity.resource import remote_system, health
from storops_test.unity import rest_mock as mock

__author__ = 'Ryan Liang'


@ddt.ddt
class UnityRemoteSystemTest(unittest.TestCase):
    @mock.patch_rest
    def test_get_properties(self):
        rs = remote_system.UnityRemoteSystem.get(cli=mock.t_rest(), _id='RS_0')
        hc.assert_that(rs.alt_management_address_list, hc.none())
        hc.assert_that(rs.connection_type,
                       hc.equal_to(storops.ReplicationCapabilityEnum.ASYNC))
        hc.assert_that(rs.health, hc.instance_of(health.UnityHealth))
        hc.assert_that(rs.health.value, hc.equal_to(storops.HealthEnum.OK))
        hc.assert_that(rs.id, hc.equal_to('RS_0'))
        hc.assert_that(rs.local_spa_interfaces,
                       hc.equal_to(['128.221.255.12']))
        hc.assert_that(rs.local_spb_interfaces,
                       hc.equal_to(['128.221.255.13']))
        hc.assert_that(rs.management_address, hc.equal_to('10.245.101.39'))
        hc.assert_that(rs.model, hc.equal_to('Unity 500'))
        hc.assert_that(rs.name, hc.equal_to('FNM00150600267'))
        hc.assert_that(rs.remote_spa_interfaces,
                       hc.equal_to(['128.221.255.12']))
        hc.assert_that(rs.remote_spb_interfaces,
                       hc.equal_to(['128.221.255.13']))
        hc.assert_that(rs.serial_number, hc.equal_to('FNM00150600267'))
        hc.assert_that(rs.sync_fc_ports, hc.equal_to(['spa_fc4', 'spb_fc4']))
        hc.assert_that(rs.username, hc.equal_to('admin'))

    @mock.patch_rest
    def test_get_collection(self):
        rs_list = remote_system.UnityRemoteSystemList.get(mock.t_rest())
        hc.assert_that(len(rs_list), hc.equal_to(2))
        hc.assert_that([rs.id for rs in rs_list],
                       hc.equal_to(['RS_0', 'RS_4']))

    @mock.patch_rest
    @ddt.data({'management_address': '1.1.1.1',
               'local_username': None, 'local_password': None,
               'remote_username': None, 'remote_password': None,
               'connection_type': None},
              {'management_address': '1.1.1.1',
               'local_username': 'admin', 'local_password': 'password',
               'remote_username': 'admin', 'remote_password': 'password',
               'connection_type': storops.ReplicationCapabilityEnum.BOTH})
    @ddt.unpack
    def test_create(self, management_address, local_username, local_password,
                    remote_username, remote_password, connection_type):
        rs = remote_system.UnityRemoteSystem.create(
            mock.t_rest(), management_address,
            local_username=local_username, local_password=local_password,
            remote_username=remote_username, remote_password=remote_password,
            connection_type=connection_type)
        hc.assert_that(rs.id, hc.equal_to('RS_4'))

    @mock.patch_rest
    @ddt.data({'management_address': '1.1.1.1',
               'username': 'admin', 'password': 'password',
               'connection_type': storops.ReplicationCapabilityEnum.BOTH})
    @ddt.unpack
    def test_modify(self, management_address, username, password,
                    connection_type):
        rs = remote_system.UnityRemoteSystem.get(cli=mock.t_rest(), _id='RS_0')
        resp = rs.modify(management_address=management_address,
                         username=username, password=password,
                         connection_type=connection_type)
        hc.assert_that(resp.is_ok(), hc.equal_to(True))

    @mock.patch_rest
    @ddt.data({'connection_type': storops.ReplicationCapabilityEnum.BOTH})
    @ddt.unpack
    def test_verify(self, connection_type):
        rs = remote_system.UnityRemoteSystem.get(cli=mock.t_rest(), _id='RS_0')
        resp = rs.verify(connection_type=connection_type)
        hc.assert_that(resp.is_ok(), hc.equal_to(True))
