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

from hamcrest import assert_that, equal_to, instance_of, only_contains, raises

from storops.unity.resource.health import UnityHealth
from storops.unity.resource.sp import UnityStorageProcessor, \
    UnityStorageProcessorList
from storops.unity.resource.system import UnityDpe
from storops.unity.enums import NodeEnum
from test.unity.rest_mock import t_rest, patch_rest

__author__ = 'Cedric Zhuang'


class UnityStorageProcessorTest(TestCase):
    @patch_rest()
    def test_properties(self):
        sp = UnityStorageProcessor(_id='spa', cli=t_rest())
        assert_that(sp.id, equal_to('spa'))
        assert_that(sp.existed, equal_to(True))
        assert_that(sp.health, instance_of(UnityHealth))
        assert_that(sp.needs_replacement, equal_to(False))
        assert_that(sp.is_rescue_mode, equal_to(False))
        assert_that(sp.model, equal_to('OBERON CANISTER 10C 105W 2.6G'))
        assert_that(sp.slot_number, equal_to(0))
        assert_that(sp.name, equal_to('SP A'))
        assert_that(sp.emc_part_number, equal_to('110-297-008C-04'))
        assert_that(sp.emc_serial_number, equal_to('CF2HF150300001'))
        assert_that(sp.manufacturer, equal_to(''))
        assert_that(sp.vendor_part_number, equal_to(''))
        assert_that(sp.vendor_serial_number, equal_to(''))
        assert_that(sp.sas_expander_version, equal_to('2.7.1'))
        assert_that(sp.bios_firmware_revision, equal_to('30.89'))
        assert_that(sp.post_firmware_revision, equal_to('21.2'))
        assert_that(sp.memory_size, equal_to(65536))
        assert_that(sp.parent_dpe, instance_of(UnityDpe))

    @patch_rest()
    def test_sp_to_node_enum(self):
        sp = UnityStorageProcessor(_id='spa', cli=t_rest())
        assert_that(sp.to_node_enum(), equal_to(NodeEnum.SPA))

    @patch_rest()
    def test_get_all_and_property_query(self):
        sp_list = UnityStorageProcessorList(cli=t_rest())
        assert_that(len(sp_list), equal_to(2))
        assert_that(sp_list.name, only_contains('SP A', 'SP B'))

    @patch_rest()
    def test_get_all_and_property_not_found(self):
        def f():
            sp_list = UnityStorageProcessorList(cli=t_rest())
            return sp_list.not_found

        assert_that(f, raises(AttributeError, 'not_found'))
