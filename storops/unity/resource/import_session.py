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

import logging

from storops.unity.resource import UnityResource, UnityResourceList, \
    UnityAttributeResource

__author__ = 'Yong Huang'

LOG = logging.getLogger(__name__)


class UnityCifsServerInfo(UnityAttributeResource):
    @staticmethod
    def to_embedded(name=None, description=None, netbios_name=None,
                    domain=None, workgroup=None, is_standalone=None,
                    cifs_username=None):
        """
        Constructs an embeded object of `UnityCifsServerInfo`.

        :param name: User-specified name for the SMB server.
        :param description: Description of the SMB server.
        :param netbios_name: Computer Name of the SMB server in Windows
            network.
        :param domain: Domain name where SMB server is registered in
            Active Directory, if applicable.
        :param workgroup: (Applies to stand-alone SMB servers.) Windows
            network workgroup for the SMB server.
        :param is_standalone: Indicates whether the SMB server is standalone.
            Values are:
                true - SMB server is standalone.
                false - SMB server is joined to the Active Directory.
        :param cifs_username: User name for authentication to CIFS server
            on the source VDM. it could be the same as Active Directory
            domain user name in some cases, and which will be used
            initialized to the Active Directory domain user name in GUI side.
        :return:
        """
        return {'name': name, 'description': description,
                'netbiosName': netbios_name, 'domain': domain,
                'workgroup': workgroup, 'isStandalone': is_standalone,
                'cifsUsername': cifs_username}


class UnityImportSyncProgress(UnityResource):
    pass


class UnityImportSyncProgressList(UnityResourceList):
    @classmethod
    def get_resource_class(cls):
        return UnityImportSyncProgress


class UnityElementImport(UnityResource):
    pass


class UnityElementImportList(UnityResourceList):
    @classmethod
    def get_resource_class(cls):
        return UnityElementImport


class UnityImportSession(UnityResource):
    @classmethod
    def create_block_import(cls, cli, remote_system, src_resource,
                            dst_resource_config,
                            dst_resource_element_configs=None,
                            import_as_vmware_datastore=None, throttle=None,
                            hosts=None, cutover_threshold=None, name=None):
        """
        Create a block import session.

        :param remote_system: Source system from which the import is being
            configured.
        :param src_resource: Unique identifier of the source resource.
        :param dst_resource_config: This is the user chosen config for
            destination resource provisioning.
        :param dst_resource_element_configs: This is the user chosen config
            for each of the member element of the destination resource.
        :param import_as_vmware_datastore: Specify if the target resource
            should be VMware Datastore. Default is 'false' and not
            application to consistency groups, only standalone luns.
        :param throttle: Throttle for session. 'True' (Default):
            Session throttled. 'False': Session not throttled.
        :param hosts: List of hosts that will be granted access to
            import session destination resources.
        :param cutover_threshold: Cutover threshold. Default value: 5
        :param name: Name of the import session.
        :return: The newly created import session.
        """

        req_body = cli.make_body(
            remoteSystem=remote_system,
            srcResource=src_resource,
            dstResourceConfig=dst_resource_config,
            dstResourceElementConfigs=dst_resource_element_configs,
            importAsVMwareDatastore=import_as_vmware_datastore,
            throttle=throttle, hosts=hosts,
            cutoverThreshold=cutover_threshold, name=name)

        resp = cli.type_action(
            cls().resource_class,
            'createBlockImport',
            **req_body)
        resp.raise_if_err()
        # response is like:
        # "content": {
        #     "id": {
        #         "id": "import_xxxx"
        #     }
        session_resp = resp.first_content['id']
        return cls.get(cli, _id=session_resp['id'])

    def modify(self, throttle=None, name=None, cutover_threshold=None,
               src_local_cifs_admin_username=None,
               src_local_cifs_admin_passwd=None):
        """
        Modify an import session.

        :param throttle: Throttle for session. 'True': Session throttled.
            'False': Session not throttled.
        :param name: Name of the import session.
        :param cutover_threshold: Cutover threshold.
        :param src_local_cifs_admin_username: User name for authentication
            to CIFS server on the source VDM. It is only used for VDM import.
        :param src_local_cifs_admin_passwd: Password for authentication
            to CIFS server on the source VDM. It is only used for VDM import.
        :return:
        """
        req_body = self._cli.make_body(
            throttle=throttle, name=name, cutoverThreshold=cutover_threshold,
            srcLocalCifsAdminUsername=src_local_cifs_admin_username,
            srcLocalCifsAdminPasswd=src_local_cifs_admin_passwd)
        resp = self.action('modify', **req_body)
        resp.raise_if_err()
        return resp

    def pause(self, test_facility_code=None):
        """
        Pause an import session.
        """
        req_body = self._cli.make_body(testFacilityCode=test_facility_code)
        resp = self.action('pause', **req_body)
        resp.raise_if_err()
        return resp

    def resume(self):
        """
        Resume an import session.
        """
        resp = self.action('resume')
        resp.raise_if_err()
        return resp

    def cutover(self, cifs_server_info=None, domain_username=None,
                domain_password=None):
        """
        Cutover an import session.

        For block import this switches the production over as well as commit
        the session. For file import this just switches the production over
        to destination site.

        :param cifs_server_info: New CIFS server object to be created at
            the source VDM.
        :param domain_username: Active Directory domain user name.
        :param domain_password: Active Directory domain password.
        :return:
        """
        req_body = self._cli.make_body(cifsServerInfo=cifs_server_info,
                                       domainUsername=domain_username,
                                       domainPassword=domain_password)
        resp = self.action('cutover', **req_body)
        resp.raise_if_err()
        return resp

    def commit(self):
        """
        Commit an import session.
        """
        resp = self.action('commit')
        resp.raise_if_err()
        return resp

    def cancel(self, domain_username=None, domain_password=None):
        """
        Cancel an import session.

        :param domain_username: Active Directory domain user name.
        :param domain_password: Active Directory domain password.
        :return:
        """
        req_body = self._cli.make_body(domainUsername=domain_username,
                                       domainPassword=domain_password)
        resp = self.action('cancel', **req_body)
        resp.raise_if_err()
        return resp


class UnityImportSessionList(UnityResourceList):
    @classmethod
    def get_resource_class(cls):
        return UnityImportSession
