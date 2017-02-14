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

from hamcrest import assert_that, has_item, raises
from hamcrest import equal_to

from storops_test.vnx.nas_mock import t_nas, patch_nas
from storops.exception import VNXBackendError
from storops.vnx.resource.mover import VNXMover
from storops.vnx.resource.nfs_share import NfsHostConfig, VNXNfsShare

__author__ = 'Jay Xu'


class VNXNfsShareTest(unittest.TestCase):
    @patch_nas
    def test_get_all_share(self):
        shares = VNXNfsShare.get(t_nas())
        assert_that(len(shares), equal_to(26))
        share = next(s for s in shares if s.path == '/EEE')
        self.verify_share_eee(share)

    @patch_nas(xml_output='abc.xml')
    def test_get_share_by_path_empty(self):
        def f():
            path = '/EEE'
            shares = VNXNfsShare.get(t_nas(), path=path)
            assert_that(len(shares), equal_to(1))

        assert_that(f, raises(IOError))

    @patch_nas
    def test_get_share_by_path_success(self):
        path = '/EEE'
        shares = VNXNfsShare.get(t_nas(), path=path)
        assert_that(len(shares), equal_to(1))
        share = next(s for s in shares if s.path == path)
        self.verify_share_eee(share)

    @patch_nas
    def test_get_share_by_mover_id(self):
        mover = self.get_mover_1()
        shares = VNXNfsShare.get(t_nas(), mover=mover)
        assert_that(len(shares), equal_to(24))
        share = next(s for s in shares if s.path == '/EEE')
        self.verify_share_eee(share)

    @staticmethod
    def verify_share_eee(share):
        assert_that(share.path, equal_to('/EEE'))
        assert_that(share.read_only, equal_to(False))
        assert_that(share.fs_id, equal_to(213))
        assert_that(share.mover_id, equal_to(1))
        assert_that(len(share.root_hosts), equal_to(41))
        assert_that(share.access_hosts, has_item('10.110.43.94'))
        assert_that(len(share.access_hosts), equal_to(41))
        assert_that(share.access_hosts, has_item('10.110.43.94'))
        assert_that(len(share.rw_hosts), equal_to(41))
        assert_that(share.rw_hosts, has_item('10.110.43.94'))
        assert_that(len(share.ro_hosts), equal_to(41))
        assert_that(share.ro_hosts, has_item('10.110.43.94'))

    @patch_nas
    def test_modify_not_exists(self):
        def f():
            host_config = NfsHostConfig(
                root_hosts=['1.1.1.1', '2.2.2.2'],
                ro_hosts=['3.3.3.3'],
                rw_hosts=['4.4.4.4', '5.5.5.5'],
                access_hosts=['6.6.6.6'])
            mover = self.get_mover_1()
            share = VNXNfsShare(cli=t_nas(), mover=mover, path='/not_found')
            share.modify(ro=False, host_config=host_config)

        assert_that(f, raises(VNXBackendError, 'does not exist'))

    @patch_nas
    def test_modify_success(self):
        host_config = NfsHostConfig(access_hosts=['7.7.7.7'])
        mover = self.get_mover_1()
        share = VNXNfsShare(cli=t_nas(), mover=mover, path='/EEE')
        resp = share.modify(ro=True, host_config=host_config)
        assert_that(resp.is_ok(), equal_to(True))

    @patch_nas
    def test_create_no_host(self):
        def f():
            mover = self.get_mover_1()
            VNXNfsShare.create(cli=t_nas(), mover=mover, path='/invalid')

        assert_that(f, raises(VNXBackendError, 'is invalid'))

    @patch_nas
    def test_create_success(self):
        mover = self.get_mover_1()
        share = VNXNfsShare.create(cli=t_nas(), mover=mover, path='/EEE')
        assert_that(share.path, equal_to('/EEE'))
        assert_that(share.mover_id, equal_to(1))
        assert_that(share.existed, equal_to(True))
        assert_that(share.fs_id, equal_to(243))

    @patch_nas
    def test_create_with_host_config(self):
        mover = self.get_mover_1()
        host_config = NfsHostConfig(
            root_hosts=['1.1.1.1', '2.2.2.2'],
            ro_hosts=['3.3.3.3'],
            rw_hosts=['4.4.4.4', '5.5.5.5'],
            access_hosts=['6.6.6.6'])
        share = VNXNfsShare.create(cli=t_nas(), mover=mover, path='/FFF',
                                   host_config=host_config)
        assert_that(share.fs_id, equal_to(247))
        assert_that(share.path, equal_to('/FFF'))
        assert_that(share.existed, equal_to(True))
        assert_that(share.access_hosts, has_item('6.6.6.6'))

    @patch_nas
    def test_delete_success(self):
        mover = self.get_mover_1()
        share = VNXNfsShare(cli=t_nas(), mover=mover, path='/EEE')
        resp = share.delete()
        assert_that(resp.is_ok(), equal_to(True))

    @patch_nas
    def test_delete_not_found(self):
        def f():
            mover = self.get_mover_1()
            share = VNXNfsShare(cli=t_nas(), mover=mover, path='/not_found')
            share.delete()

        assert_that(f, raises(VNXBackendError, 'Invalid argument'))

    @staticmethod
    def get_mover_1():
        return VNXMover(mover_id=1, cli=t_nas())

    @patch_nas
    def test_mover_property(self):
        mover = self.get_mover_1()
        share = VNXNfsShare.get(cli=t_nas(), mover=mover, path='/EEE')
        mover = share.mover
        assert_that(mover.existed, equal_to(True))
        assert_that(mover.role, equal_to('primary'))

    @patch_nas
    def test_fs_property(self):
        mover = self.get_mover_1()
        share = VNXNfsShare.get(cli=t_nas(), mover=mover, path='/EEE')
        fs = share.fs
        assert_that(fs.existed, equal_to(True))
        assert_that(fs.fs_id, equal_to(243))

    @patch_nas
    def test_allow_ro_hosts(self):
        mover = self.get_mover_1()
        share = VNXNfsShare(cli=t_nas(), mover=mover, path='/minjie_fs1')
        resp = share.allow_ro_access('1.1.1.1', '2.2.2.2')
        assert_that(resp.is_ok(), equal_to(True))

    @patch_nas
    def test_deny_hosts(self):
        mover = self.get_mover_1()
        share = VNXNfsShare(cli=t_nas(), mover=mover, path='/minjie_fs2')
        resp = share.deny_access('1.1.1.1', '2.2.2.2')
        assert_that(resp.is_ok(), equal_to(True))
