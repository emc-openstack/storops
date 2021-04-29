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

from storops.exception import UnityQuotaConfigModifyException, \
    UnityResourceNotFoundError
from storops.unity.resource import UnityResource, UnityResourceList

__author__ = 'Rajendra Indukuri'

log = logging.getLogger(__name__)


class UnityQuotaConfig(UnityResource):
    """
    Support for Unity quotaConfig component

    Operations supported:
    modify: Modify quota_config using the quota_config_id
    """

    @classmethod
    def modify(cls, cli, quota_config_id,
               quota_policy=None,
               is_user_quota_enabled=None,
               delete_user_quotas_with_disable=None,
               is_access_deny_enabled=None,
               grace_period=None,
               default_hard_limit=None,
               default_soft_limit=None):
        """
        Modifies tree_quota params for the specified tree_quota_id
        :param quota_config_id: This is required which specifies
            quota_config to be modified
        :param quota_policy: This is an enum which specifies how
            disk usage shold be measured in blocks/file_size
        :param is_user_quota_enabled: To see if user_quota is
            enabled. Cannot be passed with quota_policy
        :param delete_user_quotas_with_disable: whether to delete
            user_quotas when disabling user quotas
        :param is_access_deny_enabled: when true access will be
            denied when limit is exceeded
        :param grace_period: Grace period for soft limit
        :param default_hard_limit: Default hard limit of user quotas
            and tree quotas
        :param default_soft_limit: Default soft limit of user quotas
            and tree quotas.
        :return: None.
        """
        quota_config = UnityQuotaConfig.get(_id=quota_config_id, cli=cli)
        if not quota_config.existed:
            raise UnityResourceNotFoundError(
                     'cannot find quota_config {}.'.format(quota_config_id))

        # quota_policy and is_user_quota_enabled cannot be used together
        if quota_policy is not None and is_user_quota_enabled is not None:
            raise UnityQuotaConfigModifyException()

        req_body = cli.make_body(
            quotaPolicy=quota_policy,
            isUserQuotaEnabled=is_user_quota_enabled,
            deleteUserQuotasWithDisable=delete_user_quotas_with_disable,
            isAccessDenyEnabled=is_access_deny_enabled,
            gracePeriod=grace_period,
            defaultHardLimit=default_hard_limit,
            defaultSoftLimit=default_soft_limit
        )
        resp = cli.action(cls().resource_class, quota_config_id,
                          'modify', **req_body)
        resp.raise_if_err()
        return resp


class UnityQuotaConfigList(UnityResourceList):
    """
    List representation of quota_config
    """

    def __init__(self, cli=None, **filters):
        super(UnityQuotaConfigList, self).__init__(cli, **filters)

    @classmethod
    def get_resource_class(cls):
        return UnityQuotaConfig
