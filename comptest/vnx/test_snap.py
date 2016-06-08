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

import pytest
from comptest import t_vnx
from hamcrest import assert_that, equal_to, only_contains, none

__author__ = 'Cedric Zhuang'


vnx = t_vnx()


@pytest.mark.skipif(not vnx.is_snap_enabled(),
                    reason='snap feature not available')
def test_snap_create(vnx_gf):
    assert_that(vnx_gf.snap.existed, equal_to(True))
    assert_that(vnx_gf.snap.source_luns, only_contains(vnx_gf.lun.lun_id))
    assert_that(vnx_gf.snap.primary_luns, only_contains(vnx_gf.lun.lun_id))


@pytest.mark.skipif(not vnx.is_snap_enabled(),
                    reason='snap feature not available')
def test_attach_detach_snap(vnx_gf):
    smp_name = vnx_gf.add_lun_name()
    smp = vnx_gf.lun.create_mount_point(name=smp_name)
    smp.attach_snap(vnx_gf.snap)
    smp.update()
    assert_that(smp.attached_snapshot.name, equal_to(vnx_gf.snap.name))
    smp.detach_snap()
    smp.update()
    assert_that(smp.attached_snapshot, none())


@pytest.mark.skipif(not vnx.is_snap_enabled(),
                    reason='snap feature not available')
def test_delete_snap(vnx_gf):
    snap_name = vnx_gf.add_snap_name()
    vnx_gf.lun.create_snap(snap_name)
    snap = vnx_gf.vnx.get_snap(name=snap_name)
    snap.delete()
    snap.update()
    assert_that(snap.existed, equal_to(False))
