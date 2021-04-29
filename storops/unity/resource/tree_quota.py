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


class UnityTreeQuota(UnityResource):
    """
    Support CRUD operations for tree_quota

    Operations supported:
    create: Create tree_quota on the file_system path specified
    modify: Modify tree_quota on the file_system path specified
    delete: Delete tree_quota on the file_system using id
    """

    @classmethod
    def create(cls, cli, filesystem_id=None, path=None,
               description=None, hard_limit=None,
               soft_limit=None):
        """
        Creates tree_quota on the specified filesystem and path
        :param filesystem_id: This parameter will help create
            tree_quota on the filesystem and folder path specified
        :param path: Path of the tree quota relative to the root of
            the file system
        :param description: Description of the tree quota
        :param hard_limit: sets hard_limit on the file_system path
            specified. The default value 0 means no limitation
        :param soft_limit: sets soft_limit on the file_system path
            specified. The default value 0 means no limitation
        :return: instance of tree quota created.
        """
        fs_clz = storops.unity.resource.filesystem.UnityFileSystem
        filesystem = fs_clz.get(cli, filesystem_id)
        if not filesystem.existed:
            raise UnityResourceNotFoundError(
                'cannot find filesystem {}.'.format(filesystem_id))

        tree_quota_param = cls.prepare_tree_quota_create_parameters(
            filesystem, path, description, hard_limit, soft_limit)
        resp = cli.post(
            cls().resource_class, **tree_quota_param)
        resp.raise_if_err()
        return cls(_id=resp.resource_id, cli=cli)

    @classmethod
    def modify(cls, cli, tree_quota_id, description=None,
               hard_limit=None, soft_limit=None):
        """
        Modifies tree_quota params for the specified tree_quota_id
        :param tree_quota_id: This is required which specifies tree_quota to
            be modified
        :param description: Modified description of tree_quota
        :param hard_limit: modifies hard_limit for the
            tree_quota specified
        :param soft_limit: modifies soft_limit for the
            tree_quota specified
        :return: None
        """
        tree_quota = UnityTreeQuota.get(_id=tree_quota_id, cli=cli)
        if not tree_quota.existed:
            raise UnityResourceNotFoundError(
                'cannot find tree_quota {}.'.format(tree_quota_id))

        req_body = cli.make_body(
            description=description,
            hardLimit=hard_limit,
            softLimit=soft_limit
        )
        resp = cli.action(cls().resource_class, tree_quota_id,
                          'modify', **req_body)
        resp.raise_if_err()
        return resp

    @classmethod
    def delete(cls, cli, tree_quota_id):
        """
        Delete tree_quota
        :param tree_quota_id: Quota id of the tree_quota to be deleted
        :return: None
        """
        tree_quota = UnityTreeQuota.get(_id=tree_quota_id, cli=cli)
        if not tree_quota.existed:
            raise UnityResourceNotFoundError(
                'cannot find tree_quota {}.'.format(tree_quota_id))

        resp = cli.delete(cls().resource_class,
                          tree_quota_id)
        resp.raise_if_err()
        return resp

    @staticmethod
    def prepare_tree_quota_create_parameters(
            filesystem, path, description, hard_limit, soft_limit):
        """
        Prepare tree_quota for the create operation
        :param filesystem: Filesystem on which tree_quota needs to
            be created
        :param path: Path of the tree quota relative to the root of
            the file system
        :param description: Description of the tree_quota
        :param hard_limit: hard_limit for the tree_quota
        :param soft_limit: soft_limit for the tree_quota
        :return: tree_quota_params for create tree_quota preparation
        """
        tree_quota_param = UnityClient.make_body(
            filesystem=filesystem,
            path=path,
            description=description,
            hardLimit=hard_limit,
            softLimit=soft_limit)
        return tree_quota_param


class UnityTreeQuotaList(UnityResourceList):
    """
    List representation of tree_quota
    """

    def __init__(self, cli=None, **filters):
        super(UnityTreeQuotaList, self).__init__(cli, **filters)

    @classmethod
    def get_resource_class(cls):
        return UnityTreeQuota
