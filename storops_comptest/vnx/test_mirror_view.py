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
from hamcrest import equal_to, assert_that, raises, contains_string

from storops import cache
from storops.exception import VNXMirrorSyncImageError, \
    VNXMirrorPromotePrimaryError

from storops_comptest import vnx1, vnx2

__author__ = 'Cedric Zhuang'


@cache
def is_mirror_available():
    return (vnx1().is_mirror_view_sync_enabled() and
            vnx2().is_mirror_view_sync_enabled())


@pytest.mark.skipif(not is_mirror_available(),
                    reason='mirror view sync is not available.')
def test_create_mirror_view(multi_vnx_gf):
    mirror = multi_vnx_gf.mirror
    assert_that(mirror.existed, equal_to(True))


@pytest.mark.skipif(not is_mirror_available(),
                    reason='mirror view sync is not available.')
def test_add_image(multi_vnx_gf):
    mirror = multi_vnx_gf.mirror
    assert_that(len(mirror.images), equal_to(2))


@pytest.mark.skipif(not is_mirror_available(),
                    reason='mirror view sync is not available.')
def test_fracture_and_sync_image(multi_vnx_gf):
    mirror = multi_vnx_gf.mirror
    mirror.fracture_image(mirror.secondary_image)
    mirror.update()

    assert_that(mirror.secondary_image.condition, contains_string('fractured'))

    def sync():
        mirror.sync_image(mirror.images[0])

    sync()

    assert_that(sync, raises(VNXMirrorSyncImageError))


@pytest.mark.skipif(not is_mirror_available(),
                    reason='mirror view sync is not available.')
def test_promote_primary_image(multi_vnx_gf):
    def promote():
        mirror = multi_vnx_gf.mirror
        mirror.promote_image(mirror.primary_image)

    assert_that(promote, raises(VNXMirrorPromotePrimaryError))
