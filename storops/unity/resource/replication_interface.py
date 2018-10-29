# Copyright (c) 2018 Dell Inc. or its subsidiaries.
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

__author__ = 'Ryan Liang'

log = logging.getLogger(__name__)


class UnityReplicationInterface(UnityResource):
    @classmethod
    def create(cls, cli, sp, ip_port, ip_address, netmask=None,
               v6_prefix_length=None, gateway=None, vlan_id=None):
        """
        Creates a replication interface.

        :param cls: this class.
        :param cli: the rest cli.
        :param sp: `UnityStorageProcessor` object. Storage processor on which
            the replication interface is running.
        :param ip_port: `UnityIpPort` object. Physical port or link aggregation
            on the storage processor on which the interface is running.
        :param ip_address: IP address of the replication interface.
        :param netmask: IPv4 netmask for the replication interface, if it uses
            an IPv4 address.
        :param v6_prefix_length: IPv6 prefix length for the interface, if it
            uses an IPv6 address.
        :param gateway: IPv4 or IPv6 gateway address for the replication
            interface.
        :param vlan_id: VLAN identifier for the interface.
        :return: the newly create replication interface.
        """
        req_body = cli.make_body(sp=sp, ipPort=ip_port,
                                 ipAddress=ip_address, netmask=netmask,
                                 v6PrefixLength=v6_prefix_length,
                                 gateway=gateway, vlanId=vlan_id)

        resp = cli.post(cls().resource_class, **req_body)
        resp.raise_if_err()
        return cls.get(cli, resp.resource_id)

    def modify(self, sp=None, ip_port=None, ip_address=None, netmask=None,
               v6_prefix_length=None, gateway=None, vlan_id=None):
        """
        Modifies a replication interface.

        :param sp: same as the one in `create` method.
        :param ip_port: same as the one in `create` method.
        :param ip_address: same as the one in `create` method.
        :param netmask: same as the one in `create` method.
        :param v6_prefix_length: same as the one in `create` method.
        :param gateway: same as the one in `create` method.
        :param vlan_id: same as the one in `create` method.
        """
        req_body = self._cli.make_body(sp=sp, ipPort=ip_port,
                                       ipAddress=ip_address, netmask=netmask,
                                       v6PrefixLength=v6_prefix_length,
                                       gateway=gateway, vlanId=vlan_id)

        resp = self.action('modify', **req_body)
        resp.raise_if_err()
        return resp


class UnityReplicationInterfaceList(UnityResourceList):
    @classmethod
    def get_resource_class(cls):
        return UnityReplicationInterface
