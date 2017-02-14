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

from hamcrest import equal_to, assert_that, raises, none, instance_of

from storops.exception import VNXBackendError, VNXInvalidMoverID, \
    VNXFsExistedError
from storops.vnx.resource.fs import VNXFileSystem, VNXFileSystemList
from storops_test.vnx.nas_mock import patch_post, t_nas

__author__ = 'Jay Xu'


class FileSystemTest(unittest.TestCase):
    @staticmethod
    def verify_root_fs_1(fs):
        assert_that(fs.fs_id, equal_to(1))
        assert_that(fs.internal_use, equal_to(True))
        assert_that(fs.name, equal_to('root_fs_1'))
        assert_that(fs.volume, equal_to(10))
        assert_that(fs.policies, none())
        assert_that(fs.pools, none())
        assert_that(fs.storages, equal_to(1))
        assert_that(fs.type, equal_to('uxfs'))
        assert_that(fs.size, equal_to(16))

    @staticmethod
    def verify_fs_src0(fs):
        assert_that(fs.fs_id, equal_to(37))
        assert_that(fs.internal_use, equal_to(False))
        assert_that(fs.name, equal_to('fs_src0'))
        assert_that(fs.policies, equal_to(
            'Thin=No,Compressed=No,Mirrored=No,'
            'Tiering policy=N/A/Optimize Pool'))
        assert_that(fs.pools, equal_to([59]))
        assert_that(fs.size, equal_to(1024))
        assert_that(fs.storages, equal_to(1))
        assert_that(fs.type, equal_to('uxfs'))
        assert_that(fs.volume, equal_to(150))

    @patch_post
    def test_clz_get_fs_success(self):
        fs = VNXFileSystem.get(name='fs_src0', cli=t_nas())
        self.verify_fs_src0(fs)

    @patch_post(output='abc.xml')
    def test_clz_get_fs_empty(self):
        def f():
            fs = VNXFileSystem.get(name='fs_src0', cli=t_nas())
            assert_that(fs.existed, equal_to(False))

        assert_that(f, raises(IOError))

    @patch_post
    def test_clz_get_all(self):
        fs_list = VNXFileSystem.get(cli=t_nas())
        assert_that(len(fs_list), equal_to(25))

    @patch_post
    def test_get(self):
        fs = VNXFileSystem('fs_src0', cli=t_nas())
        self.verify_fs_src0(fs)

    @patch_post
    def test_get_by_id(self):
        fs = VNXFileSystem(fs_id=27, cli=t_nas())
        assert_that(fs.existed, equal_to(True))
        assert_that(fs.volume, equal_to(125))

    @patch_post
    def test_get_not_found(self):
        fs = VNXFileSystem('abc', cli=t_nas())
        assert_that(fs._get_name(), equal_to('abc'))
        assert_that(fs.existed, equal_to(False))

    @patch_post
    def test_get_all(self):
        fs_list = VNXFileSystemList(t_nas())
        assert_that(len(fs_list), equal_to(25))
        root_fs_1 = [fs for fs in fs_list if fs.name == 'root_fs_1'][0]
        self.verify_root_fs_1(root_fs_1)
        fs_src0 = [fs for fs in fs_list if fs.name == 'fs_src0'][0]
        self.verify_fs_src0(fs_src0)

    @patch_post
    def test_delete_fs_not_exists(self):
        def f():
            fs = VNXFileSystem(fs_id=99, cli=t_nas())
            fs.delete()

        assert_that(f, raises(VNXBackendError, 'not found'))

    @patch_post
    def test_delete_fs_success(self):
        fs = VNXFileSystem(fs_id=98, cli=t_nas())
        resp = fs.delete()
        assert_that(resp.is_ok(), equal_to(True))

    @patch_post
    def test_create_filesystem_invalid_vdm_id(self):
        def f():
            VNXFileSystem.create(t_nas(), 'test18', size_kb=1, pool=0,
                                 mover=1, is_vdm=True)

        assert_that(f, raises(VNXBackendError,
                              'VDM with id=1 not found.'))

    @patch_post
    def test_create_filesystem_invalid_pool(self):
        def f():
            VNXFileSystem.create(t_nas(), 'test17', size_kb=1, pool=0, mover=1)

        assert_that(f, raises(VNXBackendError,
                              'Storage pool was not specified or invalid'))

    @patch_post
    def test_create_filesystem_invalid_size(self):
        def f():
            VNXFileSystem.create(t_nas(), 'test16', size_kb=1, pool=59,
                                 mover=1)

        assert_that(f, raises(VNXBackendError,
                              'specified size cannot be created'))

    @patch_post
    def test_create_filesystem_not_enough_space(self):
        def f():
            VNXFileSystem.create(t_nas(), 'test15', size_kb=1024 ** 2 * 5,
                                 pool=59, mover=1)

        assert_that(f, raises(VNXBackendError,
                              'is not available from the pool'))

    @patch_post
    def test_create_filesystem_invalid_mover_id(self):
        def f():
            VNXFileSystem.create(t_nas(), 'test13', size_kb=1024 * 5,
                                 pool=61, mover=6)

        assert_that(f, raises(VNXInvalidMoverID,
                              'Mover with id=6 not found.'))

    @patch_post
    def test_create_filesystem(self):
        ret = VNXFileSystem.create(t_nas(), 'test14', size_kb=1024 * 5,
                                   pool=61, mover=1)
        assert_that(ret, instance_of(VNXFileSystem))

    @patch_post
    def test_create_fs_existed(self):
        def f():
            VNXFileSystem.create(t_nas(), 'EG_TEST_POOL',
                                 size_kb=1024 * 2 * 5,
                                 pool=32, mover=1)

        assert_that(f, raises(VNXFsExistedError, 'already exists'))

    @patch_post
    def test_extend_fs(self):
        fs = VNXFileSystem(cli=t_nas(), fs_id=243)
        resp = fs.extend(1024 * 4)
        assert_that(resp.is_ok(), equal_to(True))

    @patch_post
    def test_extend_fs_too_small(self):
        def f():
            fs = VNXFileSystem(cli=t_nas(), fs_id=243)
            fs.extend(1024 * 2)

        assert_that(f, raises(VNXBackendError, 'not valid'))

    @patch_post
    def test_create_fs_snap(self):
        fs = VNXFileSystem(cli=t_nas(), fs_id=222)
        snap = fs.create_snap('test', pool=61)
        assert_that(snap.name, equal_to('test'))
        assert_that(snap.fs_id, equal_to(222))
        assert_that(snap.existed, equal_to(True))
