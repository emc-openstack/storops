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

from hamcrest import assert_that, instance_of, raises, none
from hamcrest import equal_to

from storops.exception import VNXMirrorLunNotAvailableError, \
    VNXMirrorNameInUseError, VNXMirrorAlreadyMirroredError, \
    VNXMirrorImageNotFoundError, VNXMirrorFractureImageError, \
    VNXMirrorSyncImageError, VNXMirrorPromoteNonLocalImageError, \
    VNXMirrorPromotePrimaryError, VNXMirrorFeatureNotAvailableError, \
    VNXMirrorNotFoundError, VNXDeleteMirrorWithSecondaryError, \
    VNXMirrorRemoveSynchronizingError
from test.vnx.cli_mock import patch_cli
from test.vnx.cli_mock import t_cli
from storops.vnx.enums import VNXMirrorViewRecoveryPolicy, \
    VNXMirrorViewSyncRate, VNXSPEnum, VNXMirrorImageState
from storops.vnx.resource.mirror_view import VNXMirrorView, \
    VNXMirrorViewImage

__author__ = 'Cedric Zhuang'


class VNXMirrorViewTest(TestCase):
    @patch_cli
    def test_get_all(self):
        mv_list = VNXMirrorView.get(t_cli())
        assert_that(len(mv_list), equal_to(4))

    @patch_cli(output='mirror_not_installed.txt')
    def test_mirror_view_not_installed(self):
        mv_list = VNXMirrorView.get(t_cli())
        assert_that(len(mv_list), equal_to(0))

        mv = VNXMirrorView.get(t_cli(), 'mv_sync_2')
        assert_that(mv.existed, equal_to(False))

    @patch_cli
    def test_get(self):
        mv = VNXMirrorView.get(t_cli(), 'mv_sync_2')
        assert_that(mv.uid, equal_to(
            '50:06:01:60:88:60:05:FE:04:00:00:00:00:00:00:00'))
        assert_that(mv.name, equal_to('mv_sync_2'))
        assert_that(mv.description, equal_to(''))
        assert_that(mv.logical_unit_numbers, 30)
        assert_that(mv.quiesce_threshold, equal_to(60))
        assert_that(mv.recovery_policy,
                    equal_to(VNXMirrorViewRecoveryPolicy.MANUAL))
        assert_that(len(mv.images), equal_to(2))
        assert_that(mv.images[0], instance_of(VNXMirrorViewImage))
        assert_that(mv.synchronization_rate,
                    equal_to(VNXMirrorViewSyncRate.MEDIUM))
        assert_that(mv.existed, equal_to(True))
        assert_that(mv.state, equal_to('Active'))
        assert_that(mv.image_transitioning, equal_to(False))
        assert_that(mv.image_size, equal_to(2097152))
        assert_that(mv.image_count, equal_to(2))
        assert_that(mv.image_faulted, equal_to(False))
        assert_that(mv.minimum_number_of_images_required, equal_to(0))
        assert_that(mv.write_intent_log_used, equal_to(True))
        assert_that(mv.synchronizing_progress, equal_to(100))
        assert_that(mv.remote_mirror_status, equal_to('Secondary Copy'))
        assert_that(mv.faulted, equal_to(False))
        assert_that(mv.transitioning, equal_to(False))
        assert_that(mv.is_primary, equal_to(False))

    @patch_cli
    def test_image_properties(self):
        mv = VNXMirrorView.get(t_cli(), 'mv0')
        assert_that(mv.is_primary, equal_to(True))
        assert_that(mv.primary_image.is_primary, equal_to(True))
        assert_that(mv.secondary_image.is_primary, equal_to(False))

    @patch_cli
    def test_create_success(self):
        mv = VNXMirrorView.create(t_cli(), 'mv0', 245)
        assert_that(mv.name, equal_to('mv0'))

    @patch_cli
    def test_create_lun_not_available_for_mirror(self):
        def f():
            VNXMirrorView.create(t_cli(), 'mv0', 244)

        assert_that(f, raises(VNXMirrorLunNotAvailableError, 'not available'))

    @patch_cli
    def test_create_name_in_use(self):
        def f():
            VNXMirrorView.create(t_cli(), 'mv0', 246)

        assert_that(f, raises(VNXMirrorNameInUseError, 'in use'))

    @patch_cli
    def test_add_image_success(self):
        mv = VNXMirrorView.get(t_cli(), 'mv0')
        mv.add_image('192.168.1.94', 71)
        assert_that(len(mv.images), equal_to(2))

    @patch_cli
    def test_add_image_already_mirrored(self):
        def f():
            mv = VNXMirrorView.get(t_cli(), 'mv0')
            mv.add_image('192.168.1.94', 72)

        assert_that(f, raises(VNXMirrorAlreadyMirroredError, 'exists'))

    @patch_cli
    def test_get_image_found(self):
        mv = VNXMirrorView.get(t_cli(), 'mv0')
        image = mv.get_image('50:06:01:60:88:60:05:FE')
        assert_that(image.state, equal_to(VNXMirrorImageState.SYNCHRONIZED))

    @patch_cli
    def test_get_image_not_found(self):
        def f():
            mv = VNXMirrorView.get(t_cli(), 'mv0')
            mv.get_image('50:06:01:60:88:60:05:FF')

        assert_that(f, raises(VNXMirrorImageNotFoundError, 'not found'))

    @patch_cli
    def test_remove_image_not_found(self):
        def f():
            mv = VNXMirrorView.get(t_cli(), 'mv0')
            mv.remove_image('50:06:01:60:88:60:05:FF')

        assert_that(f, raises(VNXMirrorImageNotFoundError, 'not found'))

    @patch_cli
    def test_remove_image_success(self):
        mv = VNXMirrorView.get(t_cli(), 'mv0')
        # no error raised
        mv.remove_image()

    @patch_cli
    def test_remove_image_no_secondary_image(self):
        def f():
            mv = VNXMirrorView.get(t_cli(), 'mv1')
            mv.remove_image()

        assert_that(f,
                    raises(VNXMirrorImageNotFoundError, 'no secondary'))

    @patch_cli
    def test_fracture_primary_image(self):
        def f():
            mv = VNXMirrorView.get(t_cli(), 'mv0')
            mv.fracture_image('50:06:01:60:B6:E0:1C:F4')

        assert_that(f, raises(VNXMirrorFractureImageError, 'Cannot'))

    @patch_cli
    def test_fracture_image_success(self):
        mv = VNXMirrorView.get(t_cli(), 'mv0')
        # no error raised
        mv.fracture_image()

    @patch_cli
    def test_fracture_image_not_found(self):
        def f():
            mv = VNXMirrorView.get(t_cli(), 'mv0')
            mv.fracture_image('50:06:01:60:88:60:05:FF')

        assert_that(f, raises(VNXMirrorImageNotFoundError))

    @patch_cli
    def test_sync_image_not_found(self):
        def f():
            mv = VNXMirrorView.get(t_cli(), 'mv0')
            mv.sync_image('50:06:01:60:88:60:05:FF')

        assert_that(f, raises(VNXMirrorImageNotFoundError))

    @patch_cli
    def test_sync_image_failed(self):
        def f():
            mv = VNXMirrorView.get(t_cli(), 'mv0')
            mv.sync_image()

        assert_that(f, raises(VNXMirrorSyncImageError, 'failed'))

    @patch_cli
    def test_promote_image_not_found(self):
        def f():
            mv = VNXMirrorView.get(t_cli(), 'mv0')
            mv.promote_image('50:06:01:60:88:60:05:FF')

        assert_that(f, raises(VNXMirrorImageNotFoundError))

    @patch_cli
    def test_promote_non_local_image(self):
        def f():
            mv = VNXMirrorView.get(t_cli(), 'mv0')
            mv.promote_image()

        assert_that(f, raises(VNXMirrorPromoteNonLocalImageError,
                              'not local'))

    @patch_cli
    def test_promote_already_promoted(self):
        def f():
            mv = VNXMirrorView.get(t_cli(), 'mv0')
            mv.promote_image('50:06:01:60:88:60:05:F0')

        assert_that(f, raises(VNXMirrorPromotePrimaryError, 'primary image'))

    @patch_cli
    def test_mirror_view_feature_not_installed(self):
        def f():
            mv = VNXMirrorView.get(t_cli(), 'mv9')
            mv.delete()

        assert_that(f, raises(VNXMirrorFeatureNotAvailableError,
                              'not installed'))

    @patch_cli
    def test_delete_mirror_not_found_error(self):
        def f():
            mv = VNXMirrorView.get(t_cli(), 'mv8')
            mv.delete()

        assert_that(f, raises(VNXMirrorNotFoundError, 'not found'))

    @patch_cli
    def test_delete_mirror_has_secondary(self):
        def f():
            mv = VNXMirrorView.get(t_cli(), 'mv7')
            mv.delete()

        assert_that(f, raises(VNXDeleteMirrorWithSecondaryError,
                              'at least one secondary'))

    @patch_cli
    def test_remove_mirror_image_is_synchronizing(self):
        def f():
            mv = VNXMirrorView.get(t_cli(), 'mv2')
            mv.remove_image()

        assert_that(f, raises(VNXMirrorRemoveSynchronizingError,
                              'is being synchronized'))

    @patch_cli
    def test_force_delete_mirror_has_secondary(self):
        mv = VNXMirrorView.get(t_cli(), 'mv0')
        # no error raised
        mv.delete(force=True)


class VNXMirrorViewImageTest(TestCase):
    @patch_cli
    def test_properties(self):
        mv = VNXMirrorView.get(t_cli(), 'mv_sync_2')
        image = mv.get_image('50:06:01:60:88:60:05:FE')
        assert_that(image.uid, equal_to('50:06:01:60:88:60:05:FE'))
        assert_that(image.existed, equal_to(True))
        assert_that(image.is_primary, equal_to(True))
        assert_that(image.logical_unit_uid, equal_to(
            '60:06:01:60:41:C4:3D:00:6E:1C:50:9D:05:95:E5:11'))
        assert_that(image.condition, equal_to('Primary Image'))
        assert_that(image.state, none())
        assert_that(image.preferred_sp, equal_to(VNXSPEnum.SP_A))
