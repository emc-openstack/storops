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

import unittest

from hamcrest import assert_that, instance_of, has_items, equal_to, raises, \
    is_not

from storops.lib.common import instance_cache
from storops.lib.resource import ResourceListCollection
from storops.unity.resource.lun import UnityLun
from storops.unity.resource.sp import UnityStorageProcessor, \
    UnityStorageProcessorList
from test.unity.rest_mock import t_unity, patch_rest

__author__ = 'Cedric Zhuang'


class ResourceListCollectionTest(unittest.TestCase):
    @instance_cache
    def get_rlc(self):
        return ResourceListCollection(
            (t_unity().get_sp(), t_unity().get_lun()))

    def test_get_rsc_list(self):
        rsc_list = self.get_rlc().get_rsc_list(UnityStorageProcessor)
        assert_that(rsc_list, instance_of(UnityStorageProcessorList))

    def test_get_rsc_clz_list(self):
        clz_list = self.get_rlc().get_rsc_clz_list()
        assert_that(clz_list, has_items(UnityStorageProcessor, UnityLun))

    def test_len(self):
        assert_that(len(self.get_rlc()), equal_to(2))

    def test_add_rsc_list_wrong_type(self):
        def f():
            self.get_rlc().add_rsc_list('abc')

        assert_that(f, raises(ValueError))

    def test_add_rsc_list_success(self):
        rlc = self.get_rlc()
        rlc.add_rsc_list(t_unity().get_disk())
        assert_that(len(rlc), equal_to(3))

    @patch_rest
    def test_update(self):
        rlc = self.get_rlc()
        t0 = rlc.timestamp
        rlc.update()
        assert_that(t0, is_not(equal_to(rlc.timestamp)))


class ResourceListTest(unittest.TestCase):
    @patch_rest
    def test_add_resource_list(self):
        ret = t_unity().get_ethernet_port() + t_unity().get_link_aggregation()
        assert_that(len(ret), equal_to(10))

    def test_add_resource_list_type_error(self):
        def do():
            return t_unity().get_ethernet_port() + None
        assert_that(do, raises(TypeError))
