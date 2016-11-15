# Copyright (c) 2016 EMC Corporation.
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
# coding=utf-8
from __future__ import unicode_literals

from storops.unity.resource import UnityResource, UnityResourceList

__author__ = 'Cedric Zhuang'


class UnityDisk(UnityResource):
    @property
    def inserted(self):
        return self.raw_size > 0


class UnityDiskList(UnityResourceList):
    def __init__(self, **the_filter):
        if 'inserted' in the_filter:
            self._inserted = the_filter['inserted']
            del the_filter['inserted']
        else:
            self._inserted = None

        super(UnityDiskList, self).__init__(**the_filter)

    def _filter(self, item):
        ret = True
        if self._inserted is not None:
            ret = item.inserted == self._inserted
        return ret

    @classmethod
    def get_resource_class(cls):
        return UnityDisk
