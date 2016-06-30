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

from retryz import retry

from comptest import t_unity
from comptest.utils import ResourceManager
from storops import exception as ex, FSSupportedProtocolEnum, \
    FileInterfaceRoleEnum
from storops.exception import UnityCifsServiceNotEnabledError, \
    UnitySmbServerLockedError

__author__ = 'Cedric Zhuang'

log = logging.getLogger(__name__)


class UnityTestResourceManager(ResourceManager):
    def __init__(self, name):
        super(UnityTestResourceManager, self).__init__(name)
        self.unity = None
        self.pool = None
        self.nas_server = None

    def setup(self):
        super(UnityTestResourceManager, self).setup()
        self.unity = t_unity()
        self.pool = self._create_pool()
        self.nas_server = self._create_nas_server(
            '{}_nas_server'.format(self.name))

    def _create_pool(self, name=None):
        if name:
            ret = self.unity.get_pool(name=name)
        else:
            ret = self.unity.get_pool().first_item
        return ret

    def _create_nas_server(self, name=None):
        name = self.add_nas_server_name(name)
        try:
            server = self.unity.create_nas_server(name)
        except ex.UnityNasServerNameUsedError:
            server = self.unity.get_nas_server(name=name)

        return server

    def _create_fs(self, proto, name=None, size=None):
        if size is None:
            size = 3 * 1024 ** 3
        name = self.add_fs_name(name)
        try:
            fs = self.pool.create_filesystem(
                self.nas_server, name, size, proto=proto)
        except ex.UnityFileSystemNameAlreadyExisted:
            fs = self.unity.get_filesystem(name=name)
        return fs

    def _create_cifs_share(self, name=None):
        fs = self._create_fs(FSSupportedProtocolEnum.CIFS)
        name = self.add_cifs_share_name(name)
        try:
            cs = fs.create_cifs_share(name=name)
        except (ex.UnitySmbShareNameExistedError, ex.UnitySmbNameInUseError):
            cs = self.unity.get_cifs_share(name=name)
        return cs

    def create_nfs_share(self, name=None):
        fs = self._create_fs(FSSupportedProtocolEnum.NFS)
        name = self.add_nfs_share_name(name)
        try:
            ns = fs.create_nfs_share(name=name)
        except ex.UnityNfsShareNameExistedError:
            ns = self.unity.get_nfs_share(name=name)
        return ns

    def _enable_nfs_service(self):
        try:
            self.nas_server.enable_nfs_service()
        except ex.UnityNfsAlreadyEnabledError:
            log.info('nfs already enabled on {}'.format(self.nas_server.name))

    def _enable_cifs_service(self):
        try:
            server_name = self.add_cifs_server_name(
                '{}_cifs_server'.format(self._name))
            wg_name = server_name.upper()[-15:]
            self.nas_server.enable_cifs_service(
                name=server_name,
                workgroup=wg_name,
                netbios_name=wg_name,
                local_password='Password123!')
        except (ex.UnityNetBiosNameExistedError,
                ex.UnityOneSmbServerPerNasServerError):
            log.info('cifs already enabled on {}'.format(self.nas_server.name))

    def clean_up(self):
        # noinspection PyBroadException
        try:
            super(UnityTestResourceManager, self).clean_up()

            self._clean_up_snap()
            self._clean_up_cifs_share()
            self._clean_up_nfs_share()
            self._clean_up_fs()
            self._clean_up_nas_server()

            self._names.destroy()
        except Exception:
            self._remove_worker()
            raise

    def _clean_up_nas_server(self):
        while self.has_nas_server_name():
            name = None
            try:
                name = self._pop_name('nas_server')
                server = self.unity.get_nas_server(name=name)
                if server.existed:
                    self._delete_nas_server(server)
            except (ex.UnityResourceNotFoundError, IndexError):
                log.exception('remove nas server {} failed.'.format(name))

    def _clean_up_fs(self):
        while self.has_fs_name():
            name = None
            try:
                name = self._pop_name('fs')
                log.debug('start removing fs {}.'.format(name))
                fs = self.unity.get_filesystem(name=name)
                if fs.existed:
                    fs.delete(force_snap_delete=True,
                              force_vvol_delete=True)
            except (ex.UnityResourceNotFoundError, IndexError):
                log.exception('remove fs {} failed.'.format(name))

    def _clean_up_nfs_share(self):
        while self.has_nfs_share_name():
            try:
                self._pop_name('nfs_share')
            except IndexError:
                pass

    def _clean_up_cifs_share(self):
        while self.has_cifs_share_name():
            try:
                self._pop_name('cifs_share')
            except IndexError:
                pass

    def _clean_up_snap(self):
        while self.has_snap_name():
            try:
                self._pop_name('snap')
            except IndexError:
                pass

    @retry(on_error=ex.UnityNasServerHasFsError, wait=7)
    def _delete_nas_server(self, server):
        server.delete()


class UnityGeneralFixture(UnityTestResourceManager):
    def __init__(self):
        super(UnityGeneralFixture, self).__init__('ug')
        self.cifs_share = None
        self.nfs_share = None

    def setup(self):
        clz_name = self.__class__.__name__
        log.debug('start {} setup.'.format(clz_name))
        # noinspection PyBroadException
        try:
            super(UnityGeneralFixture, self).setup()

            self._enable_nfs_service()
            self._enable_cifs_service()

            self.cifs_share = self._create_cifs_share('ug_cifs_share')
            self.nfs_share = self.create_nfs_share('ug_nfs_share')
        except Exception:
            log.exception('failed to initialize {}'.format(clz_name))
            self._remove_worker()


class UnityCifsShareFixture(UnityTestResourceManager):
    def __init__(self):
        super(UnityCifsShareFixture, self).__init__('ucs')
        self.domain_user = None
        self.domain_pass = None
        self.domain = None
        self.domain_controller = None
        self.ip_port = None
        self.ip = None
        self.gateway = None
        self.cifs_share = None

    def setup(self):
        # please make sure system level
        # NTP server and DNS server has already
        # been configured on the unity system!

        self.domain_user = 'administrator'
        self.domain_pass = 'Password123!'
        self.domain = 'win2012.dev'
        self.domain_controller = '10.244.209.72'
        self.ip_port = 'spa_eth2'
        self.ip = '10.244.213.177'
        self.gateway = '10.244.213.1'

        clz_name = self.__class__.__name__
        log.debug('start {} setup.'.format(clz_name))
        # noinspection PyBroadException
        try:
            super(UnityCifsShareFixture, self).setup()
            self._enable_cifs_domain()
            self.cifs_share = self._create_cifs_share('ucs_cifs_share')
        except Exception:
            log.exception('failed to initialize {}'.format(clz_name))
            self._remove_worker()

    def clean_up(self):
        # noinspection PyBroadException
        try:
            self._clean_up_fs()
            self._delete_cifs_server()
            super(UnityCifsShareFixture, self).clean_up()
        except Exception:
            self._remove_worker()
            raise

    def _delete_cifs_server(self):
        try:
            cifs_server = self.nas_server.get_cifs_server()
            cifs_server.delete(username=self.domain_user,
                               password=self.domain_pass)
        except (UnityCifsServiceNotEnabledError,
                UnitySmbServerLockedError):
            # cifs server has already been deleted.
            pass

    def _enable_cifs_domain(self):
        try:
            server_name = self.add_cifs_server_name()
            self._create_dns_server()
            bios_name = server_name.upper()[-15:]
            self.nas_server.enable_cifs_service(
                name=server_name,
                interfaces=[self._create_file_interface()],
                netbios_name=bios_name,
                domain=self.domain,
                domain_username=self.domain_user,
                domain_password=self.domain_pass)
        except (ex.UnityNetBiosNameExistedError,
                ex.UnityOneDnsPerNasServerError):
            log.info('cifs already enabled on {}'.format(self.nas_server.name))

    def _create_file_interface(self, port=None, ip=None, gateway=None):
        if port is None:
            port = self.ip_port
        if ip is None:
            ip = self.ip
        if gateway is None:
            gateway = self.gateway

        return self.nas_server.create_file_interface(
            port, ip, gateway=gateway, role=FileInterfaceRoleEnum.PRODUCTION)

    def _create_dns_server(self):
        return self.nas_server.create_dns_server(
            self.domain, self.domain_controller)
