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

from hamcrest import assert_that, equal_to, has_items

from storops_test.vnx.nas_mock import t_nas, patch_post
from storops.vnx.resource.nas_pool import VNXNasPool

__author__ = 'Jay Xu'


class VNXNasPoolTest(unittest.TestCase):
    @patch_post
    def test_get_all(self):
        pool_list = VNXNasPool.get(cli=t_nas())
        assert_that(len(pool_list), equal_to(6))

    @patch_post
    def test_get_by_name(self):
        pool = VNXNasPool.get(name='vnx-sg_test', cli=t_nas())
        self.verify_pool_vnx_sg_test(pool)

    @patch_post
    def test_get_by_pool_id(self):
        pool = VNXNasPool.get(pool_id=63, cli=t_nas())
        self.verify_pool_vnx_sg_test(pool)

    @patch_post
    def test_get_by_name_not_found(self):
        pool = VNXNasPool(name='not_found', cli=t_nas())
        assert_that(pool.existed, equal_to(False))

    def verify_pool_vnx_sg_test(self, pool):
        assert_that(pool.movers_id, has_items(1, 2))
        assert_that(pool.member_volumes, has_items(105))
        assert_that(pool.name, equal_to('vnx-sg_test'))
        assert_that(pool.description, equal_to("vnx-sg_test on 000196800192"))
        assert_that(pool.may_contain_slices_default, equal_to(False))
        assert_that(pool.disk_type, equal_to('Mixed'))
        assert_that(pool.size, equal_to(0))
        assert_that(pool.used_size, equal_to(0))
        assert_that(pool.total_size, equal_to(2077))
        assert_that(pool.virtual_provisioning, equal_to(True))
        assert_that(pool.is_homogeneous, equal_to(True))
        assert_that(pool.template_pool, equal_to(63))
        assert_that(pool.stripe_count, equal_to(8))
        assert_that(pool.stripe_size, equal_to(256))
        assert_that(pool.pool_id, equal_to(63))

    def test_get_id(self):
        pool = VNXNasPool(pool_id=12)
        assert_that(pool.get_id(pool), equal_to(12))
        assert_that(pool.get_id('22'), equal_to(22))
