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

import threading
from unittest import TestCase

from hamcrest import assert_that, equal_to, only_contains

from comptest.utils import ResourceManager
from test.utils import PersistedDict

__author__ = 'Cedric Zhuang'


class PersistedDictTest(TestCase):
    @staticmethod
    def test_dict():
        name = 'PersistedDictTest_{}'.format(threading.current_thread().ident)
        return PersistedDict(name, list)

    @classmethod
    def setUpClass(cls):
        cls.d = cls.test_dict()
        cls.d.clear()
        cls.d['a'] = 'a1'
        cls.d['b'] = ['b1', 'b2']

    @classmethod
    def tearDownClass(cls):
        cls.d.destroy()
        cls.d.clear_lock_file()

    def test_get_item(self):
        assert_that(self.d['a'], equal_to('a1'))
        assert_that(self.d['b'], only_contains('b1', 'b2'))

    def test_other_instance_get_item(self):
        a = self.test_dict()
        assert_that(a['a'], equal_to('a1'))

    def test_set_item(self):
        a1 = PersistedDict('test_set_item', list)
        a1.clear()
        v = a1['b']
        v.append('b1')
        v.append('b2')
        a1['b'] = v
        a1['c'] = 'c1'

        a2 = PersistedDict('test_set_item')
        assert_that(len(a2), equal_to(2))
        assert_that(a2['c'], equal_to('c1'))
        assert_that(a2['b'], only_contains('b1', 'b2'))

        a1.destroy()

    def test_default_value(self):
        assert_that(self.d['d'], equal_to([]))


class SampleResource(object):
    def __init__(self):
        self.update_count = 0

    def update(self):
        self.update_count += 1

    @property
    def existed(self):
        return self.update_count >= 1


class ResourceManagerTest(TestCase):
    def test_until_existed(self):
        rsc = SampleResource()
        ResourceManager.until_existed(rsc)
        assert_that(rsc.update_count, equal_to(1))

    def test_until_customized(self):
        rsc = SampleResource()
        ResourceManager.until(rsc, lambda x: x.update_count >= 1)
        assert_that(rsc.update_count, equal_to(1))
