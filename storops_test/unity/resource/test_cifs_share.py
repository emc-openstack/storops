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

import logging
from unittest import TestCase

from hamcrest import assert_that, equal_to, only_contains, raises

from storops.exception import UnityException, UnitySmbShareNameExistedError, \
    UnityAclUserNotFoundError, UnitySnapNameInUseError
from storops.unity.enums import CIFSTypeEnum, ACEAccessTypeEnum, \
    CifsShareOfflineAvailabilityEnum

from storops.unity.resource.cifs_share import UnityCifsShare, \
    UnityCifsShareList, UnityAclUser, UnityAclUserList
from storops_test.unity.rest_mock import t_rest, patch_rest

__author__ = 'Cedric Zhuang'

log = logging.getLogger(__name__)

snap_based_share = UnityCifsShare(cli=t_rest(), _id='SMBShare_5')


class UnityCifsShareTest(TestCase):
    @patch_rest
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

    @patch_rest
    def test_cifs_server(self):
        share = UnityCifsShare('SMBShare_1', cli=t_rest())
        assert_that(share.cifs_server.name, equal_to('nas1130'))
        assert_that(share.cifs_server.domain, equal_to('win2012.dev'))

    @patch_rest
    def test_get_all(self):
        cifs_list = UnityCifsShareList(cli=t_rest())
        assert_that(len(cifs_list), equal_to(1))

    @patch_rest
    def test_create_path_not_exists(self):
        def f():
            UnityCifsShare.create(t_rest(), 'cs1', 'fs_8', '/cs1')

        assert_that(f, raises(UnityException,
                              'could not find the specified path'))

    @patch_rest
    def test_create_success(self):
        share = UnityCifsShare.create(t_rest(), 'cs1', 'fs_8')
        assert_that(share.name, equal_to('cs1'))

    @patch_rest
    def test_create_same_name_exists(self):
        def f():
            UnityCifsShare.create(t_rest(), 'cs2', 'fs_8')

        assert_that(f, raises(UnitySmbShareNameExistedError, 'already exists'))

    @patch_rest
    def test_delete_share_success(self):
        share = UnityCifsShare(_id='SMBShare_7', cli=t_rest())
        resp = share.delete()
        assert_that(resp.is_ok(), equal_to(True))

    @patch_rest
    def test_get_by_name(self):
        shares = UnityCifsShareList(cli=t_rest(), name='cs1')
        assert_that(len(shares), equal_to(1))
        share = shares[0]
        assert_that(share.name, equal_to('cs1'))

    @patch_rest
    def test_create_snap_existed(self):
        def f():
            share = UnityCifsShare(cli=t_rest(), _id='SMBShare_8')
            share.create_snap('share_snap')

        assert_that(f, raises(UnitySnapNameInUseError, 'in use'))

    @patch_rest
    def test_delete_snap_based_share(self):
        share = UnityCifsShare(cli=t_rest(), _id='SMBShare_15')
        resp = share.delete()
        assert_that(resp.is_ok(), equal_to(True))

    @patch_rest
    def test_get_domain_user_name_default_domain(self):
        share = UnityCifsShare(cli=t_rest(), _id='SMBShare_8')
        name = share._get_domain_user_name(user='admin')
        assert_that(name, equal_to(r'win2012.dev\admin'))

    @patch_rest
    def test_add_ace_success(self):
        share = snap_based_share
        resp = share.add_ace(user='administrator')
        assert_that(resp.is_ok(), equal_to(True))

    @patch_rest
    def test_add_ace_no_user(self):
        def f():
            share = UnityCifsShare(cli=t_rest(), _id='SMBShare_5')
            share.add_ace()

        assert_that(f, raises(ValueError, 'username'))

    @patch_rest
    def test_enabled_ace_success(self):
        share = UnityCifsShare(cli=t_rest(), _id='SMBShare_8')
        resp = share.enable_ace()
        assert_that(resp.is_ok(), equal_to(True))

    @patch_rest
    def test_disable_ace_success(self):
        share = UnityCifsShare(cli=t_rest(), _id='SMBShare_8')
        resp = share.disable_ace()
        assert_that(resp.is_ok(), equal_to(True))

    @patch_rest
    def test_ace_list_success(self):
        share = UnityCifsShare(cli=t_rest(), _id='SMBShare_5')
        ace_list = share.get_ace_list()
        assert_that(len(ace_list), equal_to(2))

        ace = ace_list[0]
        assert_that(ace.access_type, equal_to(ACEAccessTypeEnum.GRANT))

    @patch_rest
    def test_ace_clear_access_success(self):
        share = UnityCifsShare(cli=t_rest(), _id='SMBShare_5')
        removed_sid_list = share.clear_access()
        assert_that(removed_sid_list,
                    only_contains('S-1-5-15-be80fa7-8ddad211-d49ba5f9-45e',
                                  'S-1-5-15-be80fa7-8ddad211-d49ba5f9-1f4'))

    @patch_rest
    def test_ace_clear_access_with_white_list(self):
        share = UnityCifsShare(cli=t_rest(), _id='SMBShare_5')
        removed_sid_list = share.clear_access(white_list=['SMIS_User_2'])
        assert_that(removed_sid_list,
                    equal_to(['S-1-5-15-be80fa7-8ddad211-d49ba5f9-45e']))

    @patch_rest
    def test_delete_ace(self):
        share = UnityCifsShare(cli=t_rest(), _id='SMBShare_5')
        resp = share.delete_ace('win2012.dev', 'SMIS_User_2')
        assert_that(resp.is_ok(), equal_to(True))


class UnityAclUserTest(TestCase):
    @patch_rest
    def test_properties(self):
        _id = 'S-1-5-15-be80fa7-8ddad211-d49ba5f9-452'
        user = UnityAclUser(cli=t_rest(), _id=_id)
        assert_that(user.existed, equal_to(True))
        assert_that(user.id, equal_to(_id))
        assert_that(user.sid, equal_to(_id))
        assert_that(user.user_name, equal_to('L1PFC239208$'))
        assert_that(user.domain_name, equal_to('win2012.dev'))

    @patch_rest
    def test_get_all(self):
        users = UnityAclUserList(cli=t_rest())
        assert_that(len(users), equal_to(3))

    @patch_rest
    def test_get_sid_found(self):
        sid = UnityAclUser.get_sid(t_rest(), 'administrator', 'win2012.dev')
        assert_that(sid, equal_to('S-1-5-15-be80fa7-8ddad211-d49ba5f9-1f4'))

    @patch_rest
    def test_get_sid_not_found(self):
        def f():
            UnityAclUser.get_sid(t_rest(), 'not_exists', 'win2012.dev')

        assert_that(f, raises(UnityAclUserNotFoundError))

    @patch_rest
    def test_sid_list(self):
        share = UnityCifsShare(cli=t_rest(), _id='SMBShare_5')
        ace_list = share.get_ace_list()
        assert_that(ace_list.sid_list, only_contains(
            'S-1-5-15-be80fa7-8ddad211-d49ba5f9-45e',
            'S-1-5-15-be80fa7-8ddad211-d49ba5f9-1f4'))
