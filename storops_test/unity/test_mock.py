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

from hamcrest import assert_that, is_not, equal_to
from hamcrest import contains_string

from storops_test.unity.rest_mock import MockRestClient

__author__ = 'Cedric Zhuang'


class TestMockRestClient(unittest.TestCase):
    def test_get_folder_from_url(self):
        url = '/api/types/metric?compact=true&fields=name,type'
        folder = MockRestClient.get_folder_from_url(url)
        assert_that(folder, is_not(contains_string('api')))
        assert_that(folder, is_not(contains_string('types')))
        assert_that(folder, contains_string('metric'))

    def test_get_folder_from_instance_url(self):
        url = '/api/instances/lun/sv_2'
        folder = MockRestClient.get_folder_from_url(url)
        assert_that(folder, is_not(contains_string('api')))
        assert_that(folder, is_not(contains_string('types')))
        assert_that(folder, contains_string('lun'))

    def test_get_filename(self):
        inputs = ['/api/instances/lun/sv_2?compact=True&fields=type,wwn', None]
        name = MockRestClient.get_filename(inputs)
        assert_that(name, equal_to('for_test.json'))
