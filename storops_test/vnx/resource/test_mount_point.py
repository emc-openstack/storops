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

from hamcrest import assert_that, greater_than_or_equal_to, equal_to, raises

from storops_test.vnx.nas_mock import t_nas, patch_post
from storops.exception import VNXBackendError
from storops.vnx.resource.mount_point import VNXFsMountPointList, \
    VNXFsMountPoint
from storops.vnx.resource.mover import VNXMover

__author__ = 'Jay Xu'


class VNXFsMountPointTest(unittest.TestCase):
    @patch_post
    def test_get_all(self):
        mps = VNXFsMountPointList(cli=t_nas())
        assert_that(len(mps), greater_than_or_equal_to(1))
        mp = next(mp for mp in mps if mp.path == '/zhuanc_fs_100g')
        self.verify_fs_100g(mp)

    @patch_post
    def test_get_all_by_mover(self):
        mover = VNXMover(mover_id=2, cli=t_nas())
        mps = VNXFsMountPointList(mover=mover, cli=t_nas())
        assert_that(len(mps), greater_than_or_equal_to(1))

    @patch_post
    def test_get_by_path(self):
        mover = VNXMover(mover_id=1)
        mp = VNXFsMountPoint(mover=mover, path='/zhuanc_fs_100g', cli=t_nas())
        self.verify_fs_100g(mp)

    @patch_post
    def test_get_not_found(self):
        mover = VNXMover(mover_id=1)
        mp = VNXFsMountPoint(mover=mover, path='/not_found', cli=t_nas())
        assert_that(mp.existed, equal_to(False))

    @staticmethod
    def verify_fs_100g(mp):
        assert_that(mp.mover_id, equal_to(1))
        assert_that(mp.existed, equal_to(True))
        assert_that(mp.is_vdm, equal_to(False))
        assert_that(mp.disabled, equal_to(False))
        assert_that(mp.path, equal_to('/zhuanc_fs_100g'))
        assert_that(mp.fs_id, equal_to(211))
        assert_that(mp.nt_credential, equal_to(False))

    @patch_post
    def test_create_fs_mp_path_occupied(self):
        def f():
            cli = t_nas()
            mover = VNXMover(mover_id=1, cli=cli)
            VNXFsMountPoint.create(cli, '/zhuanc_fs_100g', 244, mover)

        assert_that(f, raises(VNXBackendError, 'currently mounted'))

    @patch_post
    def test_create_fs_mp_invalid_fs(self):
        def f():
            cli = t_nas()
            mover = VNXMover(mover_id=1, cli=cli)
            VNXFsMountPoint.create(cli, '/zhuanc_fs_100g', 24, mover)

        assert_that(f, raises(VNXBackendError, 'invalid filesystem specified'))

    @patch_post
    def test_create_fs_mp_mounted(self):
        def f():
            cli = t_nas()
            mover = VNXMover(mover_id=2, cli=cli)
            VNXFsMountPoint.create(cli, '/zhuanc_fs_100g', 244, mover)

        assert_that(f, raises(VNXBackendError, 'is mounted on'))

    @patch_post
    def test_create_fs_mp_success(self):
        cli = t_nas()
        mover = VNXMover(mover_id=2, cli=cli)
        VNXFsMountPoint.create(cli, '/fs_100g', 244, mover)

    @patch_post
    def test_delete_fs_mp(self):
        cli = t_nas()
        mover = VNXMover(mover_id=2, cli=cli)
        resp = VNXFsMountPoint(mover, '/testfs', cli).delete()
        assert_that(resp.is_ok(), equal_to(True))

    @patch_post
    def test_same_path_different_mover(self):
        mps = VNXFsMountPointList(cli=t_nas(), path='/same')
        assert_that(len(mps), equal_to(2))
        for mp in mps:
            assert_that(mp.path, equal_to('/same'))
