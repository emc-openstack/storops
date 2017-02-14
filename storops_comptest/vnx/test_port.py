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

from hamcrest import assert_that, equal_to, none

__author__ = 'Cedric Zhuang'


def test_create_delete_iscsi_ip(vnx_gf):
    sp, port_id = vnx_gf.select_port()

    port = vnx_gf.vnx.get_iscsi_port(sp, port_id)[0]

    # create ip
    port1 = port.config_ip('5.5.5.5', '255.255.255.0', '5.5.5.1', 1, 1)
    vnx_gf.until_existed(port1)

    assert_that(port1.ip_address, equal_to('5.5.5.5'))
    assert_that(port1.subnet_mask, equal_to('255.255.255.0'))
    assert_that(port1.gateway_address, equal_to('5.5.5.1'))

    # delete ip
    port1.delete_ip()
    vnx_gf.until_not_existed(port1)

    port = vnx_gf.vnx.get_iscsi_port(sp, port_id)[0]
    assert_that(port.ip_address, none())
    assert_that(port.subnet_mask, none())
    assert_that(port.gateway_address, none())
