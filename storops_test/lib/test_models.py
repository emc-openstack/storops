# coding=utf-8
# Copyright (c) 2017 Dell Inc. or its subsidiaries.
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

import operator
from unittest import TestCase

import ddt
from hamcrest import assert_that, equal_to

from storops.lib.models import UnityModel


@ddt.ddt
class TestUnityModel(TestCase):
    def test_model_info(self):
        unity_model = UnityModel('Unity 880F')
        assert_that(unity_model.model, equal_to('880F'))
        assert_that(unity_model.model_base, equal_to('880'))
        assert_that(unity_model.series, equal_to('8'))
        assert_that(unity_model.is_all_flash, equal_to(True))

    @ddt.data(
        {'model': 'Unity 380F', 'expected': True},
        {'model': 'Unity 380', 'expected': False},
    )
    @ddt.unpack
    def test_is_all_flash(self, model, expected):
        unity_model = UnityModel(model)
        assert_that(unity_model.is_all_flash, equal_to(expected))

    @ddt.data(
        {'model_1': 'Unity 880F', 'model_2': 'Unity 870F', 'expected': True},
        {'model_1': 'Unity 880F', 'model_2': 'Unity 890F', 'expected': True},
        {'model_1': 'Unity 880F', 'model_2': 'Unity 880', 'expected': False},
        {'model_1': 'Unity 880', 'model_2': 'Unity 880F', 'expected': False},
        {'model_1': 'Unity 680F', 'model_2': 'Unity 880F', 'expected': False},
    )
    @ddt.unpack
    def test_is_same_model_series(self, model_1, model_2, expected):
        unity_model_1 = UnityModel(model_1)
        unity_model_2 = UnityModel(model_2)
        assert_that(unity_model_1.is_same_series(unity_model_2),
                    equal_to(expected))

    @ddt.data(
        {'model_1': 'Unity 880F', 'model_2': 'Unity 880F',
         'op': operator.eq, 'expected': True},
        {'model_1': 'Unity 880F', 'model_2': 'Unity 880',
         'op': operator.eq, 'expected': False},
        {'model_1': 'Unity 880', 'model_2': 'Unity 880F',
         'op': operator.eq, 'expected': False},
        {'model_1': 'Unity 880F', 'model_2': 'Unity 870F',
         'op': operator.eq, 'expected': False},
        {'model_1': 'Unity 380', 'model_2': 'Unity 380',
         'op': operator.eq, 'expected': True},
        {'model_1': 'Unity 880F', 'model_2': 'Unity 870F',
         'op': operator.gt, 'expected': True},
        {'model_1': 'Unity 880F', 'model_2': 'Unity 880F',
         'op': operator.gt, 'expected': False},
        {'model_1': 'Unity 880F', 'model_2': 'Unity 890F',
         'op': operator.gt, 'expected': False},
        {'model_1': 'Unity 880F', 'model_2': 'Unity 770F',
         'op': operator.gt, 'expected': False},
        {'model_1': 'Unity 880F', 'model_2': 'Unity 870',
         'op': operator.gt, 'expected': False},
        {'model_1': 'Unity 380', 'model_2': 'Unity 370',
         'op': operator.gt, 'expected': True},
        {'model_1': 'Unity 880F', 'model_2': 'Unity 870F',
         'op': operator.ge, 'expected': True},
        {'model_1': 'Unity 880F', 'model_2': 'Unity 880F',
         'op': operator.ge, 'expected': True},
        {'model_1': 'Unity 880F', 'model_2': 'Unity 890F',
         'op': operator.ge, 'expected': False},
        {'model_1': 'Unity 880F', 'model_2': 'Unity 770F',
         'op': operator.ge, 'expected': False},
        {'model_1': 'Unity 880F', 'model_2': 'Unity 870',
         'op': operator.ge, 'expected': False},
        {'model_1': 'Unity 380', 'model_2': 'Unity 370',
         'op': operator.ge, 'expected': True},
        {'model_1': 'Unity 880F', 'model_2': 'Unity 870F',
         'op': operator.lt, 'expected': False},
        {'model_1': 'Unity 880F', 'model_2': 'Unity 880F',
         'op': operator.lt, 'expected': False},
        {'model_1': 'Unity 880F', 'model_2': 'Unity 890F',
         'op': operator.lt, 'expected': True},
        {'model_1': 'Unity 880F', 'model_2': 'Unity 770F',
         'op': operator.lt, 'expected': False},
        {'model_1': 'Unity 880F', 'model_2': 'Unity 870',
         'op': operator.lt, 'expected': False},
        {'model_1': 'Unity 380', 'model_2': 'Unity 370',
         'op': operator.lt, 'expected': False},
        {'model_1': 'Unity 880F', 'model_2': 'Unity 870F',
         'op': operator.le, 'expected': False},
        {'model_1': 'Unity 880F', 'model_2': 'Unity 880F',
         'op': operator.le, 'expected': True},
        {'model_1': 'Unity 880F', 'model_2': 'Unity 890F',
         'op': operator.le, 'expected': True},
        {'model_1': 'Unity 880F', 'model_2': 'Unity 770F',
         'op': operator.le, 'expected': False},
        {'model_1': 'Unity 880F', 'model_2': 'Unity 870',
         'op': operator.le, 'expected': False},
        {'model_1': 'Unity 380', 'model_2': 'Unity 370',
         'op': operator.le, 'expected': False},
    )
    @ddt.unpack
    def test_model_compare(self, model_1, model_2, op, expected):
        unity_model_1 = UnityModel(model_1)
        unity_model_2 = UnityModel(model_2)
        assert_that(op(unity_model_1, unity_model_2), equal_to(expected))
