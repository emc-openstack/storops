# coding=utf-8
# Copyright (c) 2016 EMC Corporation.
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

from hamcrest import assert_that, equal_to, only_contains

from storops.unity.parser import NestedProperties


class NestedPropertiesTest(TestCase):

    def test_build_nested_properties(self):
        np1 = NestedProperties.build(None)
        assert_that(np1, equal_to(None))
        np2 = NestedProperties.build('aa.bb')
        assert_that(np2.query_fields, only_contains('aa.bb'))
        np3 = NestedProperties.build(('aa_bb.cc', 'cc.dd'))
        assert_that(np3.query_fields, only_contains('aaBb.cc', 'cc.dd'))

    def test_get_properties(self):
        nested_props = NestedProperties('ab_cd.ef.c',
                                        'aaa_bb.ccc')
        properties = nested_props.get_properties()
        assert_that(properties, only_contains('ab_cd', 'aaa_bb'))

    def test_query_fields(self):
        nested_props = NestedProperties('ab_cd.ef.c',
                                        'aaa_bb.ccc_dd')
        assert_that(nested_props.query_fields, only_contains('abCd.ef.c',
                                                             'aaaBb.cccDd'))

    def test_get_child_subtree(self):
        nested_props = NestedProperties('ab_cd.ef.c',
                                        'ab_cd.ef.d',
                                        'aaa_bb.ccc_dd',
                                        'aaa_bb.ee_ff')
        sub1 = nested_props.get_child_subtree('ab_cd')
        assert_that(sub1.get_properties(), only_contains('ef'))
        sub1sub = sub1.get_child_subtree('ef')
        assert_that(sub1sub.get_properties(), only_contains('c', 'd'))
        sub2 = nested_props.get_child_subtree('aaa_bb')
        assert_that(sub2.get_properties(), only_contains('ccc_dd', 'ee_ff'))
