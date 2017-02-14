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

from storops_comptest import t_vnx, vnx1, vnx2
from storops_comptest.utils import ResourceManager
from storops import exception as ex

__author__ = 'Cedric Zhuang'

log = logging.getLogger(__name__)


class VNXTestResourceManager(ResourceManager):
    def __init__(self, name):
        super(VNXTestResourceManager, self).__init__(name)
        self.vnx = None
        self.pool = None
        self.lun = None

    def _create_cg(self, name):
        if not self.has_cg_name(name):
            try:
                ret = self.vnx.create_cg(name)
            except ex.VNXConsistencyGroupNameInUseError:
                ret = self.vnx.get_cg(name)
            self.add_cg_name(name)
        else:
            ret = self.vnx.get_cg(name)
        return ret

    def _create_sg(self, name):
        if not self.has_sg_name(name):
            try:
                ret = self.vnx.create_sg(name)
            except ex.VNXStorageGroupNameInUseError:
                ret = self.vnx.get_sg(name=name)
            self.add_sg_name(name)
        else:
            ret = self.vnx.get_sg(name=name)
        ret.shuffle_hlu = False
        return ret

    def _create_snap(self, name):
        if not self.has_snap_name(name):

            @retry(on_error=ex.VNXLunPreparingError, wait=7)
            def _do_create():
                try:
                    snap = self.lun.create_snap(name, allow_rw=True)
                except ex.VNXSnapNameInUseError:
                    snap = self.vnx.get_snap(name)
                self.add_snap_name(name)
                return snap

            ret = _do_create()
        else:
            ret = self.vnx.get_snap(name)
        return ret

    def _get_pool(self, vnx=None):
        if vnx is None:
            vnx = self.vnx
        pools = vnx.get_pool()
        if pools:
            ret = pools[0]
        else:
            ret = None
        return ret

    def _create_pool(self, name, vnx=None):
        if vnx is None:
            vnx = self.vnx
        if not self.has_pool_name(name):

            @retry(on_error=ex.VNXDiskUsedError, wait=7)
            def _do_create():
                try:
                    pool = vnx.create_pool(name)
                except ex.VNXPoolNameInUseError:
                    pool = vnx.get_pool(name=name)
                self.add_pool_name(name)
                return pool

            ret = _do_create()
        else:
            ret = vnx.get_pool(name=name)
        return ret

    def _create_lun(self, name, vnx=None, pool=None):
        if vnx is None:
            vnx = self.vnx
        if pool is None:
            pool = self.pool

        if not self.has_lun_name(name):
            try:
                ret = pool.create_lun(name)
            except ex.VNXLunNameInUseError:
                ret = vnx.get_lun(name=name)
            self.add_lun_name(name)
        else:
            ret = vnx.get_lun(name=name)
        return ret

    def clean_up(self):
        super(VNXTestResourceManager, self).clean_up()

        self._clean_up_snap()
        self._clean_up_cg()
        self._clean_up_mirror()
        self._clean_up_sg()
        self._clean_up_lun()
        self._clean_up_pool()
        self._names.destroy()

    def _clean_up_pool(self):
        while self.has_name('pool'):
            name = None
            try:
                name = self._pop_name('pool')
                pool = self.vnx.get_pool(name=name)
                if pool.existed:
                    pool.delete(force=True)
            except (ex.VNXPoolNotFoundError, ex.VNXPoolDestroyingError,
                    IndexError):
                log.exception('delete pool {} failed.'.format(name))

    def _clean_up_lun(self, vnx=None):
        if vnx is None:
            vnx = self.vnx
        while self.has_name('lun'):
            name = None
            try:
                name = self._pop_name('lun')
                lun = vnx.get_lun(name=name)
                if lun.existed:
                    lun.delete(force=True)
            except (ex.VNXLunNotFoundError, ex.VNXDeleteLunError, IndexError):
                log.exception('delete lun {} failed.'.format(name))

    def _clean_up_sg(self):
        while self.has_name('sg'):
            name = None
            try:
                name = self._pop_name('sg')
                sg = self.vnx.get_sg(name=name)
                if sg.existed:
                    sg.delete(disconnect_host=True)
            except (ex.VNXStorageGroupNotFoundError, IndexError):
                log.exception('delete sg {} failed.'.format(name))

    def _clean_up_cg(self):
        while self.has_name('cg'):
            name = None
            try:
                name = self._pop_name('cg')
                cg = self.vnx.get_cg(name=name)
                if cg.existed:
                    cg.delete()
            except (ex.VNXConsistencyGroupNotFoundError, IndexError):
                log.exception('delete cg {} failed.'.format(name))

    def _clean_up_mirror(self):
        @retry(on_error=ex.VNXMirrorRemoveSynchronizingError, wait=10,
               limit=18)
        def _remove_image(m):
            m.fracture_image()
            m.remove_image()

        while self.has_name('mirror'):
            name = None
            try:
                name = self._pop_name('mirror')
                mirror = self.vnx.get_mirror_view(name=name)
                if mirror.existed:
                    if len(mirror.images) > 1:
                        _remove_image(mirror)
                    mirror.delete()
            except ex.VNXMirrorException:
                log.exception('delete mirror {} failed.'.format(name))

    def _clean_up_snap(self):
        while self.has_snap_name():
            self._pop_name('snap')


class VNXGeneralFixtureManager(VNXTestResourceManager):
    def __init__(self):
        super(VNXGeneralFixtureManager, self).__init__('vg')
        self.cg = None
        self.snap = None
        self.sg = None

    def setup(self):
        clz_name = self.__class__.__name__
        log.debug('start {} setup.'.format(clz_name))
        try:
            super(VNXGeneralFixtureManager, self).setup()
            self.vnx = t_vnx()
            self.cg = self._create_cg('general_cg')
            self.pool = self._get_pool()
            if self.pool is None:
                self.pool = self._create_pool('general_pool')
            self.lun = self._create_lun('general_lun')
            self.snap = self._create_snap('general_snap')
            self.sg = self._create_sg('general_sg')
        except ex.StoropsException:
            log.exception('failed to initialize {}'.format(clz_name))
            raise

    def select_port(self):
        ports = self.vnx.get_iscsi_port()
        for port in ports:
            if port.ip_address is None:
                break
        else:
            raise ValueError('no available iSCSI port found.')
        return port.sp, port.port_id


class MultiVNXGeneralFixtureManager(VNXTestResourceManager):
    src_lun = 'general_mirror_src'
    tgt_lun = 'general_mirror_tgt'

    def __init__(self):
        super(MultiVNXGeneralFixtureManager, self).__init__('mvg')
        self.vnx1 = None
        self.vnx2 = None
        self.lun1 = None
        self.lun2 = None
        self.mirror = None

    def setup(self):
        clz_name = self.__class__.__name__
        log.debug('start {} setup.'.format(clz_name))
        try:
            super(MultiVNXGeneralFixtureManager, self).setup()
            self.vnx = vnx1()
            self.vnx1 = self.vnx
            self.vnx2 = vnx2()
            self.lun = self._get_mirror_lun(self.vnx1, self.src_lun)
            self.lun1 = self.lun
            self.lun2 = self._get_mirror_lun(self.vnx2, self.tgt_lun)
            self.mirror = self._create_mirror('general_sync_mirror')
        except ex.StoropsException:
            log.exception('failed to initialize {}'.format(clz_name))
            raise

    def _get_mirror_lun(self, vnx, name):
        pool = self._get_pool(vnx=vnx)
        if pool is None:
            pool = self._create_pool('general_pool', vnx=vnx)
        return self._create_lun(name, vnx=vnx, pool=pool)

    def _create_mirror(self, name):
        if not self.has_mirror_name(name):
            try:
                ret = self.lun1.create_mirror_view(name, False)
            except ex.VNXMirrorNameInUseError:
                ret = self.vnx1.get_mirror_view(name)
            self.add_mirror_name(name)
        else:
            ret = self.vnx.get_mirror_view(name)

        ret.add_image(self.vnx2.spa_ip, self.lun2.lun_id)
        return ret

    def clean_up(self):
        super(MultiVNXGeneralFixtureManager, self).clean_up()

        # remote the remote LUN
        try:
            lun = self.vnx2.get_lun(name=self.tgt_lun)
            if lun.existed:
                lun.delete(force=True)
        except (ex.VNXLunNotFoundError, ex.VNXDeleteLunError, IndexError):
            log.exception('delete lun {} failed.'.format(self.tgt_lun))
