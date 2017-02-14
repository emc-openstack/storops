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

from unittest import TestCase

from hamcrest import assert_that, equal_to, has_items, starts_with

from storops.unity.resource.type_resource import UnityType
from storops_test.unity.rest_mock import patch_rest, t_rest

__author__ = 'Cedric Zhuang'


class UnityTypeTest(TestCase):
    @patch_rest
    def test_get_metric_type(self):
        t = UnityType(_id='metric', cli=t_rest())
        assert_that(t.name, equal_to('metric'))
        assert_that(t.existed, equal_to(True))

    @patch_rest
    def test_get_lun_type(self):
        t = UnityType(_id='lun', cli=t_rest())
        assert_that(t.fields, has_items('creationTime', 'name', 'snapCount'))

    def test_get_type_fields(self):
        t = UnityType(_id='type')
        assert_that(t.fields_str, starts_with(
            'name,description,documentation,type,attributes.name'))

    @patch_rest
    def test_fields_str(self):
        t = UnityType(_id='lun', cli=t_rest())
        assert_that(t.fields_str, starts_with('auSize,creationTime,'))
