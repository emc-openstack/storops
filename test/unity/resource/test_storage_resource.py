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

from hamcrest import assert_that, equal_to, instance_of, has_items, raises, \
    contains_string

from storops.exception import UnityStorageResourceNameInUseError, \
    UnityConsistencyGroupNameInUseError, UnityResourceNotFoundError, \
    UnityNothingToModifyError, UnityHostAccessAlreadyExistsError
from storops.unity.enums import StorageResourceTypeEnum, ReplicationTypeEnum, \
    ThinStatusEnum, TieringPolicyEnum, HostLUNAccessEnum
from storops.unity.resource.filesystem import UnityFileSystem
from storops.unity.resource.health import UnityHealth
from storops.unity.resource.host import UnityHost
from storops.unity.resource.lun import UnityLun
from storops.unity.resource.pool import UnityPoolList
from storops.unity.resource.snap import UnitySnap
from storops.unity.resource.storage_resource import UnityStorageResource, \
    UnityStorageResourceList, UnityConsistencyGroup, UnityConsistencyGroupList
from test.unity.rest_mock import t_rest, patch_rest

__author__ = 'Cedric Zhuang'


class UnityStorageResourceTest(TestCase):
    @patch_rest
    def test_get_properties(self):
        sr = UnityStorageResource(_id='res_27', cli=t_rest())
        assert_that(sr.id, equal_to('res_27'))
        assert_that(sr.type, equal_to(StorageResourceTypeEnum.FILE_SYSTEM))
        assert_that(sr.replication_type, equal_to(ReplicationTypeEnum.NONE))
        assert_that(sr.thin_status, equal_to(ThinStatusEnum.TRUE))
        assert_that(sr.relocation_policy,
                    equal_to(TieringPolicyEnum.AUTOTIER_HIGH))
        assert_that(sr.health, instance_of(UnityHealth))
        assert_that(sr.name, equal_to('fs3'))
        assert_that(sr.description, equal_to(''))
        assert_that(sr.is_replication_destination, equal_to(False))
        assert_that(sr.size_total, equal_to(3221225472))
        assert_that(sr.size_used, equal_to(1620303872))
        assert_that(sr.size_allocated, equal_to(3221225472))
        assert_that(sr.per_tier_size_used, equal_to([6442450944, 0, 0]))
        assert_that(sr.metadata_size, equal_to(3489660928))
        assert_that(sr.metadata_size_allocated, equal_to(3221225472))
        assert_that(sr.snaps_size_total, equal_to(0))
        assert_that(sr.snaps_size_allocated, equal_to(0))
        assert_that(sr.snap_count, equal_to(0))
        assert_that(sr.pools, instance_of(UnityPoolList))
        assert_that(sr.filesystem, instance_of(UnityFileSystem))

    @patch_rest
    def test_get_all(self):
        sr_list = UnityStorageResourceList(cli=t_rest())
        assert_that(len(sr_list), equal_to(10))


class UnityConsistencyGroupTest(TestCase):
    cg_type = StorageResourceTypeEnum.CONSISTENCY_GROUP

    @staticmethod
    def get_cg():
        return UnityConsistencyGroup(cli=t_rest(), _id='res_19')

    @patch_rest
    def test_get_properties(self):
        cg = UnityConsistencyGroup(_id='res_13', cli=t_rest())
        assert_that(cg.id, equal_to('res_13'))
        assert_that(cg.type, equal_to(self.cg_type))

    @patch_rest
    def test_get_cg_list(self):
        cg_list = UnityConsistencyGroupList(cli=t_rest())
        assert_that(len(cg_list), equal_to(2))
        for cg in cg_list:
            assert_that(cg, instance_of(UnityConsistencyGroup))

    @patch_rest
    def test_create_empty_cg(self):
        cg = UnityConsistencyGroup.create(t_rest(), 'Goddess')
        assert_that(cg.name, equal_to('Goddess'))
        assert_that(cg.type, equal_to(self.cg_type))

    @patch_rest
    def test_create_cg_with_initial_member(self):
        lun1 = UnityLun(cli=t_rest(), _id='sv_3339')
        lun2 = UnityLun(cli=t_rest(), _id='sv_3340')
        cg = UnityConsistencyGroup.create(t_rest(), 'Muse',
                                          lun_list=[lun1, lun2])
        assert_that(cg.name, equal_to('Muse'))

        members = cg.luns
        assert_that(len(members), equal_to(2))
        lun_id_list = map(lambda lun: lun.get_id(), members)
        assert_that(lun_id_list, has_items('sv_3339', 'sv_3340'))

    @patch_rest
    def test_create_cg_with_hosts(self):
        lun1 = UnityLun(cli=t_rest(), _id='sv_3338')
        host1 = UnityHost(cli=t_rest(), _id='Host_14')
        host2 = UnityHost(cli=t_rest(), _id='Host_15')
        cg = UnityConsistencyGroup.create(
            t_rest(), 'Muse', lun_list=[lun1], hosts=[host1, host2])
        hosts = cg.block_host_access

        assert_that(len(hosts), equal_to(2))
        for mask in hosts.access_mask:
            assert_that(mask, equal_to(HostLUNAccessEnum.BOTH))

    @patch_rest
    def test_create_cg_name_in_use(self):
        def f():
            UnityConsistencyGroup.create(t_rest(), 'in_use')

        assert_that(f, raises(UnityConsistencyGroupNameInUseError, 'used'))

    @patch_rest
    def test_delete_cg_normal(self):
        cg = UnityConsistencyGroup(cli=t_rest(), _id='res_18')
        resp = cg.delete()
        assert_that(resp.is_ok(), equal_to(True))

    @patch_rest
    def test_delete_cg_not_exists(self):
        def f():
            cg = UnityConsistencyGroup(cli=t_rest(), _id='res_119')
            cg.delete()

        assert_that(f, raises(UnityResourceNotFoundError, 'not exist'))

    @patch_rest
    def test_rename_name_used(self):
        def f():
            self.get_cg().name = 'iscsi-test'

        assert_that(f, raises(UnityStorageResourceNameInUseError, 'reserved'))

    @patch_rest
    def test_add_lun_success(self):
        lun1 = UnityLun(cli=t_rest(), _id='sv_3341')
        lun2 = UnityLun(cli=t_rest(), _id='sv_3342')
        resp = self.get_cg().add_lun(lun1, lun2)
        assert_that(resp.is_ok(), equal_to(True))

    @patch_rest
    def test_add_lun_nothing_to_modify(self):
        def f():
            lun = UnityLun(cli=t_rest(), _id='sv_3341')
            self.get_cg().add_lun(lun)

        assert_that(f, raises(UnityNothingToModifyError, 'nothing to modify'))

    @patch_rest
    def test_remove_lun_success(self):
        lun = UnityLun(cli=t_rest(), _id='sv_3342')
        resp = self.get_cg().remove_lun(lun)
        assert_that(resp.is_ok(), equal_to(True))

    @patch_rest
    def test_remove_host_access(self):
        host1 = UnityHost(cli=t_rest(), _id='Host_14')
        host2 = UnityHost(cli=t_rest(), _id='Host_15')
        resp = self.get_cg().remove_host_access(host1, host2)
        assert_that(resp.is_ok(), equal_to(True))

    @patch_rest
    def test_set_host_access(self):
        host = UnityHost(cli=t_rest(), _id='Host_14')
        resp = self.get_cg().set_host_access(host)
        assert_that(resp.is_ok(), equal_to(True))

    @patch_rest
    def test_add_host_access_existed(self):
        def f():
            host1 = UnityHost(cli=t_rest(), _id='Host_14')
            host2 = UnityHost(cli=t_rest(), _id='Host_15')
            self.get_cg().add_host_access(host1, host2)

        assert_that(f, raises(UnityHostAccessAlreadyExistsError, 'has access'))

    @patch_rest
    def test_add_host_access_success(self):
        host1 = UnityHost(cli=t_rest(), _id='Host_12')
        host2 = UnityHost(cli=t_rest(), _id='Host_15')
        resp = self.get_cg().add_host_access(host1, host2)
        assert_that(resp.is_ok(), equal_to(True))

    @patch_rest
    def test_create_cg_snap(self):
        snap = self.get_cg().create_snap('song')
        assert_that(snap.name, equal_to('song'))
        assert_that(snap.storage_resource.get_id(), equal_to('res_19'))

    @patch_rest
    def test_list_cg_snaps(self):
        snaps = self.get_cg().snapshots
        assert_that(len(snaps), equal_to(2))
        assert_that(map(lambda s: s.name, snaps), has_items('song', 'tragedy'))

    @patch_rest
    def test_detach_cg_snap(self):
        snap = UnitySnap(cli=t_rest(), _id='85899345927')
        host = UnityHost(cli=t_rest(), _id='Host_22')
        resp = snap.detach_from(host)
        assert_that(resp.is_ok(), equal_to(True))

    @patch_rest
    def test_attach_cg_snap(self):
        snap = UnitySnap(cli=t_rest(), _id='85899345927')
        host = UnityHost(cli=t_rest(), _id='Host_22')
        resp = snap.attach_to(host)
        assert_that(resp.is_ok(), equal_to(True))

    @patch_rest
    def test_restore_cg_snap_with_backup(self):
        snap = UnitySnap(cli=t_rest(), _id='85899345927')
        backup_snap = snap.restore('paint')
        assert_that(backup_snap.name, equal_to('paint'))
        assert_that(backup_snap.storage_resource.get_id(), equal_to('res_19'))

    @patch_rest
    def test_restore_cg_snap_without_backup(self):
        snap = UnitySnap(cli=t_rest(), _id='85899345927')
        backup_snap = snap.restore()
        assert_that(backup_snap.name, equal_to('2016-11-03_08.35.00'))
        assert_that(backup_snap.storage_resource.get_id(), equal_to('res_19'))

    @patch_rest
    def test_get_csv(self):
        cg_list = UnityConsistencyGroupList(cli=t_rest())
        csv = cg_list.get_metrics_csv()
        assert_that(csv, contains_string('id,name'))
        assert_that(csv, contains_string('res_3,smis-test-cg'))
