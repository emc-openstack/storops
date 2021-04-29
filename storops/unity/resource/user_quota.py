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

import storops
from storops.exception import UnityResourceNotFoundError
from storops.unity.resource import UnityResource, UnityResourceList
from storops.unity.client import UnityClient

__author__ = 'Rajendra Indukuri'

log = logging.getLogger(__name__)


class UnityUserQuota(UnityResource):
    """
    Support CRUD operations for user_quota

    Operations supported:
    create: Create user_quota on a file_system/tree_quota
    modify: Modify user_quota on a file_system/tree_quota
    """
    @classmethod
    def create(cls, cli, filesystem_id=None, tree_quota_id=None,
               hard_limit=None, soft_limit=None, uid=None,
               unix_name=None, win_name=None):
        """
        Creates user_quota on the speficied filesystem or tree quota
        :param filesystem_id: This is an optional parameter which if provided
            will create user_quota on the filesystem specified.
        :param tree_quota_id: This is an optional parameter which if provided
            will create user_quota on the tree_quota specified.
        :param hard_limit: sets hard_limit on the filesystem for the user
            specified
        :param soft_limit: sets soft_limit on the filesystem for the user
            specified
        :param uid: This is an optional parameter to specify user. Either of
            uid/unix_name/win_name should be provided
        :param unix_name: This is an optional parameter to specify user. Either
            of uid/unix_name/win_name should be provided
        :param win_name:This is an optional parameter to specify user. Either
            of uid/unix_name/win_name should be provided
        :return: created user quota.
        """
        tree_quota = None
        filesystem = None
        if filesystem_id is not None:
            fs_clz = storops.unity.resource.filesystem.UnityFileSystem
            filesystem = fs_clz.get(_id=filesystem_id, cli=cli)
            if not filesystem.existed:
                raise UnityResourceNotFoundError(
                    'cannot find filesystem {}.'.format(filesystem_id))

        if tree_quota_id is not None:
            tquota_clz = storops.unity.resource.tree_quota.UnityTreeQuota
            tree_quota = tquota_clz.get(_id=tree_quota_id, cli=cli)
            if not tree_quota.existed:
                raise UnityResourceNotFoundError(
                    'cannot find tree_quota {}.'.format(tree_quota_id))

        user_quota_param = cls.prepare_user_quota_create_parameters(
            filesystem, tree_quota, hard_limit, soft_limit, uid,
            unix_name, win_name)
        resp = cli.post(
            cls().resource_class, **user_quota_param)
        resp.raise_if_err()
        return cls(_id=resp.resource_id, cli=cli)

    @classmethod
    def modify(cls, cli, user_quota_id, hard_limit=None, soft_limit=None):
        """
        Modifies user_quota params for the specified user_quota_id
        :param user_quota_id: This is required which speicfies user_quota to
            be modified
        :param hard_limit: modifies hard_limit on the file_system for the
            user_quota specified
        :param soft_limit: modifies soft_limit on the file_system for the
            user_quota specified
        :return: None
        """
        user_quota = UnityUserQuota.get(_id=user_quota_id, cli=cli)
        if not user_quota.existed:
            raise UnityResourceNotFoundError(
                'cannot find user_quota {}.'.format(user_quota_id))

        req_body = cli.make_body(
            hardLimit=hard_limit,
            softLimit=soft_limit
           )
        resp = cli.action(cls().resource_class, user_quota_id,
                          'modify', **req_body)
        resp.raise_if_err()
        return resp

    @staticmethod
    def prepare_user_quota_create_parameters(
            filesystem=None, tree_quota=None, hard_limit=None,
            soft_limit=None, uid=None, unix_name=None,
            win_name=None):
        """
        Prepare user_quota for the create operation
        :param filesystem: This is needed if the user_quota is to be
            created on the filesystem
        :param tree_quota: This is needed if the user_quota is to be
            created on the tree_quota
        :param hard_limit: hard_limit for the user_quota
        :param soft_limit: soft_limit for the user_quota
        :param uid: uid of the user
        :param unix_name: unix_name of the user
        :param win_name: windows name of the user
        :return: user_quota_params for create user_quota preparation
        """
        user_quota_param = UnityClient.make_body(
            filesystem=filesystem,
            treeQuota=tree_quota,
            hardLimit=hard_limit,
            softLimit=soft_limit,
            uid=uid,
            unixName=unix_name,
            winName=win_name)
        return user_quota_param


class UnityUserQuotaList(UnityResourceList):
    """
    List representation of user_quota
    """
    def __init__(self, cli=None, **filters):
        super(UnityUserQuotaList, self).__init__(cli, **filters)

    @classmethod
    def get_resource_class(cls):
        return UnityUserQuota
