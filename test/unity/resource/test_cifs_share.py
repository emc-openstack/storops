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

from hamcrest import assert_that, equal_to, only_contains, raises

from storops.exception import UnityException, UnitySmbShareNameExistedError
from storops.unity.enums import CIFSTypeEnum, CifsShareOfflineAvailabilityEnum
from storops.unity.resource.cifs_share import UnityCifsShare, \
    UnityCifsShareList
from test.unity.rest_mock import t_rest, patch_rest

__author__ = 'Cedric Zhuang'


class UnityCifsShareTest(TestCase):
    @patch_rest()
    def test_properties(self):
        cifs = UnityCifsShare('SMBShare_1', cli=t_rest())
        assert_that(cifs.id, equal_to('SMBShare_1'))
        assert_that(cifs.type, equal_to(CIFSTypeEnum.CIFS_SHARE))
        assert_that(cifs.offline_availability, equal_to(
            CifsShareOfflineAvailabilityEnum.MANUAL))
        assert_that(cifs.name, equal_to('esa_cifs1'))
        assert_that(cifs.path, equal_to(r'/'))
        assert_that(cifs.export_paths, only_contains(
            r'\\smb1130.win2012.dev\esa_cifs1',
            r'\\10.244.220.120\esa_cifs1'))
        assert_that(cifs.description, equal_to('abc'))
        assert_that(str(cifs.creation_time),
                    equal_to("2016-03-02 02:43:34.014000+00:00"))
        assert_that(str(cifs.modified_time),
                    equal_to("2016-03-02 02:43:34.014000+00:00"))
        assert_that(cifs.is_continuous_availability_enabled, equal_to(False))
        assert_that(cifs.is_encryption_enabled, equal_to(False))
        assert_that(cifs.is_ace_enabled, equal_to(False))
        assert_that(cifs.is_abe_enabled, equal_to(False))
        assert_that(cifs.is_branch_cache_enabled, equal_to(False))
        assert_that(cifs.is_dfs_enabled, equal_to(False))
        assert_that(cifs.umask, equal_to('022'))
        assert_that(cifs.filesystem.get_id(), equal_to('fs_2'))

    @patch_rest()
    def test_get_all(self):
        cifs_list = UnityCifsShareList(cli=t_rest())
        assert_that(len(cifs_list), equal_to(1))

    @patch_rest()
    def test_create_path_not_exists(self):
        def f():
            UnityCifsShare.create(t_rest(), 'cs1', 'fs_8', '/cs1')

        assert_that(f, raises(UnityException,
                              'could not find the specified path'))

    @patch_rest()
    def test_create_success(self):
        share = UnityCifsShare.create(t_rest(), 'cs1', 'fs_8')
        assert_that(share.name, equal_to('cs1'))

    @patch_rest()
    def test_create_same_name_exists(self):
        def f():
            UnityCifsShare.create(t_rest(), 'cs2', 'fs_8')

        assert_that(f, raises(UnitySmbShareNameExistedError, 'already exists'))

    @patch_rest()
    def test_remove_share_success(self):
        share = UnityCifsShare(_id='SMBShare_7', cli=t_rest())
        resp = share.remove()
        assert_that(resp.is_ok(), equal_to(True))

    @patch_rest()
    def test_get_by_name(self):
        shares = UnityCifsShareList(cli=t_rest(), name='cs1')
        assert_that(len(shares), equal_to(1))
        share = shares[0]
        assert_that(share.name, equal_to('cs1'))

    @patch_rest()
    def test_remove_snap_based_share(self):
        share = UnityCifsShare(cli=t_rest(), _id='SMBShare_15')
        resp = share.remove()
        assert_that(resp.is_ok(), equal_to(True))
