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

from hamcrest import assert_that, equal_to, raises

from storops_test.vnx.nas_mock import t_nas, patch_post

from storops.exception import VNXFsSnapNameInUseError
from storops.vnx.resource.fs_snap import VNXFsSnap

__author__ = 'Jay Xu'


class VXNFsSnapTest(unittest.TestCase):
    @staticmethod
    def verify_snap_230(snap):
        assert_that(snap.existed, equal_to(True))
        assert_that(snap.name, equal_to('ESA'))
        assert_that(snap.state, equal_to('active'))
        assert_that(snap.fs_id, equal_to(222))
        assert_that(snap.snap_id, equal_to(230))
        assert_that(snap.mover_id, equal_to(1))
        assert_that(snap.is_vdm, equal_to(False))

    @patch_post
    def test_get_all(self):
        snap_list = VNXFsSnap.get(t_nas())
        snap = next(snap for snap in snap_list if snap.snap_id == 230)
        self.verify_snap_230(snap)

    @patch_post
    def test_get_by_name(self):
        snap = VNXFsSnap.get(name='ESA', cli=t_nas())
        self.verify_snap_230(snap)

    @patch_post
    def test_get_by_name_not_found(self):
        snap = VNXFsSnap(name='aaa', cli=t_nas())
        assert_that(snap.existed, equal_to(False))

    @patch_post
    def test_get_by_id_not_found(self):
        snap = VNXFsSnap.get(snap_id=111, cli=t_nas())
        assert_that(snap.existed, equal_to(False))

    @patch_post
    def test_get_by_id(self):
        snap = VNXFsSnap(snap_id=230, cli=t_nas())
        self.verify_snap_230(snap)

    @patch_post
    def test_create_success(self):
        snap = VNXFsSnap.create(t_nas(), 'test', 222, 61)
        assert_that(snap.name, equal_to('test'))
        assert_that(snap.fs_id, equal_to(222))
        assert_that(snap.snap_id, equal_to(242))

    @patch_post
    def test_create_existed(self):
        def f():
            VNXFsSnap.create(t_nas(), 'Tan_Manual_CheckPoint', 228, 61)

        assert_that(f, raises(VNXFsSnapNameInUseError, 'already in use'))

    @patch_post
    def test_delete(self):
        snap = VNXFsSnap(name='test', cli=t_nas())
        resp = snap.delete()
        assert_that(resp.is_ok(), equal_to(True))
