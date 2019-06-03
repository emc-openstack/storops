# Copyright (c) 2018 Dell Inc. or its subsidiaries.
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

from hamcrest import assert_that, equal_to, instance_of

from storops.unity.enums import SNMPPrivacyProtocolEnum, SNMPAuthProtocolEnum
from storops.unity.resource.alert_config_snmp import UnityAlertConfigSNMPTarget
from storops_test.unity.rest_mock import t_rest, patch_rest

__author__ = 'Dong Ding'


class UnityAlertConfigSNMPTargetTest(TestCase):
    @patch_rest
    def test_create_alert_snmp_v3_config(self):
        alert_snmp_config = UnityAlertConfigSNMPTarget.create(
            cli=t_rest(),
            target_address='10.10.10.111',
            username='test_username',
            auth_protocol=SNMPAuthProtocolEnum.MD5,
            priv_protocol=SNMPPrivacyProtocolEnum.AES,
            auth_password='auth_password_test')
        assert_that(alert_snmp_config, instance_of(
            UnityAlertConfigSNMPTarget))
        assert_that(alert_snmp_config.get_id(), equal_to(
            'snmp_target_8'))
        assert_that(alert_snmp_config.address, equal_to(
            '10.10.10.111'))

    @patch_rest
    def test_create_alert_snmp_v2_config(self):
        alert_snmp_config = UnityAlertConfigSNMPTarget.create(
            cli=t_rest(), target_address='10.10.10.222',
            community='test_community')
        assert_that(alert_snmp_config, instance_of(
            UnityAlertConfigSNMPTarget))
        assert_that(alert_snmp_config.get_id(), equal_to(
            'snmp_target_9'))

    @patch_rest
    def test_modify_alert_snmp_config(self):
        alert_snmp_config = UnityAlertConfigSNMPTarget.create(
            cli=t_rest(), target_address='10.10.10.111',
            username='test_username_2')
        resp = alert_snmp_config.modify(username='test_username_modified_2')
        assert_that(resp.is_ok(), equal_to(True))

    @patch_rest
    def test_delete_alert_snmp_config(self):
        alert_snmp_config = UnityAlertConfigSNMPTarget.create(
            cli=t_rest(), target_address='10.10.10.111',
            username='test_username_2')
        resp = alert_snmp_config.delete()
        assert_that(resp.body, equal_to({}))
