# coding=utf-8
# Copyright (c) 2019 Dell Inc. or its subsidiaries.
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

import logging

from storops.unity.resource import UnityResource, UnityResourceList

LOG = logging.getLogger(__name__)


class UnityAlertConfigSNMPTarget(UnityResource):

    @classmethod
    def create(cls, cli, target_address, auth_protocol=None, username=None,
               auth_password=None, priv_protocol=None, priv_password=None,
               snmp_version=None, community=None):
        req_body = cli.make_body(targetAddress=target_address,
                                 authProtocol=auth_protocol,
                                 authPassword=auth_password,
                                 privProtocol=priv_protocol,
                                 privPassword=priv_password,
                                 version=snmp_version,
                                 community=community,
                                 username=username)
        resp = cli.post(cls().resource_class, **req_body)
        resp.raise_if_err()
        return cls.get(cli, resp.resource_id)

    def modify(self, target_address=None, auth_protocol=None, username=None,
               auth_password=None, priv_protocol=None, priv_password=None,
               community=None):
        req_body = self._cli.make_body(targetAddress=target_address,
                                       authProtocol=auth_protocol,
                                       authPassword=auth_password,
                                       privProtocol=priv_protocol,
                                       privPassword=priv_password,
                                       community=community,
                                       username=username)
        resp = self.action('modify', **req_body)
        resp.raise_if_err()
        return resp

    def delete(self):
        resp = self._cli.delete(self.resource_class,
                                self.get_id())
        resp.raise_if_err()
        return resp


class UnityAlertConfigSNMPTargetList(UnityResourceList):
    @classmethod
    def get_resource_class(cls):
        return UnityAlertConfigSNMPTarget
