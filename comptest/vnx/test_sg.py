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

from hamcrest import assert_that, equal_to, has_item

__author__ = 'Cedric Zhuang'


def test_sg_create_success(vnx_gf):
    assert_that(vnx_gf.sg.existed, equal_to(True))


def test_sg_attach_detach_lun(vnx_gf):
    sg = vnx_gf.sg
    lun = vnx_gf.lun

    sg.attach_alu(lun)
    # check cache
    assert_that(sg.get_hlu(lun), equal_to(1))

    sg.update()
    # check cli parsing
    assert_that(sg.get_hlu(lun), equal_to(1))

    sg.detach_alu(lun)
    # check cache
    assert_that(sg.has_alu(lun), equal_to(False))

    sg.update()
    # check cli parsing
    assert_that(sg.has_alu(lun), equal_to(False))


def test_set_delete_path(vnx_gf):
    sp, port_id = vnx_gf.select_port()
    uid = 'iqn.1992-04.com.abc:a.b.c'

    port = vnx_gf.vnx.get_iscsi_port(sp, port_id)[0]
    port = port.config_ip('7.7.7.7', '255.255.255.0', '7.7.7.1', 3, 3)

    vnx_gf.until_existed(port)

    sg = vnx_gf.vnx.create_sg(vnx_gf.add_sg_name())
    sg.set_path(port, uid, 'host0')

    sg.update()
    assert_that(sg.hba_sp_pairs.host_name, has_item('host0'))

    sg.delete(disconnect_host=True)
    vnx_gf.vnx.delete_hba(uid)
    port.delete_ip()
