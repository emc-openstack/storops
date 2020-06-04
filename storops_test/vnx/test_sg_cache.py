# coding=utf-8
# Copyright (c) 2020 Dell Inc. or its subsidiaries.
# All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
from __future__ import unicode_literals

import tempfile
from unittest import TestCase

from hamcrest import equal_to, assert_that

from storops import SGCache


class SGCacheTest(TestCase):
    def test_set_and_get(self):
        folder = tempfile.mkdtemp(suffix='storops')
        cache = SGCache(folder)
        cache['sg-1'] = {'abc': 'efg'}

        cache_get = SGCache(folder)
        assert_that('sg-1' in cache_get, equal_to(True))
        assert_that('abc' in cache_get['sg-1'], equal_to(True))
        assert_that(cache_get['sg-1']['abc'], equal_to('efg'))
