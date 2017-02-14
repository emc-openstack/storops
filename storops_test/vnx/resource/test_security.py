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

from hamcrest import equal_to, assert_that, raises

from storops import VNXUserRoleEnum, VNXUserScopeEnum
from storops.exception import VNXUserNameInUseError, VNXUserNotFoundError
from storops_test.vnx.cli_mock import t_cli, patch_cli

from storops.vnx.resource.security import VNXBlockUser

__author__ = 'Cedric Zhuang'


class VNXSecurityTest(TestCase):
    @patch_cli
    def test_get_existed_user(self):
        user = VNXBlockUser.get(name='a', cli=t_cli())
        assert_that(user.name, equal_to('a'))
        assert_that(user.role, equal_to(VNXUserRoleEnum.ADMIN))
        assert_that(user.scope, equal_to(VNXUserScopeEnum.GLOBAL))
        assert_that(user.type, equal_to('user'))

    @patch_cli
    def test_get_all_users(self):
        users = VNXBlockUser.get(cli=t_cli())
        assert_that(len(users), equal_to(2))

    @patch_cli
    def test_get_user_not_found(self):
        user = VNXBlockUser(name='c', cli=t_cli())
        assert_that(user.existed, equal_to(False))

    @patch_cli
    def test_create_user_success(self):
        user = VNXBlockUser.create(t_cli(), 'b', 'b')
        assert_that(user.name, equal_to('b'))
        assert_that(user.role, equal_to(VNXUserRoleEnum.ADMIN))

    @patch_cli
    def test_create_user_existed(self):
        def f():
            VNXBlockUser.create(t_cli(), 'b', 'b',
                                role=VNXUserRoleEnum.OPERATOR)

        assert_that(f, raises(VNXUserNameInUseError, 'failed'))

    @patch_cli
    def test_delete_user_success(self):
        user = VNXBlockUser.get(name='b', cli=t_cli())
        # no exception
        user.delete()

    @patch_cli
    def test_delete_user_not_found(self):
        def f():
            user = VNXBlockUser('c', cli=t_cli())
            user.delete()

        assert_that(f, raises(VNXUserNotFoundError, 'not exist'))
