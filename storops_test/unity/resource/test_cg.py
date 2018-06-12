# Copyright (c) 2018 Dell Inc. or its subsidiaries.
# All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
from __future__ import unicode_literals

from unittest import TestCase

from hamcrest import assert_that, equal_to, instance_of, has_items, raises, \
    contains_string, none, calling

from storops.exception import UnityStorageResourceNameInUseError, \
    UnityConsistencyGroupNameInUseError, UnityResourceNotFoundError, \
    UnityNothingToModifyError, UnityHostAccessAlreadyExistsError
from storops.unity.enums import StorageResourceTypeEnum, HostLUNAccessEnum
from storops.unity.resource.cg import UnityConsistencyGroup, \
    UnityConsistencyGroupList

from storops.unity.resource.host import UnityHost
from storops.unity.resource.lun import UnityLun
from storops.unity.resource.snap import UnitySnap

from storops_test.unity.rest_mock import t_rest, patch_rest


__author__ = 'Peter Wang'


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
                                          lun_add=[lun1, lun2])
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
            t_rest(), 'Muse', lun_add=[lun1], hosts=[host1, host2])
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
    def test_attach_lun_in_cg(self):
        lun_in_cg = UnityLun.get(cli=t_rest(), _id='sv_15')
        host = UnityHost(cli=t_rest(), _id='Host_22')

        resp = lun_in_cg.attach_to(host)
        assert_that(resp.is_ok(), equal_to(True))

    @patch_rest
    def test_detach_lun_in_cg(self):
        lun_in_cg = UnityLun.get(cli=t_rest(), _id='sv_15')
        host = UnityHost(cli=t_rest(), _id='Host_2')

        resp = lun_in_cg.detach_from(host)
        assert_that(resp.is_ok(), equal_to(True))

    @patch_rest
    def test_detach_lun_nothing(self):
        lun_in_cg = UnityLun.get(cli=t_rest(), _id='sv_3')
        host = UnityHost(cli=t_rest(), _id='Host_2')

        r = lun_in_cg.detach_from(host)
        assert_that(r, none())

    @patch_rest
    def test_detach_lun_from_all(self):
        lun_in_cg = UnityLun.get(cli=t_rest(), _id='sv_15')
        resp = lun_in_cg.detach_from(None)
        assert_that(resp.is_ok(), equal_to(True))

    @patch_rest
    def test_expand_lun_in_cg(self):
        lun_in_cg = UnityLun.get(cli=t_rest(), _id='sv_15')
        old_size = lun_in_cg.size_total
        resp = lun_in_cg.expand(100 * 1024 ** 3)
        assert_that(resp, equal_to(old_size))

    @patch_rest
    def test_modify_lun_in_cg(self):
        lun_in_cg = UnityLun.get(cli=t_rest(), _id='sv_15')
        resp = lun_in_cg.modify(size=15 * 1024 ** 3)
        assert_that(resp.is_ok(), equal_to(True))

    @patch_rest
    def test_modify_lun_compression_enabled_in_cg_v4_2(self):
        lun_in_cg = UnityLun.get(cli=t_rest(version='4.2'), _id='sv_17')
        resp = lun_in_cg.modify(is_compression=True)
        assert_that(resp.is_ok(), equal_to(True))

    @patch_rest
    def test_modify_lun_compression_enabled_in_cg(self):
        lun_in_cg = UnityLun.get(cli=t_rest(version='4.3'), _id='sv_18')
        resp = lun_in_cg.modify(is_compression=True)
        assert_that(resp.is_ok(), equal_to(True))

    @patch_rest
    def test_replace_lun_in_cg(self):
        cg = UnityConsistencyGroup.get(cli=t_rest(), _id='res_6')
        lun1 = UnityLun(cli=t_rest(), _id='sv_3341')
        lun2 = UnityLun(cli=t_rest(), _id='sv_3342')
        resp = cg.replace_lun(lun1, lun2)
        assert_that(resp.is_ok(), equal_to(True))

    @patch_rest
    def test_replace_lun_in_cg_already_in(self):
        cg = UnityConsistencyGroup.get(cli=t_rest(), _id='res_6')
        lun1 = UnityLun(cli=t_rest(), _id='sv_3341')
        lun2 = UnityLun(cli=t_rest(), _id='sv_14')
        resp = cg.replace_lun(lun1, lun2)
        assert_that(resp.is_ok(), equal_to(True))

    @patch_rest
    def test_get_csv(self):
        cg_list = UnityConsistencyGroupList(cli=t_rest())
        csv = cg_list.get_metrics_csv()
        assert_that(csv, contains_string('id,name'))
        assert_that(csv, contains_string('res_3,smis-test-cg'))

    @patch_rest
    def test_attach_cg_not_implemented(self):
        cg = UnityConsistencyGroup.get(cli=t_rest(), _id='res_6')
        assert_that(calling(cg.attach_to), raises(NotImplementedError))

    @patch_rest
    def test_detach_cg_not_implemented(self):
        cg = UnityConsistencyGroup.get(cli=t_rest(), _id='res_6')
        assert_that(calling(cg.detach_from), raises(NotImplementedError))

    @patch_rest
    def test_update_lun_add(self):
        cg = UnityConsistencyGroup.get(cli=t_rest(), _id='res_21')
        lun1 = UnityLun(cli=t_rest(), _id='sv_60')
        lun2 = UnityLun(cli=t_rest(), _id='sv_61')
        resp = cg.update_lun(add_luns=[lun1, lun2])
        assert_that(resp.is_ok(), equal_to(True))

    @patch_rest
    def test_update_lun_remove(self):
        cg = UnityConsistencyGroup.get(cli=t_rest(), _id='res_21')
        lun1 = UnityLun(cli=t_rest(), _id='sv_58')
        lun2 = UnityLun(cli=t_rest(), _id='sv_59')
        resp = cg.update_lun(remove_luns=[lun1, lun2])
        assert_that(resp.is_ok(), equal_to(True))

    @patch_rest
    def test_update_lun_add_remove(self):
        cg = UnityConsistencyGroup.get(cli=t_rest(), _id='res_21')
        lun1 = UnityLun(cli=t_rest(), _id='sv_58')
        lun2 = UnityLun(cli=t_rest(), _id='sv_59')
        lun3 = UnityLun(cli=t_rest(), _id='sv_60')
        lun4 = UnityLun(cli=t_rest(), _id='sv_61')
        resp = cg.update_lun(add_luns=[lun1, lun3], remove_luns=[lun2, lun4])
        assert_that(resp.is_ok(), equal_to(True))

    @patch_rest
    def test_update_lun_all_none(self):
        cg = UnityConsistencyGroup.get(cli=t_rest(), _id='res_21')
        resp = cg.update_lun()
        assert_that(resp.is_ok(), equal_to(True))
