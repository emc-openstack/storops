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

import json
import os
from unittest import TestCase

from hamcrest import assert_that, equal_to, only_contains, raises, none

from storops.exception import UnityNasServerNameUsedError, UnityException
from storops.unity.resp import RestResponse
from test.utils import read_test_file

__author__ = 'Cedric Zhuang'


def read_json(folder, filename):
    raw = read_test_file(os.path.join('unity', 'rest_data', folder), filename)
    return json.loads(raw, encoding='utf-8')


def read_error_json(filename):
    return read_json('error', filename)


class RestResponseTest(TestCase):
    def test_has_next_page(self):
        resp = RestResponse(read_json('metric', 'metrics_page_1.json'))
        assert_that(resp.next_page, equal_to(2))
        assert_that(resp.has_next_page, equal_to(True))

    def test_has_current_page(self):
        resp = RestResponse(read_json('metric', 'metrics_page_1.json'))
        assert_that(resp.current_page, equal_to(1))


class UnityErrorTest(TestCase):
    def test_get_properties(self):
        body = read_error_json('409.json')
        resp = RestResponse(body)
        assert_that(resp.has_error(), equal_to(True))
        err = resp.error
        assert_that(err.existed, equal_to(True))
        assert_that(str(err.created),
                    equal_to('2016-03-16 15:13:45.977000+00:00'))
        assert_that(err.get_messages(), only_contains(
            'The name of NAS server is already in use. '
            '(Error Code:0x6702024)'))
        assert_that(err.http_status_code, equal_to(409))
        assert_that(err.error_code, equal_to(108011556))

    def test_raise_if_err_409(self):
        def f():
            body = read_error_json('409.json')
            resp = RestResponse(body)
            resp.raise_if_err()

        assert_that(f, raises(UnityNasServerNameUsedError, 'in use'))

    def test_raise_if_err_nothing(self):
        body = read_error_json('200.json')
        resp = RestResponse(body)
        resp.raise_if_err()


class UnityExceptionTest(TestCase):
    def test_unity_exception_error_code(self):
        resp = RestResponse(read_error_json('409.json'))
        ex = UnityException(resp.error)
        assert_that(ex.error_code, equal_to(108011556))

    def test_unity_exception_default_error_code(self):
        assert_that(UnityException().error_code, none())
