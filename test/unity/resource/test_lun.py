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

from hamcrest import assert_that, only_contains, instance_of, contains_string
from hamcrest import equal_to
from storops.unity.resource.host import UnityBlockHostAccessList, UnityHost

from storops import UnitySystem
from storops.unity.resource.lun import UnityLun, UnityLunList
from storops.unity.resource.pool import UnityPool
from storops.unity.enums import HostLUNAccessEnum, NodeEnum
from storops.unity.resource.storage_resource import UnityStorageResource
from storops.unity.resource.sp import UnityStorageProcessor
from test.unity.rest_mock import t_rest, patch_rest

__author__ = 'Cedric Zhuang'


class UnityLunTest(TestCase):
    @patch_rest()
    def test_get_lun_sv2_simple_property(self):
        lun = UnityLun(_id='sv_2', cli=t_rest())
        assert_that(lun.existed, equal_to(True))
        assert_that(lun.id, equal_to('sv_2'))
        assert_that(lun.name, equal_to('openstack_lun'))
        assert_that(lun.description, equal_to('sample'))
        assert_that(lun.size_total, equal_to(107374182400))
        assert_that(lun.size_allocated, equal_to(0))
        assert_that(lun.per_tier_size_used, only_contains(2952790016, 0, 0))
        assert_that(lun.is_thin_enabled, equal_to(True))
        assert_that(lun.wwn, equal_to(
            '60:06:01:60:17:50:3C:00:C2:0A:D5:56:92:D1:BA:12'))
        assert_that(lun.is_replication_destination, equal_to(False))
        assert_that(lun.is_snap_schedule_paused, equal_to(False))
        assert_that(lun.metadata_size, equal_to(5100273664))
        assert_that(lun.metadata_size_allocated, equal_to(2684354560))
        assert_that(lun.snap_wwn, equal_to(
            '60:06:01:60:17:50:3C:00:C4:0A:D5:56:00:95:DE:11'))
        assert_that(lun.snaps_size, equal_to(0))
        assert_that(lun.snaps_size_allocated, equal_to(0))
        assert_that(lun.snap_count, equal_to(0))
        assert_that(lun.storage_resource, instance_of(UnityStorageResource))
        assert_that(lun.pool, instance_of(UnityPool))

    @patch_rest()
    def test_lun_modify_host_access(self):
        host = UnityHost(_id="Host_1", cli=t_rest())
        lun = UnityLun(_id='sv_4', cli=t_rest())
        host_access = [{'host': host, 'accessMask': HostLUNAccessEnum.BOTH}]
        lun.modify(host_access=host_access)
        lun.update()
        assert_that(lun.host_access[0].host, equal_to(host))
        assert_that(lun.host_access[0].access_mask,
                    equal_to(HostLUNAccessEnum.BOTH))

    @patch_rest()
    def test_lun_modify_sp(self):
        lun = UnityLun(_id='sv_4', cli=t_rest())
        sp = UnityStorageProcessor(_id='spb', cli=t_rest())
        lun.modify(sp=sp)
        lun.update()
        assert_that(sp.to_node_enum(), equal_to(NodeEnum.SPB))

    @patch_rest()
    def test_lun_modify_none(self):
        lun = UnityLun(_id='sv_4', cli=t_rest())
        resp = lun.modify(host_access=None)
        lun.update()
        assert_that(resp.is_ok(), equal_to(True))

    @patch_rest()
    def test_lun_modify_wipe_host_access(self):
        lun = UnityLun(_id='sv_4', cli=t_rest())
        resp = lun.modify(host_access=[])
        lun.update()
        assert_that(resp.is_ok(), equal_to(True))

    @patch_rest()
    def test_lun_modify_muitl_property_except_sp(self):
        lun = UnityLun(_id='sv_4', cli=t_rest())
        lun.modify(name="RestLun100", is_thin=True,
                   description="Lun description")
        lun.update()
        assert_that(lun.name, equal_to('RestLun100'))
        assert_that(lun.description, equal_to('Lun description'))

    @patch_rest()
    def test_lun_delete(self):
        lun = UnityLun(_id='sv_4', cli=t_rest())
        resp = lun.delete(force_snap_delete=True, force_vvol_delete=True)
        lun.update()
        assert_that(resp.is_ok(), equal_to(True))
        assert_that(resp.job.existed, equal_to(False))

    @patch_rest()
    def test_lun_attch_to_new_host(self):
        host = UnityHost(_id="Host_10", cli=t_rest())
        lun = UnityLun(_id='sv_4', cli=t_rest())
        resp = lun.attach_to(host)
        assert_that(resp.is_ok(), equal_to(True))

    @patch_rest()
    def test_lun_attch_to_same_host(self):
        host = UnityHost(_id="Host_1", cli=t_rest())
        lun = UnityLun(_id='sv_4', cli=t_rest())
        resp = lun.attach_to(host, access_mask=HostLUNAccessEnum.BOTH)
        assert_that(resp.is_ok(), equal_to(True))

    @patch_rest()
    def test_lun_detach_from_host(self):
        host = UnityHost(_id="Host_1", cli=t_rest())
        lun = UnityLun(_id='sv_4', cli=t_rest())
        resp = lun.detach_from(host)
        assert_that(resp.is_ok(), equal_to(True))

    @patch_rest()
    def test_get_lun_sv2_nested_property_update_property(self):
        lun = UnityLun(_id='sv_2', cli=t_rest())
        sr = lun.storage_resource
        assert_that(sr._cli, equal_to(t_rest()))
        assert_that(sr.size_total, equal_to(107374182400))

    @patch_rest()
    def test_get_lun_sv3_nested_property_no_update(self):
        lun = UnityLunList.get(_id='sv_3', cli=t_rest())
        sr = lun.storage_resource
        assert_that(sr._cli, equal_to(t_rest()))

    @patch_rest()
    def test_get_lun_all_0(self):
        lun_list = UnityLunList.get(cli=t_rest())
        assert_that(len(lun_list), equal_to(5))

    @patch_rest()
    def test_get_lun_doc(self):
        lun = UnityLun(_id='sv_2', cli=t_rest())
        doc = lun.doc
        assert_that(doc,
                    contains_string('Represents Volume, LUN, Virtual Disk.'))
        assert_that(doc, contains_string('current_node'))
        assert_that(doc, contains_string('Current SP'))

    @patch_rest()
    def test_get_lun_with_host_access(self):
        unity = UnitySystem('10.109.22.101', 'admin', 'Password123!')
        lun = unity.get_lun(_id='sv_567')
        assert_that(lun.host_access, instance_of(UnityBlockHostAccessList))
        access = lun.host_access[0]
        assert_that(access.access_mask, equal_to(HostLUNAccessEnum.PRODUCTION))
        assert_that(access.host, instance_of(UnityHost))
        assert_that(access.host.id, equal_to('Host_1'))
