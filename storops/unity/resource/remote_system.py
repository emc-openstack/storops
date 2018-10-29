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


class UnityRemoteSystem(UnityResource):

    @classmethod
    def create(cls, cli, management_address,
               local_username=None, local_password=None,
               remote_username=None, remote_password=None,
               connection_type=None):
        """
        Configures a remote system for remote replication.

        :param cls: this class.
        :param cli: the rest client.
        :param management_address: the management IP address of the remote
            system.
        :param local_username: administrative username of local system.
        :param local_password: administrative password of local system.
        :param remote_username: administrative username of remote system.
        :param remote_password: administrative password of remote system.
        :param connection_type: `ReplicationCapabilityEnum`. Replication
            connection type to the remote system.
        :return: the newly created remote system.
        """

        req_body = cli.make_body(
            managementAddress=management_address, localUsername=local_username,
            localPassword=local_password, remoteUsername=remote_username,
            remotePassword=remote_password, connectionType=connection_type)

        resp = cli.post(cls().resource_class, **req_body)
        resp.raise_if_err()
        return cls.get(cli, resp.resource_id)

    def modify(self, management_address=None, username=None, password=None,
               connection_type=None):
        """
        Modifies a remote system for remote replication.

        :param management_address: same as the one in `create` method.
        :param username: username for accessing the remote system.
        :param password: password for accessing the remote system.
        :param connection_type: same as the one in `create` method.
        """
        req_body = self._cli.make_body(
            managementAddress=management_address, username=username,
            password=password, connectionType=connection_type)

        resp = self.action('modify', **req_body)
        resp.raise_if_err()
        return resp

    def verify(self, connection_type=None):
        """
        Verifies and update the remote system settings.

        :param connection_type: same as the one in `create` method.
        """
        req_body = self._cli.make_body(connectionType=connection_type)

        resp = self.action('verify', **req_body)
        resp.raise_if_err()
        return resp


class UnityRemoteSystemList(UnityResourceList):
    @classmethod
    def get_resource_class(cls):
        return UnityRemoteSystem
