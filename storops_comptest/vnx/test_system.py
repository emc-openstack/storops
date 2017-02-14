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

import logging

from hamcrest import assert_that, not_none, greater_than, equal_to

from storops_comptest import t_vnx

__author__ = 'Cedric Zhuang'

log = logging.getLogger(__name__)

vnx = t_vnx()


def test_domain():
    assert_that(vnx.spa_ip, not_none())
    assert_that(vnx.spb_ip, not_none())
    assert_that(vnx.control_station_ip, not_none())


def test_feature_list():
    feature = vnx.get_pool_feature()
    assert_that(feature.existed, equal_to(True))
    assert_that(len(feature.available_disks), greater_than(0))
