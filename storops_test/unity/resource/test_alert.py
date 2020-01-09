# Copyright (c) 2020 Dell Inc. or its subsidiaries.
# All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
from __future__ import unicode_literals

from unittest import TestCase

from hamcrest import assert_that, equal_to

from storops.unity.enums import SeverityEnum
from storops.unity.resource.alert import UnityAlert
from storops_test.unity.rest_mock import t_rest, patch_rest


class UnityAlertConfigSNMPTargetTest(TestCase):
    @patch_rest
    def test_alert_properties(self):
        alert = UnityAlert(_id='alert_180', cli=t_rest())
        assert_that(alert.id, equal_to('alert_180'))
        assert_that(alert.severity, equal_to(SeverityEnum.CRITICAL))
        assert_that(alert.instance_id, equal_to(
            'root/emc:C4CB_AlertEvent%AlertID=1577836740661/637773388'))
        assert_that(alert.timestamp, equal_to('2019-12-31T23:59:00.661Z'))
        assert_that(alert.message_id, equal_to('14:170002'))
        assert_that(alert.arguments, equal_to(['BASE_OE_V4_0']))
        assert_that(alert.catalog_id, equal_to('CEM-CatalogService'))
        assert_that(alert.message, equal_to(
            "The BASE_OE_V4_0 license has expired, and the storage system's "
            "support for the licensed feature has been disabled. Obtain and "
            "install a new license file to ensure support for the licensed "
            "feature."))
        assert_that(alert.description_id, equal_to(
            'ALRT_LICENSINGSERVICES_LICENSE_EXPIRED'))
        assert_that(alert.description, equal_to(
            "One of your system licenses has expired or will expire soon. "
            "Obtain and install the license file to ensure continued access "
            "to the relevant feature."))
        assert_that(alert.resolution_id, equal_to('licnse_update'))
        assert_that(alert.resolution, equal_to(
            '/help/webhelp/en_US/index.html?#unity_t_manage_licenses.html'))
        assert_that(alert.component_facility, equal_to('LicensingServices'))
        assert_that(alert.is_acknowledged, equal_to(False))

    @patch_rest
    def test_modify_alert(self):
        alert = UnityAlert(_id='alert_181', cli=t_rest())
        resp = alert.modify(is_acknowledged=True)
        alert.update()
        assert_that(resp.is_ok(), equal_to(True))
        assert_that(alert.is_acknowledged, equal_to(True))

    @patch_rest
    def test_delete_alert(self):
        alert = UnityAlert(_id='alert_182', cli=t_rest())
        resp = alert.delete()
        assert_that(resp.body, equal_to({}))
