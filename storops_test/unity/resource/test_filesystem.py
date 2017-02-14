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

from hamcrest import equal_to, assert_that, instance_of, none, raises

from storops.exception import UnityResourceNotFoundError, \
    UnityFileSystemNameAlreadyExisted, UnitySnapNameInUseError, \
    UnityFileSystemSizeTooSmallError
from storops.unity.enums import FilesystemTypeEnum, TieringPolicyEnum, \
    FSSupportedProtocolEnum, AccessPolicyEnum, FSFormatEnum, \
    ResourcePoolFullPolicyEnum, HostIOSizeEnum, NFSShareDefaultAccessEnum, \
    JobStateEnum
from storops.unity.resource.cifs_share import UnityCifsShareList
from storops.unity.resource.filesystem import UnityFileSystem, \
    UnityFileSystemList
from storops.unity.resource.nas_server import UnityNasServer
from storops.unity.resource.pool import UnityPool
from storops.unity.resource.storage_resource import UnityStorageResource
from storops.unity.resource.health import UnityHealth
from storops_test.unity.rest_mock import t_rest, patch_rest

__author__ = 'Cedric Zhuang'


class UnityFileSystemTest(TestCase):
    @patch_rest
    def test_properties(self):
        fs = UnityFileSystem(_id='fs_2', cli=t_rest())
        assert_that(fs.id, equal_to('fs_2'))
        assert_that(fs.type, equal_to(FilesystemTypeEnum.FILESYSTEM))
        assert_that(fs.tiering_policy,
                    equal_to(TieringPolicyEnum.AUTOTIER_HIGH))
        assert_that(fs.supported_protocols,
                    equal_to(FSSupportedProtocolEnum.CIFS))
        assert_that(fs.access_policy, equal_to(AccessPolicyEnum.WINDOWS))
        assert_that(fs.format, equal_to(FSFormatEnum.UFS64))
        assert_that(fs.host_io_size, equal_to(HostIOSizeEnum.GENERAL_8K))
        assert_that(fs.pool_full_policy,
                    equal_to(ResourcePoolFullPolicyEnum.DELETE_ALL_SNAPS))
        assert_that(fs.health, instance_of(UnityHealth))
        assert_that(fs.name, equal_to('esa_cifs1'))
        assert_that(fs.description, equal_to(''))
        assert_that(fs.size_total, equal_to(5368709120))
        assert_that(fs.size_used, equal_to(1642971136))
        assert_that(fs.size_allocated, equal_to(3221225472))
        assert_that(fs.is_read_only, equal_to(False))
        assert_that(fs.is_thin_enabled, equal_to(True))
        assert_that(fs.is_cifs_sync_writes_enabled, equal_to(False))
        assert_that(fs.is_cifs_op_locks_enabled, equal_to(True))
        assert_that(fs.is_cifs_notify_on_write_enabled, equal_to(False))
        assert_that(fs.is_cifs_notify_on_access_enabled, equal_to(False))
        assert_that(fs.cifs_notify_on_change_dir_depth, equal_to(512))
        assert_that(fs.metadata_size, equal_to(3489660928))
        assert_that(fs.metadata_size_allocated, equal_to(3221225472))
        assert_that(fs.per_tier_size_used, equal_to([6442450944, 0, 0]))
        assert_that(fs.snaps_size, equal_to(0))
        assert_that(fs.snaps_size_allocated, equal_to(0))
        assert_that(fs.snap_count, equal_to(0))
        assert_that(fs.is_smbca, equal_to(False))
        assert_that(fs.storage_resource, instance_of(UnityStorageResource))
        assert_that(fs.pool, instance_of(UnityPool))
        assert_that(fs.nas_server, instance_of(UnityNasServer))
        assert_that(fs.cifs_share, instance_of(UnityCifsShareList))
        assert_that(len(fs.cifs_share), equal_to(1))
        assert_that(fs.nfs_share, none())

    @patch_rest
    def test_get_all(self):
        fs_list = UnityFileSystemList(cli=t_rest())
        assert_that(len(fs_list), equal_to(3))

    @patch_rest
    def test_delete_fs_9(self):
        fs = UnityFileSystem(_id='fs_9', cli=t_rest())
        resp = fs.delete(force_snap_delete=True, force_vvol_delete=True)
        assert_that(resp.is_ok(), equal_to(True))
        assert_that(resp.job.existed, equal_to(False))

    @patch_rest
    def test_delete_not_found(self):
        def f():
            fs = UnityFileSystem(_id='fs_99', cli=t_rest())
            fs.delete(force_snap_delete=True, force_vvol_delete=True)

        assert_that(f, raises(UnityResourceNotFoundError))

    @patch_rest
    def test_extend(self):
        fs = UnityFileSystem(_id='fs_8', cli=t_rest())
        resp = fs.extend(1024 ** 3 * 5)
        assert_that(resp.is_ok(), equal_to(True))

    @patch_rest
    def test_extend_size_error(self):
        def f():
            fs = UnityFileSystem(_id='fs_8', cli=t_rest())
            fs.extend(1024 ** 3 * 2)

        assert_that(f, raises(UnityFileSystemSizeTooSmallError,
                              'size is too small'))

    @patch_rest
    def test_create_success(self):
        fs = UnityFileSystem.create(
            t_rest(), 'pool_1', 'nas_2', 'fs3', 3 * 1024 ** 3,
            proto=FSSupportedProtocolEnum.CIFS,
            tiering_policy=TieringPolicyEnum.AUTOTIER_HIGH)
        assert_that(fs.get_id(), equal_to('fs_12'))

    @patch_rest
    def test_delete_filesystem_async(self):
        fs = UnityFileSystem(_id='fs_14', cli=t_rest())
        resp = fs.delete(async=True)
        assert_that(resp.is_ok(), equal_to(True))
        job = resp.job
        assert_that(job.id, equal_to('N-345'))
        assert_that(job.state, equal_to(JobStateEnum.RUNNING))
        assert_that(job.description, equal_to(
            'job.applicationprovisioningservice.job.DeleteApplication'))
        assert_that(str(job.state_change_time),
                    equal_to('2016-03-22 10:39:20.097000+00:00'))
        assert_that(str(job.submit_time),
                    equal_to('2016-03-22 10:39:20.033000+00:00'))
        assert_that(str(job.est_remain_time), equal_to('0:00:29'))
        assert_that(job.progress_pct, equal_to(0))

    @patch_rest
    def test_create_existed(self):
        def f():
            UnityFileSystem.create(
                t_rest(), 'pool_1', 'nas_2', 'fs3', 3 * 1024 ** 3,
                proto=FSSupportedProtocolEnum.NFS)

        assert_that(f, raises(UnityFileSystemNameAlreadyExisted,
                              'file system name has already'))

    @patch_rest
    def test_create_nfs_share_success(self):
        fs = UnityFileSystem(_id='fs_9', cli=t_rest())
        share = fs.create_nfs_share(
            'ns1', share_access=NFSShareDefaultAccessEnum.READ_WRITE)
        assert_that(share.name, equal_to('ns1'))
        assert_that(share.id, equal_to('NFSShare_4'))

    @patch_rest
    def test_create_cifs_share_success(self):
        fs = UnityFileSystem(_id='fs_8', cli=t_rest())
        share = fs.create_cifs_share('cs1')
        assert_that(share.name, equal_to('cs1'))
        assert_that(share.existed, equal_to(True))

    @patch_rest
    def test_create_snap_success(self):
        fs = UnityFileSystem(_id='fs_8', cli=t_rest())
        snap = fs.create_snap()
        assert_that(snap.existed, equal_to(True))
        assert_that(snap.storage_resource, equal_to(fs.storage_resource))

    @patch_rest
    def test_create_snap_name_existed(self):
        def f():
            fs = UnityFileSystem(_id='fs_8', cli=t_rest())
            fs.create_snap(name='2016-03-15_10:56:08')

        assert_that(f, raises(UnitySnapNameInUseError, 'in use'))

    @patch_rest
    def test_create_snap_fs_snap_existed(self):
        def f():
            fs = UnityFileSystem(_id='fs_8', cli=t_rest())
            fs.create_snap('s1')

        assert_that(f, raises(UnitySnapNameInUseError, 'in use'))

    @patch_rest
    def test_fs_snapshots(self):
        fs = UnityFileSystem(_id='fs_5', cli=t_rest())
        assert_that(len(fs.snapshots), equal_to(2))

    @patch_rest
    def test_has_snap_destroying(self):
        fs = UnityFileSystem(_id='fs_5', cli=t_rest())
        assert_that(fs.has_snap(), equal_to(False))

    @patch_rest
    def test_has_snap_true(self):
        fs = UnityFileSystem(_id='fs_8', cli=t_rest())
        assert_that(fs.has_snap(), equal_to(True))
