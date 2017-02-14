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

import six
from hamcrest import assert_that, equal_to, none, only_contains

from storops.lib.parser import PropMapper, PropDescriptor, OutputParser

__author__ = 'Cedric Zhuang'


class PropMapperTest(TestCase):
    def test_camel_case_to_under_score(self):
        test_data = {
            'AbcDef': 'ABC_DEF',
            'abc def': 'ABC_DEF',
            'abc:': 'ABC',
            'SPAWrites': 'SPA_WRITES',
            'Is Thin LUN': 'IS_THIN_LUN',
            'TestCIMElement': 'TEST_CIM_ELEMENT'
        }

        for (k, v) in six.iteritems(test_data):
            assert_that(PropMapper.camel_case_to_under_score(k).upper(),
                        equal_to(v))

    def test_camel_case_to_under_score_with_delimiter(self):
        test_data = {
            'AbcDef': 'ABC.DEF',
            'abc def': 'ABC.DEF',
            'Is Thin LUN': 'IS.THIN.LUN',
            'abc:': 'ABC',
            'SPAWrites': 'SPA.WRITES',
            'TestCIMElement': 'TEST.CIM.ELEMENT',
            'VALUE_ARRAY': 'VALUE.ARRAY',
            'LUNs': 'LUNS',
            'Source LUN(s)': 'SOURCE.LUNS',
            'Capacity (GBs)': 'CAPACITY.GBS'
        }

        for (k, v) in six.iteritems(test_data):
            assert_that(PropMapper.camel_case_to_under_score(k, '.').upper(),
                        equal_to(v))


A = PropDescriptor('-a', 'Prop A (name):', 'prop_a')
B = PropDescriptor('-b', 'Prop B:')
C = PropDescriptor('-c', 'Prop C:')
ID = PropDescriptor(None, 'ID:', is_index=True)


class DemoParser(OutputParser):
    def __init__(self):
        super(DemoParser, self).__init__()
        self.add_property(A, B, C, ID)


class OutputParserTest(TestCase):
    def test_sequence(self):
        parser = DemoParser()
        index = parser.index_property
        assert_that(index.sequence, equal_to(3))

    def test_property_key(self):
        parser = DemoParser()
        assert_that(parser.has_property_key('prop_a'), equal_to(True))
        assert_that(parser.has_property_key('prop_b'), equal_to(True))
        assert_that(parser.has_property_key('D'), equal_to(False))

    def test_get_property_label_found(self):
        parser = DemoParser()
        assert_that(parser.get_property_label('prop_a'),
                    equal_to('Prop A (name):'))

    def test_get_property_label_not_found(self):
        parser = DemoParser()
        assert_that(parser.get_property_label('na'), none())

    def test_get_property_key_found(self):
        parser = DemoParser()
        assert_that(parser.get_property_key('Prop A (name):'),
                    equal_to('prop_a'))

    def test_get_property_key_not_found(self):
        parser = DemoParser()
        assert_that(parser.get_property_key('Prop B (name):'), none())

    def test_property_names(self):
        parser = DemoParser()
        assert_that(parser.property_names,
                    only_contains('id', 'prop_a', 'prop_b', 'prop_c'))
