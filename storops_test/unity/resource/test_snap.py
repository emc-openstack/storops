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

import mock

from hamcrest import assert_that, equal_to, instance_of, raises, none, calling

from storops.exception import UnityShareOnCkptSnapError, \
    UnityDeleteAttachedSnapError, UnityResourceNotFoundError, \
    UnitySnapAlreadyPromotedException, UnityException, \
    UnityThinCloneNotAllowedError, UnityCGMemberActionNotSupportError
from storops.unity.enums import FilesystemSnapAccessTypeEnum, \
    SnapCreatorTypeEnum, SnapStateEnum, NFSTypeEnum, CIFSTypeEnum
from storops.unity.resource.filesystem import UnityFileSystem
from storops.unity.resource.host import UnityHost
from storops.unity.resource.lun import UnityLun
from storops.unity.resource.snap import UnitySnap, UnitySnapList
from storops.unity.resource.storage_resource import UnityStorageResource
from storops.unity.resource.port import UnityIoLimitPolicy

from storops_test.unity.rest_mock import t_rest, patch_rest

__author__ = 'Cedric Zhuang'


class UnitySnapTest(TestCase):
    @patch_rest
    def test_properties(self):
        snap = UnitySnap(_id=171798691852, cli=t_rest())
        assert_that(snap.existed, equal_to(True))
        assert_that(snap.state, equal_to(SnapStateEnum.READY))
        assert_that(snap.name, equal_to('esa_nfs1_2016-03-15_10:56:29'))
        assert_that(snap.is_system_snap, equal_to(False))
        assert_that(snap.is_modifiable, equal_to(False))
        assert_that(snap.is_read_only, equal_to(False))
        assert_that(snap.is_modified, equal_to(False))
        assert_that(snap.is_auto_delete, equal_to(True))
        assert_that(snap.size, equal_to(5368709120))
        assert_that(str(snap.creation_time),
                    equal_to('2016-03-15 02:57:27.092000+00:00'))
        assert_that(snap.storage_resource, instance_of(UnityStorageResource))
        assert_that(snap.creator_type,
                    equal_to(SnapCreatorTypeEnum.USER_CUSTOM))
        assert_that(snap.access_type,
                    equal_to(FilesystemSnapAccessTypeEnum.CHECKPOINT))
        assert_that(snap.is_cg_snap(), equal_to(False))

    @patch_rest
    def test_get_all(self):
        snaps = UnitySnapList(cli=t_rest())
        assert_that(snaps[0].existed, equal_to(True))
        assert_that(len(snaps), equal_to(3))

    @patch_rest
    def test_create_snap_success(self):
        snap = UnitySnap(_id='171798691884', cli=t_rest())
        sos = snap.create_snap(name='snap_over_snap')
        assert_that(sos.name, equal_to('snap_over_snap'))
        assert_that(sos.existed, equal_to(True))

    @patch_rest
    def test_delete_snap(self):
        snap = UnitySnap(_id='171798691885', cli=t_rest())
        resp = snap.delete()
        assert_that(resp.is_ok(), equal_to(True))

    @patch_rest
    def test_create_nfs_share_type_error(self):
        def f():
            snap = UnitySnap(cli=t_rest(), _id='171798691852')
            snap.create_nfs_share('sns1')

        assert_that(f, raises(UnityShareOnCkptSnapError, 'is a checkpoint'))

    @patch_rest
    def test_create_nfs_share_success(self):
        snap = UnitySnap(cli=t_rest(), _id='171798691896')
        share = snap.create_nfs_share('sns1')
        assert_that(share.snap, equal_to(snap))
        assert_that(share.name, equal_to('sns1'))
        assert_that(share.type, equal_to(NFSTypeEnum.NFS_SNAPSHOT))

    @patch_rest
    def test_create_cifs_share_success(self):
        snap = UnitySnap(cli=t_rest(), _id='171798691899')
        share = snap.create_cifs_share('sns2')
        assert_that(share.snap, equal_to(snap))
        assert_that(share.name, equal_to('sns2'))
        assert_that(share.type, equal_to(CIFSTypeEnum.CIFS_SNAPSHOT))

    @patch_rest
    def test_filesystem_snap(self):
        snap = UnitySnap(cli=t_rest(), _id='171798691852')
        fs = snap.filesystem
        assert_that(fs, instance_of(UnityFileSystem))
        assert_that(fs.storage_resource, equal_to(snap.storage_resource))
        assert_that(snap.lun, none())

    @patch_rest
    def test_lun_snap(self):
        snap = UnitySnap(cli=t_rest(), _id='38654705785')
        lun = snap.lun
        assert_that(lun, instance_of(UnityLun))
        assert_that(snap.filesystem, none())

    @patch_rest
    def test_copy_snap_success(self):
        snap = UnitySnap(cli=t_rest(), _id='38654705785')
        snap = snap.copy('s3')
        assert_that(snap.existed, equal_to(True))
        assert_that(snap, instance_of(UnitySnap))

    @patch_rest
    def test_destroying_snap_existed(self):
        snap = UnitySnap(cli=t_rest(), _id='171798691953')
        assert_that(snap.existed, equal_to(False))

    @patch_rest
    def test_not_found_snap_existed(self):
        snap = UnitySnap(cli=t_rest(), _id='12345')
        assert_that(snap.existed, equal_to(False))

    @patch_rest
    def test_delete_not_exist_snap(self):
        snap = UnitySnap(_id='38654705844', cli=t_rest())
        assert_that(lambda: snap.delete(), raises(UnityResourceNotFoundError))

    @patch_rest
    def test_delete_attached_snap(self):
        snap = UnitySnap(_id='38654705845', cli=t_rest())
        assert_that(lambda: snap.delete(),
                    raises(UnityDeleteAttachedSnapError))

    @patch_rest
    def test_delete_attached_snap_with_force(self):
        snap = UnitySnap(_id='38654705845', cli=t_rest())

        def fake_detach_from(host):
            snap._id = '171798691885'

        with mock.patch.object(UnitySnap, 'detach_from',
                               side_effect=fake_detach_from):
            resp = snap.delete(even_attached=True)
            assert_that(snap._id, equal_to('171798691885'))
            assert_that(resp.is_ok(), equal_to(True))

    @patch_rest
    def test_attach_snap_success(self):
        snap = UnitySnap(_id='38654705676', cli=t_rest())
        host = UnityHost(_id="Host_12", cli=t_rest())
        resp = snap.attach_to(host)
        assert_that(resp.is_ok(), equal_to(True))

    @patch_rest
    def test_attach_second_snap_success(self):
        snap = UnitySnap(_id='38654705670', cli=t_rest())
        host = UnityHost(_id="Host_19", cli=t_rest())
        resp = snap.attach_to(host)
        assert_that(resp.is_ok(), equal_to(True))

    @patch_rest
    def test_detach_snap_success(self):
        snap = UnitySnap(_id='38654705676', cli=t_rest())
        host = UnityHost(_id="Host_12", cli=t_rest())
        resp = snap.detach_from(host)
        assert_that(resp.is_ok(), equal_to(True))

    @patch_rest
    def test_attach_snap_already_attached(self):
        def f():
            snap = UnitySnap(_id='38654705676', cli=t_rest())
            host = UnityHost(_id="Host_13", cli=t_rest())
            snap.attach_to(host)

        assert_that(f, raises(UnitySnapAlreadyPromotedException, "promoted"))

    @patch_rest
    def test_is_cg_snap(self):
        snap = UnitySnap(_id='85899345930', cli=t_rest())
        assert_that(snap.is_cg_snap(), equal_to(True))

    @patch_rest
    def test_get_member_snap_not_found(self):
        def f():
            snap = UnitySnap(_id='85899345930', cli=t_rest())
            lun = UnityLun(cli=t_rest(), _id='sv_3342')
            snap.get_member_snap(lun)

        assert_that(f, raises(ValueError, 'no instance'))

    @patch_rest
    def test_get_member_snap_found(self):
        snap_group = UnitySnap(_id='85899345930', cli=t_rest())
        lun = UnityLun(cli=t_rest(), _id='sv_3338')
        snap = snap_group.get_member_snap(lun)
        assert_that(snap.snap_group.get_id(), equal_to(snap_group.get_id()))
        assert_that(snap.storage_resource.get_id(), equal_to('res_19'))
        assert_that(snap.lun.get_id(), equal_to(lun.get_id()))

    @patch_rest
    def test_thin_clone(self):
        snap = UnitySnap(_id='38654705847', cli=t_rest(version='4.2.0'))
        policy = UnityIoLimitPolicy(_id='qp_2', cli=t_rest())
        clone = snap.thin_clone(name='test_thin_clone',
                                description='This is description.',
                                io_limit_policy=policy)
        assert_that(clone.id, equal_to('sv_4678'))

    @patch_rest
    def test_thin_clone_auto_delete(self):
        snap = UnitySnap(_id='38654705848', cli=t_rest(version='4.2.0'))

        def _inner():
            snap.thin_clone(name='test_thin_clone',
                            description='This is description.',
                            io_limit_policy=None)
        assert_that(_inner, raises(UnityException, "Error Code:0x670166b"))

    @patch_rest
    def test_snap_restore(self):
        snap = UnitySnap(cli=t_rest(), _id='38654705785')
        backup = snap.restore(backup="backup_snap", delete_backup=True)
        assert_that(backup.id, equal_to("38654700002"))

    @patch_rest
    def test_snap_restore_auto_delete_false(self):
        snap = UnitySnap(cli=t_rest(), _id='38654705785')
        backup = snap.restore(backup="backup_snap")
        assert_that(backup.id, equal_to("38654700002"))

    @patch_rest
    def test_thinclone_of_member_snap_not_support(self):
        snap = UnitySnap(cli=t_rest(version='4.3'), _id='38654707282')
        assert_that(calling(snap.thin_clone).with_args('not-support'),
                    raises(UnityCGMemberActionNotSupportError))

    @patch_rest
    def test_thinclone_of_thick_lun_snap_not_allowed(self):
        snap = UnitySnap(cli=t_rest(version='4.3'), _id='38654707273')
        assert_that(calling(snap.thin_clone).with_args('not-allowed'),
                    raises(UnityThinCloneNotAllowedError))
