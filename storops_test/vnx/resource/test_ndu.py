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

from storops_test.vnx.cli_mock import patch_cli, t_cli
from storops.vnx.resource.ndu import VNXNdu

__author__ = 'Cedric Zhuang'


class VNXNduTest(TestCase):
    @patch_cli
    def test_get_all(self):
        ndu_list = VNXNdu.get(t_cli())
        assert_that(len(ndu_list), equal_to(16))

    @patch_cli
    def test_get(self):
        ndu = VNXNdu.get(t_cli(), '-VNXSnapshots')
        assert_that(ndu.name, equal_to('-VNXSnapshots'))
        assert_that(ndu.revision, equal_to('-'))
        assert_that(ndu.commit_required, equal_to(False))
        assert_that(ndu.revert_possible, equal_to(False))
        assert_that(ndu.active_state, equal_to(True))
        assert_that(ndu.is_installation_completed, equal_to(True))
        assert_that(ndu.is_this_system_software, equal_to(False))

    @patch_cli(output='-np_ndu_-list_-name_-Deduplication_no.txt')
    def test_is_dedup_enabled_false(self):
        assert_that(VNXNdu.is_dedup_enabled(t_cli()), equal_to(False))

    @patch_cli
    def test_is_dedup_enabled(self):
        assert_that(VNXNdu.is_dedup_enabled(t_cli()), equal_to(True))

    @patch_cli
    def test_is_compression_enabled(self):
        assert_that(VNXNdu.is_compression_enabled(t_cli()), equal_to(True))

    @patch_cli
    def test_is_snap_enabled(self):
        assert_that(VNXNdu.is_snap_enabled(t_cli()), equal_to(True))

    @patch_cli
    def test_is_mirror_view_async_enabled(self):
        assert_that(VNXNdu.is_mirror_view_async_enabled(t_cli()),
                    equal_to(True))

    @patch_cli
    def test_is_mirror_view_sync_enabled(self):
        assert_that(VNXNdu.is_mirror_view_sync_enabled(t_cli()),
                    equal_to(True))

    @patch_cli
    def test_is_mirror_view_enabled(self):
        assert_that(VNXNdu.is_mirror_view_enabled(t_cli()),
                    equal_to(True))

    @patch_cli
    def test_is_thin_enabled(self):
        assert_that(VNXNdu.is_thin_enabled(t_cli()), equal_to(True))

    @patch_cli
    def test_is_sancopy_enabled(self):
        assert_that(VNXNdu.is_sancopy_enabled(t_cli()), equal_to(True))

    @patch_cli
    def test_is_auto_tiering_enabled(self):
        assert_that(VNXNdu.is_auto_tiering_enabled(t_cli()), equal_to(True))

    @patch_cli
    def test_is_fast_cache_enabled(self):
        assert_that(VNXNdu.is_fast_cache_enabled(t_cli()), equal_to(True))
