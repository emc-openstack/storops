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

from hamcrest import assert_that, equal_to, raises, contains_string, \
    only_contains

from storops.exception import VNXNasObjectNotFound, \
    VNXInvalidMoverID, VNXFileCredentialError
from storops.vnx.nas_client import NasXmlResponse, XmlStatus
from test.vnx.nas_mock import MockXmlPost

__author__ = 'Cedric Zhuang'


class NasXmlResponseTest(TestCase):
    @property
    def fs_not_found(self):
        return NasXmlResponse(MockXmlPost.read_file('fs_not_found.xml'))

    @property
    def invalid_dm(self):
        return NasXmlResponse(MockXmlPost.read_file('invalid_data_mover.xml'))

    def test_is_ok(self):
        resp = self.fs_not_found
        assert_that(resp.is_ok(), equal_to(False))

    def test_credential_error(self):
        def f():
            NasXmlResponse(MockXmlPost.read_file('credential_error.html'))

        assert_that(f, raises(VNXFileCredentialError, 'credential error'))

    def test_has_error_code(self):
        resp = self.fs_not_found
        assert_that(resp.has_error_code('18522112101'), equal_to(True))
        assert_that(resp.has_error_code(18522112101), equal_to(True))
        assert_that(resp.has_error_code(18522112102), equal_to(False))

    def test_status(self):
        resp = self.fs_not_found
        assert_that(resp.status, equal_to(XmlStatus.WARNING))

    def test_problem_message_codes(self):
        resp = self.fs_not_found
        assert_that(resp.problem_message_codes, equal_to({18522112101, }))

    def test_problem_diagnostics(self):
        resp = self.fs_not_found
        assert_that(resp.problem_diagnostics, contains_string(
            'Migration file system not found.'))
        assert_that(resp.problem_diagnostics, contains_string(
            'File system not found.'))

    def test_problem_messages(self):
        resp = self.fs_not_found
        assert_that(resp.problem_messages, equal_to(
            'The query may be incomplete or requested object not found.'))

    def test_check_invalid_data_mover(self):
        def f():
            resp = self.invalid_dm
            resp.check_invalid_data_mover()

        assert_that(f, raises(VNXInvalidMoverID, 'id=100 not found'))

    def test_raise_if_not_found(self):
        def f():
            resp = self.fs_not_found
            resp.raise_if_no_object('no fs here')

        assert_that(f, raises(VNXNasObjectNotFound, 'no fs here'))

    def test_get_problem_string(self):
        resp = self.fs_not_found
        problems = resp.get_problems_string(' ' * 4)
        assert_that(problems, contains_string('    (1) code: 18522112101'))
        assert_that(problems, contains_string('        message: The query'))
        assert_that(problems, contains_string('        diagnostics:'))

    def test_problem_message_codes_hex(self):
        resp = self.fs_not_found
        assert_that(resp.hex_problem_message_codes,
                    only_contains('0x450010065'))
