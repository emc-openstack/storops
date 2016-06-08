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
from hamcrest import assert_that, equal_to, raises
from retryz import retry

from comptest import t_vnx
from storops.exception import VNXLunExtendError, VNXDedupAlreadyEnabled, \
    VNXLunPreparingError, VNXNotReadyExpandError
from storops.vnx.enums import VNXProvisionEnum, VNXTieringEnum

__author__ = 'Cedric Zhuang'

vnx = t_vnx()


def test_create_thick_lun(vnx_gf):
    assert_that(vnx_gf.lun.existed, equal_to(True))
    assert_that(vnx_gf.lun.provision, equal_to(VNXProvisionEnum.THICK))
    assert_that(vnx_gf.lun.tier, equal_to(VNXTieringEnum.HIGH_AUTO))


@pytest.mark.skipif(not vnx.is_auto_tiering_enabled(),
                    reason='auto tiering not available')
def test_create_typed_lun(vnx_gf):
    lun = _create_test_lun(vnx_gf, tier=VNXTieringEnum.NO_MOVE)
    assert_that(lun.existed, equal_to(True))
    assert_that(lun.provision, equal_to(VNXProvisionEnum.THIN))
    assert_that(lun.tier, equal_to(VNXTieringEnum.NO_MOVE))


@pytest.mark.skipif(not vnx.is_compression_enabled(),
                    reason='compression not available')
def test_create_compression_lun(vnx_gf):
    lun = _create_test_lun(vnx_gf, provision=VNXProvisionEnum.COMPRESSED)
    assert_that(lun.existed, equal_to(True))
    assert_that(lun.provision, equal_to(VNXProvisionEnum.COMPRESSED))


@pytest.mark.skipif(not vnx.is_compression_enabled(),
                    reason='compression not available')
def test_enable_disable_compression(vnx_gf):
    lun = _create_test_lun(vnx_gf)
    assert_that(lun.existed, equal_to(True))

    # enable compression
    lun.enable_compression()
    lun.update()
    assert_that(lun.provision, equal_to(VNXProvisionEnum.COMPRESSED))

    # disable compression
    lun.disable_compression()
    lun.update()
    assert_that(lun.provision, equal_to(VNXProvisionEnum.THIN))


@pytest.mark.skipif(not vnx.is_dedup_enabled(),
                    reason='dedup feature not available')
def test_create_dedup_lun(vnx_gf):
    lun = _create_test_lun(vnx_gf, provision=VNXProvisionEnum.DEDUPED)
    assert_that(lun.existed, equal_to(True))

    def f():
        lun.enable_dedup()

    assert_that(f, raises(VNXDedupAlreadyEnabled))


@pytest.mark.skipif(not vnx.is_snap_enabled(),
                    reason='snap feature not available')
def test_create_smp(vnx_gf):
    smp_name = vnx_gf.add_lun_name()
    smp = vnx_gf.lun.create_mount_point(name=smp_name)
    assert_that(smp.existed, equal_to(True))
    assert_that(smp.primary_lun.name, equal_to(vnx_gf.lun.name))


def _extend_retry_err(ex):
    return isinstance(ex, (VNXLunPreparingError, VNXNotReadyExpandError))


def test_extend_lun(vnx_gf):
    @retry(on_error=_extend_retry_err, wait=7)
    def do_expand():
        lun.expand(2)

    lun = _create_test_lun(vnx_gf)
    assert_that(lun.user_capacity_gbs, equal_to(1.0))
    do_expand()

    def f():
        lun.expand(1)

    assert_that(f, raises(VNXLunExtendError))


@pytest.mark.skipif(not vnx.is_auto_tiering_enabled(),
                    reason='auto tiering feature not available')
def test_update_tiering_value(vnx_gf):
    lun = vnx_gf.lun
    lun.tier = VNXTieringEnum.NO_MOVE
    lun.update()
    assert_that(lun.tier, equal_to(VNXTieringEnum.NO_MOVE))


def test_migration_success(vnx_gf):
    src = _create_test_lun(vnx_gf)
    tgt = _create_test_lun(vnx_gf)

    vnx_gf.until(src, lambda x: x.state == 'Ready')
    vnx_gf.until(tgt, lambda x: x.state == 'Ready')

    src.migrate(tgt)
    ms = vnx_gf.vnx.get_migration_session(src_lun=src)
    vnx_gf.until_not_existed(ms)

    tgt.update()
    assert_that(tgt.existed, equal_to(False))
    src.update()
    assert_that(src.existed, equal_to(True))


def _create_test_lun(vnx_gf, provision=None, tier=None):
    if provision is None:
        provision = VNXProvisionEnum.THIN
    lun_name = vnx_gf.add_lun_name()
    lun = vnx_gf.pool.create_lun(lun_name, provision=provision, tier=tier)
    return lun
