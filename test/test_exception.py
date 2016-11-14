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

from storops.exception import StoropsException, check_error, \
    VNXSpNotAvailableError, VNXNotSupportedError, UnityNameNotUniqueError
from storops.unity.resource.host import UnityHost

__author__ = 'Cedric Zhuang'


class DemoException(StoropsException):
    message_template = 'hello, {name}.'


class StrangeException(Exception):
    def __init__(self):
        super(StrangeException, self).__init__('strange exception')


class ExceptionTest(TestCase):
    def test_message(self):
        ex = DemoException(name='Peter')
        assert_that(ex.message, equal_to('hello, Peter.'))

    def test_not_enough_param(self):
        ex = DemoException()
        assert_that(ex.message, equal_to('hello, {name}.'))

    def test_code(self):
        ex = DemoException('code is {code}')
        assert_that(str(ex), equal_to('code is 500'))

    def test_exception_convert_to_message(self):
        ex = StoropsException(message=StrangeException())
        assert_that(str(ex), equal_to('strange exception'))

    def test_check_error_found(self):
        def f():
            out = ("A network error occurred while trying to connect: "
                   "'10.244.211.39'.\n"
                   "Message : Error occurred because of time out")
            check_error(out, VNXSpNotAvailableError)

        assert_that(f, raises(VNXSpNotAvailableError))

    def test_check_error_not_found(self):
        out = 'The specified source LUN is not currently migrating.'
        # no exception, not checking a `VNXLunNotMigratingError`
        check_error(out, VNXSpNotAvailableError)

    def test_check_error_found_in_multiple_errors(self):
        def f():
            out = ("A network error occurred while trying to connect: "
                   "'10.244.211.39'.\n"
                   "Message : Error occurred because of time out")
            check_error(out, VNXNotSupportedError, VNXSpNotAvailableError)

        assert_that(f, raises(VNXSpNotAvailableError))

    def test_check_error_not_found_in_multiple_errors(self):
        out = 'The specified source LUN is not currently migrating.'
        # no exception, not checking a `VNXLunNotMigratingError`
        check_error(out, VNXNotSupportedError, VNXSpNotAvailableError)

    def test_unity_name_not_unique_error(self):
        ex = UnityNameNotUniqueError(objects=None)
        assert_that(str(ex), equal_to('multiple objects found'))
        assert_that(ex.objects, equal_to(None))

        host = UnityHost(_id=9999)
        ex = UnityNameNotUniqueError("Multipath hosts found.", objects=host)
        assert_that(str(ex), equal_to('Multipath hosts found.'))
        assert_that(ex.objects, equal_to(host))
