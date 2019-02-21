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

import hamcrest as hc

import storops
from storops.unity.resource import migration_object, remote_system
from storops_test.unity import rest_mock as mock

__author__ = 'Yong Huang'


class UnityMoveSessionTest(unittest.TestCase):
    @mock.patch_rest
    def test_get_properties(self):
        instance_id = 'root/emc:EMC_UIS_MigrationResourceLeaf\"%InstanceID=' \
                      'mo_17628%Name=APM00152904558%SystemName=VNX\"'
        wwn = '60:06:01:60:12:90:38:00:F7:99:07:16:BE:DF:E7:11'
        mo = migration_object.UnityMigrationObject.get(cli=mock.t_rest(),
                                                       _id='mo_17628')
        hc.assert_that(mo.id, hc.equal_to('mo_17628'))
        hc.assert_that(mo.type, hc.equal_to(storops.RemoteObjectTypeEnum.LUN))
        hc.assert_that(mo.instance_id, hc.equal_to(instance_id))
        hc.assert_that(mo.remote_id, hc.equal_to('541'))
        hc.assert_that(mo.name, hc.equal_to('lun-liangr'))
        hc.assert_that(mo.lun_info.is_thin, hc.equal_to(False))
        hc.assert_that(mo.lun_info.size, hc.equal_to(10737418240))
        hc.assert_that(mo.lun_info.wwn, hc.equal_to(wwn))
        hc.assert_that(mo.lun_info.storage_pool_name,
                       hc.equal_to('DAILY_1'))
        hc.assert_that(mo.lun_info.default_sp, hc.equal_to('1'))
        hc.assert_that(mo.remote_system.id, hc.equal_to('RS_65557'))

    @mock.patch_rest
    def test_get_collection(self):
        mo_list = migration_object.UnityMigrationObjectList.get(
            mock.t_rest())
        hc.assert_that(len(mo_list), hc.equal_to(3))
        hc.assert_that([mo.id for mo in mo_list],
                       hc.equal_to(['mo_8182', 'mo_17628', 'mo_17593']))

    @mock.patch_rest
    def test_discover(self):
        remote_sys = remote_system.UnityRemoteSystem(_id='RS_65557',
                                                     cli=mock.t_rest())
        resp = migration_object.UnityMigrationObject.discover(mock.t_rest(),
                                                              remote_sys)
        hc.assert_that(resp.is_ok(), hc.equal_to(True))
