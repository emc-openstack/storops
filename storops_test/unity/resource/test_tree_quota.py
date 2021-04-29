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
from storops.unity.resource.tree_quota import UnityTreeQuota, \
     UnityTreeQuotaList
from storops_test.unity.rest_mock import t_rest, patch_rest

__author__ = 'Rajendra Indukuri'


@ddt.ddt
class UnityTreeQuotaListTest(TestCase):
    @patch_rest
    def test_get_all(self):
        tree_quotas = UnityTreeQuotaList(cli=t_rest())
        assert_that(tree_quotas, instance_of(UnityTreeQuotaList))
        assert_that(len(tree_quotas), equal_to(4))

    @patch_rest
    def test_get_specific_tree_quota(self):
        tree_quota = UnityTreeQuota(_id='treequota_171798692187_3',
                                    cli=t_rest())
        assert_that(tree_quota, instance_of(UnityTreeQuota))
        assert_that(tree_quota.id,
                    equal_to('treequota_171798692187_3'))
        assert_that(tree_quota.existed, equal_to(True))

    @patch_rest
    def test_get_tree_quota_not_found(self):
        tree_quota = UnityTreeQuota(_id='abc', cli=t_rest())
        assert_that(tree_quota.existed, equal_to(False))

    @patch_rest
    def test_create_tree_quota(self):
        ret = UnityTreeQuota.create(cli=t_rest(), filesystem_id='fs_2',
                                    hard_limit=9663676416,
                                    soft_limit=3221225472,
                                    path='/myPath',
                                    description="Creating Tree Quota")
        assert_that(ret, instance_of(UnityTreeQuota))
        assert_that(ret.id, equal_to('treequota_171798692187_3'))
        assert_that(ret.existed, equal_to(True))

    @patch_rest
    def test_create_tree_quota_invalid_filesystem_id(self):
        def f():
            UnityTreeQuota.create(
                cli=t_rest(), filesystem_id='fs_99',
                hard_limit=9663676416, soft_limit=3221225472,
                path='/myPath', description="Creating Tree Quota")

        assert_that(f, raises(UnityResourceNotFoundError))

    @patch_rest
    def test_modify_tree_quota(self):
        resp = UnityTreeQuota.modify(cli=t_rest(),
                                     tree_quota_id='treequota_171798692187_3',
                                     hard_limit=8589934592,
                                     soft_limit=2147483648,
                                     description='modify tree Quota')
        assert_that(resp.is_ok(), equal_to(True))

    @patch_rest
    def test_modify_tree_quota_invalid_treequota_id(self):
        def f():
            UnityTreeQuota.modify(cli=t_rest(),
                                  tree_quota_id='abc',
                                  hard_limit=8589934592,
                                  soft_limit=2147483648,
                                  description="modify tree Quota")

        assert_that(f, raises(UnityResourceNotFoundError))

    @patch_rest
    def test_delete_tree_quota(self):
        resp = UnityTreeQuota.delete(cli=t_rest(),
                                     tree_quota_id='treequota_171798692187_3')
        assert_that(resp.is_ok(), equal_to(True))

    @patch_rest
    def test_delete_tree_quota_invalid_tree_quota_id(self):
        def f():
            UnityTreeQuota.delete(cli=t_rest(), tree_quota_id='abc')

        assert_that(f, raises(UnityResourceNotFoundError))
