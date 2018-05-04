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

from storops.unity.resource import UnityResource, UnityResourceList

__author__ = 'Cedric Zhuang'


class UnityStorageResource(UnityResource):
    @classmethod
    def get(cls, cli, _id=None):
        if not isinstance(_id, cls):
            ret = cls(_id=_id, cli=cli)
        else:
            ret = _id
        return ret

    def action(self, action_name, **kwargs):
        return self._cli.action(self.resource_class,
                                self.get_id(),
                                action_name,
                                **kwargs)

    def modify_fs(self, **kwargs):
        return self.action('modifyFilesystem', **kwargs)


class UnityStorageResourceList(UnityResourceList):
    @classmethod
    def get_resource_class(cls):
        return UnityStorageResource
