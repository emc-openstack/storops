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

import ddt
from hamcrest import equal_to, assert_that, instance_of, none, raises, calling

from storops.exception import UnityResourceNotFoundError, \
    UnityFileSystemNameAlreadyExisted, UnitySnapNameInUseError, \
    UnityFileSystemSizeTooSmallError, UnityShareShrinkSizeTooLargeError, \
    UnityShareShrinkSizeTooSmallError, UnityLocalReplicationFsNameNotSameError
from storops.unity.enums import FilesystemTypeEnum, TieringPolicyEnum, \
    FSSupportedProtocolEnum, AccessPolicyEnum, FSFormatEnum, \
    ResourcePoolFullPolicyEnum, HostIOSizeEnum, NFSShareDefaultAccessEnum, \
    JobStateEnum, NFSShareSecurityEnum, FSRenamePolicyEnum, \
    FSLockingPolicyEnum, CifsShareOfflineAvailabilityEnum
from storops.unity.resource.cifs_share import UnityCifsShareList
from storops.unity.resource.filesystem import UnityFileSystem, \
    UnityFileSystemList
from storops.unity.resource.nas_server import UnityNasServer
from storops.unity.resource.pool import UnityPool
from storops.unity.resource.remote_system import UnityRemoteSystem
from storops.unity.resource.storage_resource import UnityStorageResource
from storops.unity.resource.health import UnityHealth
from storops_test.unity.rest_mock import t_rest, patch_rest

__author__ = 'Cedric Zhuang'


@ddt.ddt
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
        assert_that(fs.folder_rename_policy,
                    equal_to(FSRenamePolicyEnum.SMB_RENAME_FORBIDDEN))
        assert_that(fs.locking_policy,
                    equal_to(FSLockingPolicyEnum.MANDATORY))
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
        assert_that(fs.size_preallocated, equal_to(2401206272))
        assert_that(fs.size_allocated_total, equal_to(4578115584))
        assert_that(fs.min_size_allocated, equal_to(0))
        assert_that(fs.is_read_only, equal_to(False))
        assert_that(fs.is_thin_enabled, equal_to(True))
        assert_that(fs.is_data_reduction_enabled, equal_to(True))
        assert_that(fs.data_reduction_size_saved, equal_to(0))
        assert_that(fs.data_reduction_percent, equal_to(0))
        assert_that(fs.data_reduction_ratio, equal_to(1.0))
        assert_that(fs.is_advanced_dedup_enabled, equal_to(False))
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
    def test_shrink_success(self):
        fs = UnityFileSystem(_id='fs_8', cli=t_rest())
        resp = fs.shrink(1024 ** 3 * 2.5)
        assert_that(resp.is_ok(), equal_to(True))

    @patch_rest
    def test_shrink_size_too_large_error(self):
        def f():
            fs = UnityFileSystem(_id='fs_8', cli=t_rest())
            fs.storage_resource.size_total = 1024 ** 3 * 3
            fs.shrink(1024 ** 3 * 4)

        message = 'Reject shrink share request, ' \
                  'the new size should be smaller than original.'
        assert_that(f, raises(UnityShareShrinkSizeTooLargeError, message))

    @patch_rest
    def test_shrink_size_too_small_error(self):
        def f():
            fs = UnityFileSystem(_id='fs_8', cli=t_rest())
            fs.storage_resource.size_used = 1024 ** 3 * 3
            fs.shrink(1024 ** 3 * 2)

        message = 'Reject shrink share request, ' \
                  'the new size should be larger than used.'
        assert_that(f, raises(UnityShareShrinkSizeTooSmallError, message))

    @patch_rest()
    def test_create_success(self):
        fs = UnityFileSystem.create(
            t_rest(), 'pool_1', 'nas_2', 'fs3', 3 * 1024 ** 3,
            proto=FSSupportedProtocolEnum.CIFS,
            tiering_policy=TieringPolicyEnum.AUTOTIER_HIGH)
        assert_that(fs.get_id(), equal_to('fs_12'))

    @patch_rest
    def test_create_success_all_params(self):
        size = 3 * 1024 ** 3
        supplemented_size = (3 + 1.5) * 1024 ** 3
        desc = 'Test filesystem.'
        proto = FSSupportedProtocolEnum.NFS
        tiering_policy = TieringPolicyEnum.AUTOTIER_HIGH
        access_policy = AccessPolicyEnum.WINDOWS
        locking_policy = FSLockingPolicyEnum.MANDATORY

        fs = UnityFileSystem.create(
            t_rest(version='4.3.0'), 'pool_1', 'nas_2', 'fs13', size,
            proto=proto, is_thin=True, tiering_policy=tiering_policy,
            user_cap=True, is_compression=True, access_policy=access_policy,
            locking_policy=locking_policy,
            description=desc)

        assert_that(fs.get_id(), equal_to('fs_13'), )
        assert_that(fs.supported_protocols, equal_to(proto))
        assert_that(fs.size_total, equal_to(supplemented_size))
        assert_that(fs.tiering_policy, equal_to(tiering_policy))
        assert_that(fs.is_data_reduction_enabled, equal_to(True))
        assert_that(fs.access_policy, equal_to(access_policy))
        assert_that(fs.locking_policy, equal_to(locking_policy))
        assert_that(fs.description, equal_to(desc))

    @patch_rest
    def test_modify_success_fs_params(self):
        fs = UnityFileSystem(cli=t_rest(), _id='fs_21')

        size = 5 * 1024 ** 3
        desc = 'Modified filesystem.'
        tiering_policy = TieringPolicyEnum.LOWEST
        access_policy = AccessPolicyEnum.UNIX
        locking_policy = FSLockingPolicyEnum.MANDATORY

        fs.modify(size=size, is_thin=False,
                  tiering_policy=tiering_policy,
                  is_compression=False,
                  access_policy=access_policy,
                  locking_policy=locking_policy,
                  description=desc)

        assert_that(fs.size_total, equal_to(size))
        assert_that(fs.tiering_policy, equal_to(tiering_policy))
        assert_that(fs.is_data_reduction_enabled, equal_to(False))
        assert_that(fs.access_policy, equal_to(access_policy))
        assert_that(fs.locking_policy, equal_to(locking_policy))
        assert_that(fs.description, equal_to(desc))

    @patch_rest
    def test_modify_success_cifs_fs_params(self):
        fs = UnityFileSystem(cli=t_rest(), _id='fs_21')

        cifs_fs_params = fs.prepare_cifs_fs_parameters(
            True, True, True, True, 256)

        fs.modify(cifs_fs_parameters=cifs_fs_params)

        assert_that(fs.is_cifs_sync_writes_enabled, equal_to(True))
        assert_that(fs.is_cifs_op_locks_enabled, equal_to(True))
        assert_that(fs.is_cifs_notify_on_write_enabled, equal_to(True))
        assert_that(fs.is_cifs_notify_on_access_enabled, equal_to(True))
        assert_that(fs.cifs_notify_on_change_dir_depth, equal_to(256))

    @patch_rest
    def test_modify_success_no_param(self):
        fs = UnityFileSystem(cli=t_rest(), _id='fs_21')
        fs.modify()

    @patch_rest
    def test_modify_success_empty_description(self):
        fs = UnityFileSystem(cli=t_rest(), _id='fs_22')
        fs.modify(description='')
        assert_that(fs.description, equal_to(''))

    @patch_rest
    def test_modify_success_snap_schedule(self):
        fs = UnityFileSystem(cli=t_rest(), _id='fs_22')
        snap_schedule_parameters = {'snapSchedule': {'id': 'snapSch_1'}}
        resp = fs.modify(snap_schedule_parameters=snap_schedule_parameters)
        assert_that(resp.is_ok(), equal_to(True))

    @patch_rest
    def test_delete_filesystem_async(self):
        fs = UnityFileSystem(_id='fs_14', cli=t_rest())
        resp = fs.delete(async_mode=True)
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
    def test_create_nfs_share_success_all_params(self):
        share_access = NFSShareDefaultAccessEnum.READ_WRITE
        min_security = NFSShareSecurityEnum.KERBEROS
        description = 'Test nfs share.'

        fs = UnityFileSystem(_id='fs_41', cli=t_rest())
        share = fs.create_nfs_share(
            'ns41',
            share_access=share_access,
            min_security=min_security,
            no_access_hosts_string='Host_42',
            read_only_hosts_string='Host_41',
            read_write_hosts_string='Host_19,Host_18',
            read_only_root_hosts_string='Host_17',
            root_access_hosts_string='Host_16,Host_13',
            anonymous_uid=10001,
            anonymous_gid=10002,
            export_option=20001,
            description=description)

        assert_that(share.name, equal_to('ns41'))
        assert_that(share.id, equal_to('NFSShare_41'))
        assert_that(share.path, equal_to('/'))
        assert_that(share.default_access, equal_to(share_access))
        assert_that(share.min_security, equal_to(min_security))
        assert_that(share.no_access_hosts_string, equal_to('Host_42'))
        assert_that(share.read_only_hosts_string, equal_to('Host_41'))
        assert_that(share.read_write_hosts_string,
                    equal_to('Host_18,Host_19'))
        assert_that(share.read_only_root_hosts_string, equal_to('Host_17'))
        assert_that(share.read_write_root_hosts_string,
                    equal_to('Host_13,Host_16'))
        assert_that(share.anonymous_uid, equal_to(10001))
        assert_that(share.anonymous_gid, equal_to(10002))
        assert_that(share.export_option, equal_to(20001))
        assert_that(share.description, equal_to(description))

    @patch_rest
    def test_create_cifs_share_success(self):
        fs = UnityFileSystem(_id='fs_8', cli=t_rest())
        share = fs.create_cifs_share('cs1')
        assert_that(share.name, equal_to('cs1'))
        assert_that(share.existed, equal_to(True))

    @patch_rest
    def test_create_cifs_share_success_all_params(self):
        offline_availability = CifsShareOfflineAvailabilityEnum.DOCUMENTS
        umask = '222'
        description = 'Test cifs share.'

        fs = UnityFileSystem(_id='fs_61', cli=t_rest())
        share = fs.create_cifs_share(
            'cs61',
            is_read_only=True,
            is_encryption_enabled=True,
            is_con_avail_enabled=True,
            is_abe_enabled=True,
            is_branch_cache_enabled=True,
            offline_availability=offline_availability,
            umask=umask, description=description)

        assert_that(share.name, equal_to('cs61'))
        assert_that(share.is_encryption_enabled, equal_to(True))
        assert_that(share.is_continuous_availability_enabled, equal_to(True))
        assert_that(share.is_abe_enabled, equal_to(True))
        assert_that(share.is_branch_cache_enabled, equal_to(True))
        assert_that(share.offline_availability,
                    equal_to(offline_availability))
        assert_that(share.umask, equal_to(umask))
        assert_that(share.description, equal_to(description))

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

    @patch_rest
    @ddt.data(
        {'dst_fs_name': None, 'remote_system': None, 'rep_name': None,
         'dst_size': None, 'is_dst_thin': None, 'dst_tiering_policy': None,
         'is_dst_compression': None,
         'expected_rep_session_id': '171798691895_APM00192210744_0000'
                                    '_171798691923_APM00192210744_0000',
         },
        {'dst_fs_name': 'fs-liangr', 'remote_system': 'RS_6',
         'rep_name': 'fs-rep', 'dst_size': 107374182400, 'is_dst_thin': True,
         'dst_tiering_policy': TieringPolicyEnum.AUTOTIER_HIGH,
         'is_dst_compression': False,
         'expected_rep_session_id': '171798691895_APM00192210744_0000'
                                    '_171798691868_FNM00184901113_0000',
         },
    )
    @ddt.unpack
    def test_replicate_with_dst_resource_provisioning(self,
                                                      dst_fs_name,
                                                      remote_system,
                                                      rep_name,
                                                      dst_size,
                                                      is_dst_thin,
                                                      dst_tiering_policy,
                                                      is_dst_compression,
                                                      expected_rep_session_id):
        fs = UnityFileSystem.get(cli=t_rest(), _id='fs_4')
        if remote_system:
            remote_system = UnityRemoteSystem(_id=remote_system, cli=t_rest())
        rep_session = fs.replicate_with_dst_resource_provisioning(
            60, 'pool_1', dst_fs_name=dst_fs_name,
            remote_system=remote_system, replication_name=rep_name,
            dst_size=dst_size, is_dst_thin=is_dst_thin,
            dst_tiering_policy=dst_tiering_policy,
            is_dst_compression=is_dst_compression)
        assert_that(rep_session.id, equal_to(expected_rep_session_id))

    @patch_rest
    def test_replicate_with_dst_resource_provisioning_fs_name_error(self):
        fs = UnityFileSystem.get(cli=t_rest(), _id='fs_4')
        assert_that(
            calling(
                fs.replicate_with_dst_resource_provisioning
            ).with_args(
                60, 'pool_1', dst_fs_name='fs-liangr-rep-dst'),
            raises(UnityLocalReplicationFsNameNotSameError,
                   'dst_fs_name passed in for creating filesystem local '
                   'replication should be same as source filesystem name '
                   'or None')
        )
