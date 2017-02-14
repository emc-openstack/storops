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

from hamcrest import assert_that, equal_to, raises, has_item

from storops_test.vnx.nas_mock import t_nas, patch_nas
from storops.exception import VNXGeneralNasError
from storops.vnx.resource.cifs_share import VNXCifsShare
from storops.vnx.resource.fs import VNXFileSystem
from storops.vnx.resource.mover import VNXMover

__author__ = 'Jay Xu'


class VNXCifsShareTest(unittest.TestCase):
    # todo: add test for share access commands

    @patch_nas
    def test_get_all(self):
        shares = VNXCifsShare.get(cli=t_nas())
        assert_that(len(shares), equal_to(16))
        share = next(s for s in shares if s.name == 'zhuanc_cifs_100g')
        self.verify_share_zhuanc(share)

    @staticmethod
    def verify_share_zhuanc(share):
        assert_that(share.path, equal_to('\zhuanc_fs_100g'))
        assert_that(share.fs_id, equal_to(211))
        assert_that(share.max_users, equal_to(10))
        assert_that(share.comment, equal_to('100g cifs share for zhuanc'))
        assert_that(share.name, equal_to('zhuanc_cifs_100g'))
        assert_that(share.mover_id, equal_to(1))
        assert_that(share.is_vdm, equal_to(False))
        assert_that(share.cifs_server_names, has_item('CIFS'))

    @patch_nas
    def test_get_by_mover(self):
        mover = self.get_mover_1()
        shares = VNXCifsShare.get(cli=t_nas(), mover=mover)
        for share in shares:
            assert_that(share.mover.get_mover_id(),
                        equal_to(mover.get_mover_id()))
            assert_that(share.mover.is_vdm, equal_to(mover.is_vdm))

    def get_mover_1(self):
        mover = VNXMover(mover_id=1, cli=t_nas())
        return mover

    @patch_nas
    def test_get_by_share_name(self):
        shares = VNXCifsShare.get(cli=t_nas(), name='zhuanc_cifs_100g')
        assert_that(len(shares), equal_to(1))
        self.verify_share_zhuanc(shares[0])

    @patch_nas
    def test_get_cifs_share(self):
        mover = self.get_mover_1()
        share = VNXCifsShare.get(name='zhuanc_cifs_100g', mover=mover,
                                 cli=t_nas())
        self.verify_share_zhuanc(share)

    @patch_nas
    def test_get_not_found(self):
        mover = self.get_mover_1()
        cifs = VNXCifsShare.get(name='not_exists', mover=mover, cli=t_nas())
        assert_that(cifs.existed, equal_to(False))

    @patch_nas
    def test_create_invalid_path(self):
        def f():
            mover = self.get_mover_1()
            VNXCifsShare.create(t_nas(), 'test_zhuanc', 'CIFS', mover,
                                path='/test_zhuanc')

        assert_that(f, raises(VNXGeneralNasError, 'Invalid path'))

    @patch_nas
    def test_create_success(self):
        fs = VNXFileSystem(name='zzz', cli=t_nas())
        mover = self.get_mover_1()
        share = VNXCifsShare.create(t_nas(), fs, 'CIFS', mover)
        assert_that(share.path, equal_to('\zzz'))

    @patch_nas
    def test_delete_success(self):
        share = VNXCifsShare(name='zzz', mover=self.get_mover_1(), cli=t_nas())
        resp = share.delete()
        assert_that(resp.is_ok(), equal_to(True))

    @patch_nas
    def test_delete_not_found(self):
        def f():
            share = VNXCifsShare(name='yyy', mover=self.get_mover_1(),
                                 cli=t_nas())
            share.delete('CIFS')

        assert_that(f, raises(VNXGeneralNasError, 'No such file'))
