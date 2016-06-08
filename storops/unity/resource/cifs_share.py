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

import logging

from pywbemReq import CIMInstance, CIMInstanceName, Uint16, CIMError

import storops.unity.resource.cifs_server
import storops.unity.resource.filesystem
import storops.unity.resource.snap
from storops.exception import UnityCreateCifsUserError, \
    UnityImportCifsUserError, UnityAddCifsAceError, \
    UnityDeleteCifsAceError, UnityAceNotFoundError, \
    UnityCimResourceNotFoundError, UnityCreateSnapError
from storops.lib.common import instance_cache
from storops.unity.enums import CIFSTypeEnum, ACEAccessTypeEnum, \
    ACEAccessLevelEnum, FilesystemSnapAccessTypeEnum
from storops.unity.resource import UnityResource, UnityResourceList, \
    UnityAttributeResource

__author__ = 'Jay Xu'

log = logging.getLogger(__name__)


class UnityCifsShare(UnityResource):
    @classmethod
    def create(cls, cli, name, fs, path=None, cifs_server=None):
        fs_clz = storops.unity.resource.filesystem.UnityFileSystem
        fs = fs_clz.get(cli, fs).verify()
        sr = fs.storage_resource

        if path is None:
            path = '/'

        if cifs_server is None:
            cifs_server = fs.first_available_cifs_server
        else:
            server_clz = storops.unity.resource.cifs_server.UnityCifsServer
            cifs_server = server_clz.get(cli, cifs_server)

        param = cli.make_body(name=name,
                              path=path,
                              cifsServer=cifs_server)
        resp = sr.modify_fs(cifsShareCreate=[param])
        resp.raise_if_err()
        return UnityCifsShareList(cli=cli, name=name).first_item

    @classmethod
    def create_from_snap(cls, cli, snap, name, path=None, is_read_only=None):
        snap_clz = storops.unity.resource.snap.UnitySnap
        snap = snap_clz.get(cli, snap)

        if path is None:
            path = '/'

        resp = cli.post(cls().resource_class,
                        snap=snap,
                        path=path,
                        name=name,
                        isReadOnly=is_read_only)
        resp.raise_if_err()
        return cls(_id=resp.resource_id, cli=cli)

    @property
    @instance_cache
    def storage_resource(self):
        fs = self.filesystem
        if fs is not None:
            ret = fs.storage_resource
        else:
            ret = None
        return ret

    def delete(self, async=False):
        if self.type == CIFSTypeEnum.CIFS_SNAPSHOT:
            resp = super(UnityCifsShare, self).delete(async=async)
        else:
            fs = self.filesystem.verify()
            sr = fs.storage_resource
            param = self._cli.make_body(cifsShare=self)
            resp = sr.modify_fs(async=async, cifsShareDelete=[param])
        resp.raise_if_err()
        return resp

    def get_ace_list(self):
        obj_list = self._cli.ref(self.cim.path, 'CIM_AssociatedPrivilege')
        ret = {
            ACEAccessLevelEnum.FULL: [],
            ACEAccessLevelEnum.READ: [],
            ACEAccessLevelEnum.WRITE: [],
        }
        for obj in obj_list:
            try:
                sid = obj['subject']['instanceId']
                access = ACEAccessLevelEnum.from_list(obj['activities'])
                ret[access].append(sid)
            except (AttributeError, IndexError, ValueError):
                # skip, next one
                pass
        return ret

    def get_ace_list_rest(self):
        resp = self.action('getACEs')
        resp.raise_if_err()

    def enable_ace(self):
        return self.modify(is_ace_enabled=True)

    def disable_ace(self):
        return self.modify(is_ace_enabled=False)

    def add_ace(self, domain=None, user=None, access_level=None):
        name = self._get_domain_user_name(domain, user)
        if access_level is None:
            access_level = ACEAccessLevelEnum.FULL
        ACEAccessLevelEnum.verify(access_level)

        activity = Uint16(access_level.to_smis_activity_value())
        identity = self.get_identity_instance_name(name)

        resp = self._cli.im(
            'AssignPrivilegeToExportedShare',
            self.cim_export_service.path,
            Identities=[identity],
            Activities=[activity],
            FileShare=self.cim_instance_name)
        resp.raise_if_err(default=UnityAddCifsAceError)
        return resp

    def _get_domain_user_name(self, domain=None, user=None):
        if domain is None:
            domain = self.cifs_server.domain
        if user is None:
            raise ValueError('username not specified.')
        return r'{}\{}'.format(domain, user)

    def delete_ace(self, domain=None, user=None, sid=None):
        if sid is None:
            name = self._get_domain_user_name(domain, user)
            sid = self.get_user_sids(self._cli, name)
        obj_list = self._cli.ref(self.cim.path, 'CIM_AssociatedPrivilege')
        for obj in obj_list:
            try:
                if sid == obj['subject']['instanceId'].strip():
                    ret = self._cli.di(obj.path)
                    ret.raise_if_err(default=UnityDeleteCifsAceError)
                    break
            except (ValueError, AttributeError, IndexError):
                pass
        else:
            raise UnityAceNotFoundError()
        return ret

    def clear_access(self):
        """ clear all ace entries of the share

        :return: sid list of ace entries removed successfully
        """
        access_entries = self.get_ace_list()
        ret = []
        for sid_list in access_entries.values():
            for sid in sid_list:
                try:
                    resp = self.delete_ace(sid=sid)
                    if resp.is_ok():
                        ret.append(sid)
                except UnityAceNotFoundError:
                    log.info('sid {} not found in access entries.'.format(sid))
        return ret

    def add_ace_rest(self, domain, user, access_level=None):
        if access_level is None:
            access_level = ACEAccessLevelEnum.FULL
        sid = UnityAclUser.get_sid(self._cli, user=user, domain=domain)
        ace = self._cli.make_body(
            sid=sid,
            accessType=ACEAccessTypeEnum.GRANT,
            accessLevel=access_level
        )

        resp = self.modify(add_ace=[ace])
        resp.raise_if_err()
        return resp

    def modify(self, is_read_only=None, is_ace_enabled=None, add_ace=None,
               delete_ace=None):
        sr = self.storage_resource
        if sr is None:
            raise ValueError('storage resource for share {} not found.'
                             .format(self.name))

        share_param = self._cli.make_body(
            allow_empty=True,
            isReadOnly=is_read_only,
            isACEEnabled=is_ace_enabled,
            addACE=add_ace,
            deleteAce=delete_ace)
        modify_param = self._cli.make_body(
            allow_empty=True,
            cifsShare=self,
            cifsShareParameters=share_param)
        param = self._cli.make_body(
            allow_empty=True,
            cifsShareModify=[modify_param])

        resp = sr.modify_fs(**param)
        resp.raise_if_err()
        return resp

    @property
    @instance_cache
    def cim(self):
        return self._cli.gi(self.cim_instance_name)

    @property
    def cim_instance_name(self):
        return CIMInstanceName('EMC_VNXe_CIFSShareLeaf',
                               {'InstanceID': self.get_id()},
                               namespace='root/emc/smis')

    def get_identity_instance_name(self, name):
        sid = self.get_user_sids(self._cli, name)
        return CIMInstanceName('EMC_VNXe_IdentityLeaf',
                               {'InstanceID': sid})

    @classmethod
    def create_user(cls, cli, name):
        contact_clz_name = 'CIM_UserContact'
        user = CIMInstance(contact_clz_name,
                           {
                               'Name': name,
                               'CreationClassName': contact_clz_name
                           })
        ret = cli.im('CreateUserContact',
                     cli.account_management_service.path,
                     System=cli.system.path,
                     UserContactTemplate=user)
        ret.raise_if_err(default=UnityCreateCifsUserError)
        try:
            ret = ret.value['Identities'][0]['InstanceID'].strip()
        except (AttributeError, IndexError, ValueError):
            raise UnityImportCifsUserError()
        return ret

    @property
    @instance_cache
    def cim_export_service(self):
        inst_name = self.cim_instance_name
        instances = self._cli.ai(inst_name, 'CIM_ServiceAffectsElement',
                                 'CIM_FileExportService')
        if instances:
            ret = instances[0]
        else:
            raise UnityCimResourceNotFoundError(
                'FileExportService not found for cifs share: {}'.format(
                    self.get_id()))
        return ret

    @classmethod
    def get_user_sids(cls, cli, name=None):
        if name is None:
            ret = [user['userID'].strip() for user in cls.get_user(cli, name)]
        else:
            ret = cls.get_user(cli, name)
            if ret is None:
                ret = cls.create_user(cli, name)
            else:
                ret = ret['userID'].strip()
        return ret

    @classmethod
    def get_user(cls, cli, name=None):
        if name is not None:
            try:
                ret = cli.gi(cls.get_user_instance_name(name))
            except CIMError:
                ret = None
        else:
            ret = cli.ei('EMC_VNXe_UserContactLeaf')
        return ret

    @classmethod
    def get_user_instance_name(cls, name):
        clz_name = 'EMC_VNXe_UserContactLeaf'
        return CIMInstanceName(
            clz_name,
            {'CreationClassName': clz_name,
             'Name': name},
            namespace='root/emc/smis')

    @property
    @instance_cache
    def cifs_server(self):
        ret = None
        fs = self.filesystem
        if fs:
            nas_server = fs.nas_server
            if nas_server:
                cifs_servers = nas_server.cifs_server
                if cifs_servers:
                    ret = cifs_servers[0]
        return ret

    def create_snap(self, name=None, fs_access_type=None):
        if fs_access_type is None:
            fs_access_type = FilesystemSnapAccessTypeEnum.PROTOCOL

        if self.type == CIFSTypeEnum.CIFS_SHARE:
            ret = self.filesystem.create_snap(
                name=name, fs_access_type=fs_access_type)
        elif self.type == CIFSTypeEnum.CIFS_SNAPSHOT:
            ret = self.snap.copy(copy_name=name)
        else:
            raise UnityCreateSnapError('do not know how to create snap for '
                                       'cifs share {}, type {}.'
                                       .format(self.name, self.type))
        return ret


class UnityCifsShareList(UnityResourceList):
    @classmethod
    def get_resource_class(cls):
        return UnityCifsShare


class UnityCifsShareAce(UnityAttributeResource):
    pass


class UnityCifsShareAceList(UnityResourceList):
    def sid_list(self):
        return [ace.sid for ace in self]

    @classmethod
    def get_resource_class(cls):
        return UnityCifsShareAce


class UnityAclUser(UnityResource):
    @classmethod
    def get_sid(cls, cli, user, domain):
        resp = cli.type_action(cls().resource_class,
                               'lookupSIDByDomainUser',
                               domainName=domain,
                               userName=user)
        resp.raise_if_err()
        return resp.first_content.get('sid')


class UnityAclUserList(UnityResourceList):
    @classmethod
    def get_resource_class(cls):
        return UnityAclUser
