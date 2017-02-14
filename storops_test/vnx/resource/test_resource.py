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

from hamcrest import assert_that, equal_to, raises

from storops.vnx.resource import VNXCliResource

__author__ = 'Cedric Zhuang'


class VNXCliResourceTest(TestCase):
    def test_with_poll(self):
        r = VNXCliResource()
        assert_that(r.poll, equal_to(True))
        r.poll = False
        assert_that(r.poll, equal_to(False))
        with r.with_poll():
            assert_that(r.poll, equal_to(True))
        assert_that(r.poll, equal_to(False))

    def test_no_with(self):
        r = VNXCliResource()
        r.with_poll()
        assert_that(r.poll, equal_to(True))
        r.with_no_poll()
        assert_that(r.poll, equal_to(False))

    def test_with_no_poll(self):
        r = VNXCliResource()
        assert_that(r.poll, equal_to(True))
        with r.with_no_poll():
            assert_that(r.poll, equal_to(False))
        assert_that(r.poll, equal_to(True))

    class DemoCliResourceRaiseException(VNXCliResource):
        @staticmethod
        def do():
            raise ValueError('test error.')

    def test_exception_in_with(self):
        def f():
            r = self.DemoCliResourceRaiseException()
            with r.with_no_poll():
                r.do()
        assert_that(f, raises(ValueError, 'test error'))
