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

import os
from unittest import TestCase

from hamcrest import assert_that, equal_to

from storops_test.utils import read_test_file
from storops_test.vnx.nas_mock import MockXmlPost

__author__ = 'Cedric Zhuang'


class NasMockTest(TestCase):
    def test_get_name(self):
        post_body = read_test_file(self.get_folder(), 'fs_single_post.xml')
        filename = MockXmlPost.get_filename(post_body)
        assert_that(filename,
                    equal_to('get_fs_abc.xml'))

    def get_folder(self):
        return os.path.join('vnx', 'testdata', 'nas_xml_output')

    def test_get_folder(self):
        post_body = read_test_file(self.get_folder(), 'fs_single_post.xml')
        folder = MockXmlPost.get_folder(post_body)
        expected = os.path.join(self.get_folder(), 'Query',
                                'FileSystemQueryParams')
        assert_that(folder, equal_to(expected))
