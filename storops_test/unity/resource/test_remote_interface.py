# Copyright (c) 2018 Dell Inc. or its subsidiaries.
# All Rights Reserved.
#
#    Licensed under the Apache License, Veriion 2.0 (the "License"); you may
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
import unittest

import hamcrest as hc

import storops
from storops.unity.resource import remote_interface, remote_system
from storops_test.unity import rest_mock as mock

__author__ = 'Ryan Liang'


class UnityRemoteInterfaceTest(unittest.TestCase):
    @mock.patch_rest
    def test_get_properties(self):
        ri = remote_interface.UnityRemoteInterface.get(
            cli=mock.t_rest(), _id='FNM00150600267:if_10')
        hc.assert_that(ri.address, hc.equal_to('10.245.47.99'))
        hc.assert_that(ri.capability,
                       hc.equal_to(storops.ReplicationCapabilityEnum.ASYNC))
        hc.assert_that(ri.id, hc.equal_to('FNM00150600267:if_10'))
        hc.assert_that(ri.name, hc.equal_to('4_FNM00150600267'))
        hc.assert_that(ri.node, hc.equal_to(storops.NodeEnum.SPA))
        hc.assert_that(ri.remote_id, hc.equal_to('if_10'))
        hc.assert_that(ri.remote_system,
                       hc.instance_of(remote_system.UnityRemoteSystem))
        hc.assert_that(ri.remote_system.id, hc.equal_to('RS_0'))

    @mock.patch_rest
    def test_get_collection(self):
        ri_list = remote_interface.UnityRemoteInterfaceList.get(mock.t_rest())
        hc.assert_that(len(ri_list), hc.equal_to(8))
        hc.assert_that([ri.id for ri in ri_list],
                       hc.equal_to(['FNM00150600267:if_10',
                                    'FNM00150600267:if_11',
                                    'FNM00150600267:system_if_0',
                                    'FNM00150600267:system_if_1',
                                    'FNM00150600267:system_if_2',
                                    'FNM00150600267:system_if_3',
                                    'FNM00152000052:if_6',
                                    'FNM00152000052:if_7']))
