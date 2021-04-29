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

from hamcrest import assert_that, equal_to, instance_of, raises

from storops.exception import UnityResourceNotFoundError
from storops.unity.resource.user_quota import UnityUserQuota, \
     UnityUserQuotaList
from storops_test.unity.rest_mock import t_rest, patch_rest

__author__ = 'Rajendra Indukuri'


@ddt.ddt
class UnityUserQuotaListTest(TestCase):
    @patch_rest
    def test_get_all(self):
        user_quotas = UnityUserQuotaList(cli=t_rest())
        assert_that(user_quotas, instance_of(UnityUserQuotaList))
        assert_that(len(user_quotas), equal_to(2))

    @patch_rest
    def test_get_specific_user_quota(self):
        user_quota = UnityUserQuota(
                      _id='userquota_171798692187_3_3', cli=t_rest())
        assert_that(user_quota, instance_of(UnityUserQuota))
        assert_that(user_quota.id, equal_to('userquota_171798692187_3_3'))
        assert_that(user_quota.existed, equal_to(True))

    @patch_rest
    def test_get_user_quota_not_found(self):
        user_quota = UnityUserQuota(
                      _id='abc', cli=t_rest())
        assert_that(user_quota.existed, equal_to(False))

    @patch_rest
    def test_create_user_quota(self):
        ret = UnityUserQuota.create(cli=t_rest(),
                                    filesystem_id='fs_2',
                                    hard_limit=9663676416,
                                    soft_limit=3221225472,
                                    uid=3)
        assert_that(ret, instance_of(UnityUserQuota))
        assert_that(ret.id, equal_to('userquota_171798692187_3_3'))
        assert_that(ret.existed, equal_to(True))

    @patch_rest
    def test_create_user_quota_invalid_filesystem_id(self):
        def f():
            UnityUserQuota.create(cli=t_rest(),
                                  filesystem_id='fs_99',
                                  hard_limit=9663676416,
                                  soft_limit=3221225472,
                                  uid=3)

        assert_that(f, raises(UnityResourceNotFoundError))

    @patch_rest
    def test_create_user_quota_on_tree_quota(self):
        ret = UnityUserQuota.create(cli=t_rest(), filesystem_id='fs_2',
                                    tree_quota_id='treequota_171798692187_3',
                                    hard_limit=9663676416,
                                    soft_limit=3221225472,
                                    uid=3)
        assert_that(ret, instance_of(UnityUserQuota))
        assert_that(ret.id, equal_to('userquota_171798692187_3_3'))
        assert_that(ret.existed, equal_to(True))

    @patch_rest
    def test_create_user_quota_on_tree_quota_fs_invalid(self):
        def f():
            UnityUserQuota.create(cli=t_rest(), filesystem_id='fs_99',
                                  tree_quota_id='treequota_171798692187_3',
                                  hard_limit=9663676416,
                                  soft_limit=3221225472,
                                  uid=3)

        assert_that(f, raises(UnityResourceNotFoundError))

    @patch_rest
    def test_create_user_quota_on_tree_quota_tq_invalid(self):
        def f():
            UnityUserQuota.create(cli=t_rest(), filesystem_id='fs_2',
                                  tree_quota_id='abc',
                                  hard_limit=9663676416,
                                  soft_limit=3221225472,
                                  uid=3)

        assert_that(f, raises(UnityResourceNotFoundError))

    @patch_rest
    def test_create_user_quota_on_tree_quota_tq_n_fs_invalid(self):
        def f():
            UnityUserQuota.create(cli=t_rest(), filesystem_id='fs_99',
                                  tree_quota_id='abc',
                                  hard_limit=9663676416,
                                  soft_limit=3221225472,
                                  uid=3)

        assert_that(f, raises(UnityResourceNotFoundError))

    @patch_rest
    def test_modify_user_quota(self):
        resp = UnityUserQuota.modify(
                cli=t_rest(), user_quota_id='userquota_171798692187_3_3',
                hard_limit=8589934592, soft_limit=2147483648)
        assert_that(resp.is_ok(), equal_to(True))

    @patch_rest
    def test_modify_user_quota_user_quota_id_invalid(self):
        def f():
            UnityUserQuota.modify(
                cli=t_rest(), user_quota_id='abc',
                hard_limit=8589934592, soft_limit=2147483648)

        assert_that(f, raises(UnityResourceNotFoundError))
