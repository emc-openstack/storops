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

from hamcrest import assert_that, equal_to, raises, instance_of

from storops_test.vnx.cli_mock import patch_cli, t_cli
from storops_test.vnx.resource.verifiers import verify_raid0
from storops.exception import VNXCreateRaidGroupError, \
    VNXDeleteRaidGroupError
from storops.vnx.resource.disk import VNXDisk
from storops.vnx.resource.rg import VNXRaidGroup

__author__ = 'Cedric Zhuang'


class VNXRaidGroupTest(TestCase):
    @patch_cli
    def test_get_rg(self):
        rg = VNXRaidGroup.get(t_cli(), 0)
        verify_raid0(rg)

    @patch_cli
    def test_get_rg_list(self):
        rgs = VNXRaidGroup.get(t_cli())
        assert_that(len(rgs), equal_to(7))
        for rg in rgs:
            if rg.raid_group_id == 0:
                verify_raid0(rg)
                break
        else:
            self.fail('RAID group 0 not found.')

    @patch_cli
    def test_create_rg(self):
        def f():
            VNXRaidGroup.create(t_cli(), 11, ['1_0_0', '1_0_1'])

        assert_that(f, raises(VNXCreateRaidGroupError, 'not supported'))

    @patch_cli
    def test_create_rg_invalid_raid_type(self):
        def f():
            VNXRaidGroup.create(t_cli(), 11, ['1_0_0', '1_0_1'], 'r12')

        assert_that(f, raises(ValueError, 'valid value'))

    @patch_cli
    def test_delete_rg(self):
        def f():
            VNXRaidGroup(11, t_cli()).delete()

        assert_that(f, raises(VNXDeleteRaidGroupError, 'Not Found'))

    @patch_cli
    def test_disks(self):
        rg = VNXRaidGroup(4, t_cli())
        disks = rg.disks
        assert_that(len(disks), equal_to(5))
        for disk in disks:
            assert_that(disk, instance_of(VNXDisk))
            assert_that(disk.existed, equal_to(True))

    @patch_cli
    def test_available_capacity_gbs(self):
        rg = VNXRaidGroup(4, t_cli())
        available_capacity = rg.available_capacity_gbs
        assert_that(available_capacity, equal_to(0.943))
