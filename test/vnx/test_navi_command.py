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

import time
from unittest import TestCase

from hamcrest import equal_to, assert_that, raises, less_than

from storops.exception import VNXCredentialError
from storops.vnx.navi_command import NaviCommand
from test.vnx.cli_mock import patch_cli

__author__ = 'Cedric Zhuang'


class NaviCommandTest(TestCase):
    @patch_cli
    def test_username_password(self):
        cmd = NaviCommand('a', 'a', 1)
        assert_that(' '.join(map(str, cmd.get_credentials())),
                    equal_to('-user a -password a -scope 1'))

    @patch_cli
    def test_default_security_file(self):
        cmd = NaviCommand()
        assert_that(cmd.get_credentials(), equal_to([]))

    @patch_cli
    def test_security_file(self):
        cmd = NaviCommand(sec_file=r'/a/b/c.key')
        assert_that(' '.join(cmd.get_credentials()),
                    equal_to('-secfilepath /a/b/c.key'))

    @patch_cli
    def test_security_file_precedence(self):
        cmd = NaviCommand(sec_file=r'/a/b/c.key',
                          username='admin', password='')
        assert_that(' '.join(cmd.get_credentials()),
                    equal_to('-secfilepath /a/b/c.key'))

    @patch_cli
    def test_username_password_timeout(self):
        cmd = NaviCommand('a', 'a', 1, timeout=20)
        assert_that(' '.join(map(str, cmd.get_credentials())),
                    equal_to('-user a -password a -scope 1 -t 20'))

    @patch_cli
    def test_sec_file_empty_string(self):
        cmd = NaviCommand('a', 'a', 1, '', timeout=20)
        assert_that(' '.join(map(str, cmd.get_credentials())),
                    equal_to('-user a -password a -scope 1 -t 20'))

    @patch_cli
    def test_timeout_max_and_min(self):
        cmd = NaviCommand()
        cmd._timeout = 0.5
        assert_that(cmd.timeout, equal_to(cmd.MIN_TIMEOUT))
        cmd._timeout = 10 ** 10
        assert_that(cmd.timeout, equal_to(cmd.MAX_TIMEOUT))

    @patch_cli(output='security_low.txt')
    def test_security_level_low(self):
        cmd = NaviCommand()
        assert_that(cmd.get_security_level('naviseccli'), equal_to('low'))

    def test_error_credentials(self):
        cmd = NaviCommand('a')
        assert_that(cmd.is_credential_valid, equal_to(True))
        assert_that(cmd.get_credentials, raises(VNXCredentialError, 'missing'))
        assert_that(cmd.is_credential_valid, equal_to(False))

    def test_timeout_error(self):
        cmd = NaviCommand()
        start = time.time()
        cmd.execute('python'.split(), timeout=0.1)
        dt = time.time() - start
        assert_that(dt, less_than(1))
