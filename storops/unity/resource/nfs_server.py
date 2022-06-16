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

import storops.unity.resource.nas_server
from storops.unity.resource import UnityResource, UnityResourceList

__author__ = 'Jay Xu'

LOG = logging.getLogger(__name__)


class UnityNfsServer(UnityResource):
    @classmethod
    def create(cls, cli, nas_server, host_name=None, nfs_v4_enabled=True,
               is_secure_enabled=None, is_extended_credentials_enabled=None,
               kdc_type=None, kdc_username=None, kdc_password=None,
               nfs_v3_enabled=None, credentials_cache_ttl=None):
        clz = storops.unity.resource.nas_server.UnityNasServer
        nas_server = clz.get(cli, nas_server)

        resp = cli.post(
            cls().resource_class,
            nasServer=nas_server,
            hostName=host_name,
            nfsv4Enabled=nfs_v4_enabled,
            isSecureEnabled=is_secure_enabled,
            isExtendedCredentialsEnabled=is_extended_credentials_enabled,
            kdcType=kdc_type,
            kdcUsername=kdc_username,
            kdcPassword=kdc_password,
            nfsv3Enabled=nfs_v3_enabled,
            credentialsCacheTTL=credentials_cache_ttl)

        resp.raise_if_err()
        return cls(_id=resp.resource_id, cli=cli)

    def delete(self, skip_kdc_unjoin=None, username=None,
               password=None, async_mode=False):
        resp = self._cli.delete(self.resource_class,
                                self.get_id(),
                                skipUnjoin=skip_kdc_unjoin,
                                kdcUsername=username,
                                kdcPassword=password,
                                async_mode=async_mode)
        resp.raise_if_err()
        return resp

    def modify(self, host_name=None, nfs_v4_enabled=None,
               is_secure_enabled=None, is_extended_credentials_enabled=None,
               kdc_type=None, kdc_username=None, kdc_password=None,
               nfs_v3_enabled=None, credentials_cache_ttl=None):
        req_body = self._cli.make_body(
            hostName=host_name,
            nfsv4Enabled=nfs_v4_enabled,
            isSecureEnabled=is_secure_enabled,
            isExtendedCredentialsEnabled=is_extended_credentials_enabled,
            kdcType=kdc_type,
            kdcUsername=kdc_username,
            kdcPassword=kdc_password,
            nfsv3Enabled=nfs_v3_enabled,
            credentialsCacheTTL=credentials_cache_ttl)

        resp = self.action('modify', **req_body)
        resp.raise_if_err()
        return resp


class UnityNfsServerList(UnityResourceList):
    @classmethod
    def get_resource_class(cls):
        return UnityNfsServer
