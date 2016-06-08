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

from hamcrest import assert_that, equal_to, only_contains, raises, none

from storops.exception import UnityException, UnitySmbShareNameExistedError, \
    UnityAclUserNotFoundError, UnityCreateCifsUserError, \
    UnityAddCifsAceError, \
    UnityAceNotFoundError, UnitySnapNameInUseError
from storops.unity.enums import CIFSTypeEnum, ACEAccessLevelEnum, \
    CifsShareOfflineAvailabilityEnum
from storops.unity.resource.cifs_share import UnityCifsShare, \
    UnityCifsShareList, UnityAclUser, UnityAclUserList
from test.unity.cim_mock import patch_cim
from test.unity.rest_mock import t_rest, patch_rest

__author__ = 'Cedric Zhuang'

log = logging.getLogger(__name__)


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
    def test_cifs_server(self):
        share = UnityCifsShare('SMBShare_1', cli=t_rest())
        assert_that(share.cifs_server.name, equal_to('nas1130'))
        assert_that(share.cifs_server.domain, equal_to('win2012.dev'))

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
    def test_delete_share_success(self):
        share = UnityCifsShare(_id='SMBShare_7', cli=t_rest())
        resp = share.delete()
        assert_that(resp.is_ok(), equal_to(True))

    @patch_rest()
    def test_get_by_name(self):
        shares = UnityCifsShareList(cli=t_rest(), name='cs1')
        assert_that(len(shares), equal_to(1))
        share = shares[0]
        assert_that(share.name, equal_to('cs1'))

    @patch_rest()
    def test_create_snap_existed(self):
        def f():
            share = UnityCifsShare(cli=t_rest(), _id='SMBShare_8')
            share.create_snap('share_snap')

        assert_that(f, raises(UnitySnapNameInUseError, 'in use'))

    @patch_rest()
    def test_delete_snap_based_share(self):
        share = UnityCifsShare(cli=t_rest(), _id='SMBShare_15')
        resp = share.delete()
        assert_that(resp.is_ok(), equal_to(True))

    @patch_cim()
    def test_get_user_all(self):
        users = UnityCifsShare.get_user(cli=t_rest())
        assert_that(len(users), equal_to(3))

    @patch_cim()
    def test_get_user_by_name_found(self):
        user = UnityCifsShare.get_user(cli=t_rest(),
                                       name=r'win2012.dev\hyperv')
        assert_that(user['name'], equal_to(r'win2012.dev\hyperv'))
        assert_that(user['userID'].strip(),
                    equal_to('S-1-5-15-be80fa7-8ddad211-d49ba5f9-467'))

    @patch_cim(mock_map={'EMC_VNXe_UserContactLeaf.xml': 'not_found.xml'})
    def test_get_user_by_name_not_found(self):
        user = UnityCifsShare.get_user(cli=t_rest(), name=r'win2012.dev\abc')
        assert_that(user, none())

    @patch_cim()
    def test_get_user_sids_all(self):
        users = UnityCifsShare.get_user_sids(cli=t_rest())
        assert_that(len(users), equal_to(3))

    @patch_cim()
    def test_get_user_sids_found(self):
        sid = UnityCifsShare.get_user_sids(cli=t_rest(),
                                           name=r'win2012.dev\hyperv')
        assert_that(sid, equal_to('S-1-5-15-be80fa7-8ddad211-d49ba5f9-467'))

    @patch_cim(mock_map={'CreateUserContact': 'create_user_failed.xml',
                         'EMC_VNXe_UserContactLeaf.xml': 'not_found.xml'})
    def test_get_user_sids_not_found(self):
        def f():
            UnityCifsShare.get_user_sids(cli=t_rest(), name=r'a')

        assert_that(f, raises(UnityCreateCifsUserError))

    @patch_cim(mock_map={'EMC_VNXe_UserContactLeaf.xml': 'not_found.xml'})
    def test_get_user_sid_with_create(self):
        sid = UnityCifsShare.get_user_sids(cli=t_rest(),
                                           name=r'win2012.dev\administrator')
        assert_that(sid, equal_to('S-1-5-15-be80fa7-8ddad211-d49ba5f9-1f4'))

    @patch_cim(mock_map={'CreateUserContact': 'create_user_failed.xml'})
    def test_create_user_not_exists(self):
        def f():
            UnityCifsShare.create_user(cli=t_rest(), name=r'a.b\c')

        assert_that(f, raises(UnityCreateCifsUserError, 'failed to import'))

    @patch_cim()
    def test_create_user_success(self):
        ret = UnityCifsShare.create_user(cli=t_rest(),
                                         name=r'win2012.dev\administrator')
        uid = 'S-1-5-15-be80fa7-8ddad211-d49ba5f9-1f4'
        assert_that(ret, equal_to(uid))

    @patch_cim()
    def test_add_ace_cim_success(self):
        share = UnityCifsShare(cli=t_rest(), _id='SMBShare_8')
        resp = share.add_ace('win2012.dev', 'SMIS_User_1')
        assert_that(resp.is_ok(), equal_to(True))

    @patch_cim(
        mock_map={'AssignPrivilegeToExportedShare': 'set_ace_failed.xml'})
    def test_add_ace_cim_failed(self):
        def f():
            share = UnityCifsShare(cli=t_rest(), _id='SMBShare_8')
            share.add_ace('win2012.dev', 'administrator')

        assert_that(f, raises(UnityAddCifsAceError, 'failed to'))

    @patch_cim()
    def test_delete_ace_success(self):
        share = UnityCifsShare(cli=t_rest(), _id='SMBShare_8')
        resp = share.delete_ace('win2012.dev', 'administrator')
        assert_that(resp.is_ok(), equal_to(True))

    @patch_cim(
        mock_map={'EMC_VNXe_UserContactLeaf.xml': 'user_administrator.xml'})
    def test_delete_ace_not_found(self):
        def f():
            share = UnityCifsShare(cli=t_rest(), _id='SMBShare_8')
            share.delete_ace('win2012.dev', 'hyperv')

        assert_that(f, raises(UnityAceNotFoundError))

    @patch_cim()
    def test_cim_property(self):
        share = UnityCifsShare(cli=t_rest(), _id='SMBShare_8')
        assert_that(share.cim['ElementName'], equal_to('esa_cifs1'))

    @patch_rest()
    def test_get_domain_user_name_default_domain(self):
        share = UnityCifsShare(cli=t_rest(), _id='SMBShare_8')
        name = share._get_domain_user_name(user='admin')
        assert_that(name, equal_to(r'win2012.dev\admin'))

    @patch_rest()
    def test_add_ace_rest_success(self):
        share = UnityCifsShare(cli=t_rest(), _id='SMBShare_8')
        resp = share.add_ace_rest('win2012.dev', 'administrator')
        assert_that(resp.is_ok(), equal_to(True))

    @patch_rest()
    def test_enabled_ace_success(self):
        share = UnityCifsShare(cli=t_rest(), _id='SMBShare_8')
        resp = share.enable_ace()
        assert_that(resp.is_ok(), equal_to(True))

    @patch_rest()
    def test_disable_ace_success(self):
        share = UnityCifsShare(cli=t_rest(), _id='SMBShare_8')
        resp = share.disable_ace()
        assert_that(resp.is_ok(), equal_to(True))

    @patch_cim()
    def test_get_ace_list(self):
        share = UnityCifsShare(cli=t_rest(), _id='SMBShare_8')
        access_list = share.get_ace_list()
        s1 = 'S-1-5-15-be80fa7-8ddad211-d49ba5f9-1f4'
        s2 = 'S-1-5-15-be80fa7-8ddad211-d49ba5f9-467'
        assert_that(access_list[ACEAccessLevelEnum.FULL],
                    only_contains(s1, s2))
        assert_that(len(access_list[ACEAccessLevelEnum.FULL]), equal_to(2))
        assert_that(len(access_list[ACEAccessLevelEnum.READ]), equal_to(0))
        assert_that(len(access_list[ACEAccessLevelEnum.WRITE]), equal_to(0))

    @patch_cim()
    def test_cim_export_service_property(self):
        share = UnityCifsShare(cli=t_rest(), _id='SMBShare_8')
        export_service = share.cim_export_service
        assert_that(export_service['SystemName'], equal_to('cifs_2'))

    @patch_cim()
    def test_cim_clear_access_success(self):
        share = UnityCifsShare(cli=t_rest(), _id='SMBShare_8')
        sids = share.clear_access()
        assert_that(len(sids), equal_to(2))


class UnityAclUserTest(TestCase):
    @patch_rest()
    def test_properties(self):
        _id = 'S-1-5-15-be80fa7-8ddad211-d49ba5f9-452'
        user = UnityAclUser(cli=t_rest(), _id=_id)
        assert_that(user.existed, equal_to(True))
        assert_that(user.id, equal_to(_id))
        assert_that(user.sid, equal_to(_id))
        assert_that(user.user_name, equal_to('L1PFC239208$'))
        assert_that(user.domain_name, equal_to('win2012.dev'))

    @patch_rest()
    def test_get_all(self):
        users = UnityAclUserList(cli=t_rest())
        assert_that(len(users), equal_to(3))

    @patch_rest()
    def test_get_sid_found(self):
        sid = UnityAclUser.get_sid(t_rest(), 'administrator', 'win2012.dev')
        assert_that(sid, equal_to('S-1-5-15-be80fa7-8ddad211-d49ba5f9-1f4'))

    @patch_rest()
    def test_get_sid_not_found(self):
        def f():
            UnityAclUser.get_sid(t_rest(), 'not_exists', 'win2012.dev')

        assert_that(f, raises(UnityAclUserNotFoundError))
