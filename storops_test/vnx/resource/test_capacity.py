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

from hamcrest import assert_that, equal_to
from storops.vnx.resource.capacity import VNXCapacity
from storops_test.vnx.cli_mock import patch_cli, t_cli

__author__ = 'Tina Tang'


class VNXCapacityTest(TestCase):
    @patch_cli
    def test_total(self):
        capacity = VNXCapacity.get(t_cli())
        assert_that(capacity.total, equal_to(178269.891))

    @patch_cli
    def test_free_raw_disk(self):
        capacity = VNXCapacity.get(t_cli())
        assert_that(capacity.free_raw_disk, equal_to(42170.744))

    @patch_cli
    def test_free_storage_pool(self):
        capacity = VNXCapacity.get(t_cli())
        assert_that(capacity.free_storage_pool, equal_to(11958.398))

    @patch_cli
    def test_used(self):
        capacity = VNXCapacity.get(t_cli())
        assert_that(capacity.used, equal_to(124140.749))
