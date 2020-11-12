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

import six

import storops.unity.resource.cifs_server
import storops.unity.resource.filesystem
import storops.unity.resource.snap
from storops.exception import UnityCreateSnapError
from storops.lib.common import instance_cache
from storops.unity.client import UnityClient
from storops.unity.enums import CIFSTypeEnum, ACEAccessTypeEnum, \
    ACEAccessLevelEnum, FilesystemSnapAccessTypeEnum, \
    CifsShareOfflineAvailabilityEnum
from storops.unity.resource import UnityResource, UnityResourceList, \
    UnityAttributeResource
from storops.unity.resp import RestResponse

__author__ = 'Jay Xu'

log = logging.getLogger(__name__)


class UnityCifsShare(UnityResource):
    @classmethod
    def create(cls, cli, name, fs, path=None, cifs_server=None,
               is_read_only=None, is_encryption_enabled=None,
               is_con_avail_enabled=None, is_abe_enabled=None,
               is_branch_cache_enabled=None, offline_availability=None,
               umask=None, description=None):
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

        share_param = cls.prepare_cifs_share_parameters(
            is_read_only=is_read_only,
            is_encryption_enabled=is_encryption_enabled,
            is_con_avail_enabled=is_con_avail_enabled,
            is_abe_enabled=is_abe_enabled,
            is_branch_cache_enabled=is_branch_cache_enabled,
            offline_availability=offline_availability,
            umask=umask, description=description)

        param = cli.make_body(name=name,
                              path=path,
                              cifsServer=cifs_server,
                              cifsShareParameters=share_param)
        resp = sr.modify_fs(cifsShareCreate=[param])
        resp.raise_if_err()
        return UnityCifsShareList(
            cli=cli, name=name, filesystem=fs).first_item

    @classmethod
    def create_from_snap(cls, cli, snap, name, path=None, is_read_only=None,
                         is_abe_enabled=None, is_branch_cache_enabled=None,
                         is_con_avail_enabled=None,
                         is_encryption_enabled=None,
                         offline_availability=None,
                         umask=None, description=None):
        snap_clz = storops.unity.resource.snap.UnitySnap
        snap = snap_clz.get(cli, snap)

        if path is None:
            path = '/'

        share_param = cls.prepare_cifs_share_parameters(
            is_read_only=is_read_only,
            is_encryption_enabled=is_encryption_enabled,
            is_con_avail_enabled=is_con_avail_enabled,
            is_abe_enabled=is_abe_enabled,
            is_branch_cache_enabled=is_branch_cache_enabled,
            offline_availability=offline_availability,
            umask=umask, description=description)

        resp = cli.post(
            cls().resource_class, snap=snap, path=path, name=name,
            **share_param)
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

    def delete(self, async_mode=False):
        if self.type == CIFSTypeEnum.CIFS_SNAPSHOT:
            resp = super(UnityCifsShare, self).delete(async_mode=async_mode)
        else:
            fs = self.filesystem.verify()
            sr = fs.storage_resource
            param = self._cli.make_body(cifsShare=self)
            resp = sr.modify_fs(async_mode=async_mode, cifsShareDelete=[param])
        resp.raise_if_err()
        return resp

    def get_ace_list(self):
        return UnityCifsShareAceList(cli=self._cli, cifs_share=self)

    def enable_ace(self):
        return self.modify(is_ace_enabled=True)

    def disable_ace(self):
        return self.modify(is_ace_enabled=False)

    def _get_domain_user_name(self, domain=None, user=None):
        if domain is None:
            domain = self.cifs_server.domain
        if user is None:
            raise ValueError('username not specified.')
        return r'{}\{}'.format(domain, user)

    def clear_access(self, white_list=None):
        """ clear all ace entries of the share

        :param white_list: list of username whose access entry won't be cleared
        :return: sid list of ace entries removed successfully
        """
        access_entries = self.get_ace_list()
        sid_list = access_entries.sid_list

        if white_list:
            sid_white_list = [UnityAclUser.get_sid(self._cli,
                                                   user,
                                                   self.cifs_server.domain)
                              for user in white_list]
            sid_list = list(set(sid_list) - set(sid_white_list))

        resp = self.delete_ace(sid=sid_list)
        resp.raise_if_err()
        return sid_list

    def add_ace(self, domain=None, user=None, access_level=None):
        if domain is None:
            domain = self.cifs_server.domain
        if user is None:
            raise ValueError('cifs username is not specified.')

        if access_level is None:
            access_level = ACEAccessLevelEnum.FULL
        sid = UnityAclUser.get_sid(self._cli, user=user, domain=domain)
        ace = self._cli.make_body(
            sid=sid,
            accessType=ACEAccessTypeEnum.GRANT,
            accessLevel=access_level
        )

        resp = self.action("setACEs", cifsShareACEs=[ace])
        resp.raise_if_err()
        return resp

    def delete_ace(self, domain=None, user=None, sid=None):
        """ delete ACE for the share

        delete ACE for the share.  User could either supply the domain and
        username or the sid of the user.

        :param domain: domain of the user
        :param user: username
        :param sid: sid of the user or sid list of the user
        :return: REST API response
        """
        if sid is None:
            if domain is None:
                domain = self.cifs_server.domain

            sid = UnityAclUser.get_sid(self._cli, user=user, domain=domain)
        if isinstance(sid, six.string_types):
            sid = [sid]
        ace_list = [self._make_remove_ace_entry(s) for s in sid]

        resp = self.action("setACEs", cifsShareACEs=ace_list)
        resp.raise_if_err()
        return resp

    def _make_remove_ace_entry(self, sid):
        return self._cli.make_body(
            sid=sid,
            accessType=ACEAccessTypeEnum.NONE,
            accessLevel=ACEAccessLevelEnum.FULL)

    def modify(self, is_read_only=None, is_ace_enabled=None, add_ace=None,
               delete_ace=None, is_encryption_enabled=None,
               is_con_avail_enabled=None, is_abe_enabled=None,
               is_branch_cache_enabled=None, offline_availability=None,
               umask=None, description=None):
        if self.type == CIFSTypeEnum.CIFS_SHARE:
            share_param = self.prepare_cifs_share_parameters(
                is_read_only=is_read_only,
                is_encryption_enabled=is_encryption_enabled,
                is_con_avail_enabled=is_con_avail_enabled,
                is_ace_enabled=is_ace_enabled,
                add_ace=add_ace, delete_ace=delete_ace,
                is_abe_enabled=is_abe_enabled,
                is_branch_cache_enabled=is_branch_cache_enabled,
                offline_availability=offline_availability,
                umask=umask, description=description)
            if share_param:
                resp = self._modify_fs_share(share_param)
            else:
                resp = RestResponse('', self._cli)
        if self.type == CIFSTypeEnum.CIFS_SNAPSHOT:
            share_param = self.prepare_cifs_share_parameters(
                is_encryption_enabled=is_encryption_enabled,
                is_con_avail_enabled=is_con_avail_enabled,
                is_abe_enabled=is_abe_enabled,
                is_branch_cache_enabled=is_branch_cache_enabled,
                offline_availability=offline_availability,
                umask=umask, description=description)
            if share_param:
                resp = self._modify_snap_share(share_param)
            else:
                resp = RestResponse('', self._cli)

        resp.raise_if_err()
        return resp

    def _modify_snap_share(self, cifs_share_param):
        return self.action('modify', **cifs_share_param)

    def _modify_fs_share(self, cifs_share_param):
        sr = self.storage_resource
        if sr is None:
            raise ValueError('storage resource for share {} not found.'
                             .format(self.name))

        modify_param = self._cli.make_body(
            allow_empty=True,
            cifsShare=self,
            cifsShareParameters=cifs_share_param)
        param = self._cli.make_body(
            allow_empty=True,
            cifsShareModify=[modify_param])

        resp = sr.modify_fs(**param)
        resp.raise_if_err()
        return resp

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

    @staticmethod
    def prepare_cifs_share_parameters(**kwargs):
        offline_availability = kwargs.get('offline_availability')
        CifsShareOfflineAvailabilityEnum.verify(offline_availability)

        cifs_share_param = UnityClient.make_body(
            allow_empty=True,
            isReadOnly=kwargs.get('is_read_only'),
            isEncryptionEnabled=kwargs.get('is_encryption_enabled'),
            isContinuousAvailabilityEnabled=kwargs.get(
                'is_con_avail_enabled'),
            isACEEnabled=kwargs.get('is_ace_enabled'),
            addACE=kwargs.get('add_ace'),
            deleteACE=kwargs.get('delete_ace'),
            isABEEnabled=kwargs.get('is_abe_enabled'),
            isBranchCacheEnabled=kwargs.get('is_branch_cache_enabled'),
            offlineAvailability=offline_availability,
            umask=kwargs.get('umask'),
            description=kwargs.get('description'))
        return cifs_share_param


class UnityCifsShareList(UnityResourceList):
    @classmethod
    def get_resource_class(cls):
        return UnityCifsShare


class UnityCifsShareAce(UnityAttributeResource):
    pass


class UnityCifsShareAceList(UnityResourceList):
    def __init__(self, cli=None, cifs_share=None, **the_filter):
        super(UnityCifsShareAceList, self).__init__(
            cli=cli, **the_filter)
        self.cifs_share = cifs_share

    def _get_raw_resource(self):
        resp = self.cifs_share.action('getACEs')
        resp.raise_if_err()
        return resp.first_content['cifsShareACEs']

    @property
    def sid_list(self):
        return [ace.sid for ace in self]

    @classmethod
    def get_resource_class(cls):
        return UnityCifsShareAce


class UnityAclUser(UnityResource):
    @classmethod
    def get_sid(cls, cli, user, domain=None):
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
