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
from hamcrest import assert_that, equal_to

__author__ = 'Cedric Zhuang'

vnx = t_vnx()


def _create_cg_with_member(vnx_gf):
    """ Helper function to create a cg with a lun

    :param vnx_gf: the vnx general test fixture
    :return: created cg
    """
    lun_name = vnx_gf.add_lun_name()
    lun = vnx_gf.pool.create_lun(lun_name)

    cg_name = vnx_gf.add_cg_name()
    cg = vnx_gf.vnx.create_cg(cg_name)
    cg.add_member(lun)
    return cg


def test_cg_create_success(vnx_gf):
    assert_that(vnx_gf.cg.existed, equal_to(True))


def test_add_delete_cg_member(vnx_gf):
    lun_name = vnx_gf.add_lun_name()
    lun = vnx_gf.pool.create_lun(lun_name)

    # add member
    vnx_gf.cg.add_member(lun)
    vnx_gf.cg.update()
    assert_that(vnx_gf.cg.has_member(lun), equal_to(True))

    # delete member
    vnx_gf.cg.delete_member(lun)
    vnx_gf.cg.update()
    assert_that(vnx_gf.cg.has_member(lun), equal_to(False))


def test_update_cg_member(vnx_gf):
    lun_name = vnx_gf.add_lun_name()
    lun = vnx_gf.pool.create_lun(lun_name)

    # update member
    cg = _create_cg_with_member(vnx_gf)
    assert_that(cg.has_member(lun), equal_to(False))

    cg.replace_member(lun)
    cg.update()
    assert_that(cg.has_member(lun), equal_to(True))


@pytest.mark.skipif(not vnx.is_snap_enabled(),
                    reason='snap feature not available')
def test_create_delete_cg_snapshot(vnx_gf):
    cg = _create_cg_with_member(vnx_gf)

    # create snap
    name = vnx_gf.add_snap_name()
    snap = cg.create_snap(name)
    assert_that(snap.name, equal_to(name))
    assert_that(snap.existed, equal_to(True))

    # delete snap
    snap.delete()
    snap.update()
    assert_that(snap.existed, equal_to(False))


def test_delete_cg_success(vnx_gf):
    name = vnx_gf.add_cg_name()
    cg = vnx_gf.vnx.create_cg(name)
    assert_that(cg.existed, equal_to(True))

    cg.delete()
    cg.update()
    assert_that(cg.existed, equal_to(False))
