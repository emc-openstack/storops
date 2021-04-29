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

from storops.exception import UnityQuotaConfigModifyException, \
    UnityResourceNotFoundError
from storops.unity.enums import QuotaPolicyEnum
from storops.unity.resource.quota_config import UnityQuotaConfigList, \
     UnityQuotaConfig
from storops_test.unity.rest_mock import t_rest, patch_rest

__author__ = 'Rajendra Indukuri'


@ddt.ddt
class UnityQuotaConfigListTest(TestCase):
    @patch_rest
    def test_get_all(self):
        quotas_configs = UnityQuotaConfigList(cli=t_rest())
        assert_that(quotas_configs, instance_of(UnityQuotaConfigList))
        assert_that(len(quotas_configs), equal_to(2))

    @patch_rest
    def test_get_specific_quota_config(self):
        quota_config = UnityQuotaConfig(
                          _id='quotaconfig_171798691845_1', cli=t_rest())
        assert_that(quota_config, instance_of(UnityQuotaConfig))
        assert_that(quota_config.id,
                    equal_to('quotaconfig_171798691845_1'))
        assert_that(quota_config.existed, equal_to(True))

    @patch_rest
    def test_get_quota_config_not_found(self):
        quota_config = UnityQuotaConfig(_id='abc', cli=t_rest())
        assert_that(quota_config.existed, equal_to(False))

    @patch_rest
    def test_modify_quota_config(self):
        resp = UnityQuotaConfig.modify(
                cli=t_rest(), quota_config_id='quotaconfig_171798691845_1',
                quota_policy=QuotaPolicyEnum.BLOCKS,
                is_user_quota_enabled=None,
                delete_user_quotas_with_disable=False,
                is_access_deny_enabled=False,
                grace_period=345600,
                default_hard_limit=8589934592,
                default_soft_limit=2147483648)
        assert_that(resp.is_ok(), equal_to(True))

    @patch_rest
    def test_modify_quota_config_invalid_quota_config_id(self):
        def f():
            UnityQuotaConfig.modify(cli=t_rest(),
                                    quota_config_id='abc',
                                    quota_policy=QuotaPolicyEnum.BLOCKS,
                                    is_user_quota_enabled=None,
                                    delete_user_quotas_with_disable=False,
                                    is_access_deny_enabled=False,
                                    grace_period=345600,
                                    default_hard_limit=8589934592,
                                    default_soft_limit=2147483648)

        assert_that(f, raises(UnityResourceNotFoundError))

    @patch_rest
    def test_modify_quota_config_pass_policy_is_quota_enabled_together(self):
        def f():
            UnityQuotaConfig.modify(
                cli=t_rest(), quota_config_id='quotaconfig_171798691845_1',
                quota_policy=QuotaPolicyEnum.BLOCKS,
                is_user_quota_enabled=True,
                delete_user_quotas_with_disable=False,
                is_access_deny_enabled=False,
                grace_period=345600,
                default_hard_limit=8589934592,
                default_soft_limit=2147483648)

        assert_that(f, raises(UnityQuotaConfigModifyException))
