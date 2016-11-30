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

from retryz import retry

import storops.vnx.resource.block_pool
import storops.vnx.resource.cg
import storops.vnx.resource.mirror_view
import storops.vnx.resource.sg
from storops import exception as ex
from storops.lib.common import check_int, daemon, instance_cache
from storops.lib.converter import to_bool
from storops.vnx.enums import VNXLunType, VNXTieringEnum, VNXProvisionEnum, \
    VNXMigrationRate
from storops.vnx.resource import VNXCliResourceList, VNXCliResource
from storops.vnx.resource.migration import VNXMigrationSession
from storops.vnx.resource.snap import VNXSnap, VNXSnapList

__author__ = 'Cedric Zhuang'


class _IsMigratingError(Exception):
    pass


class VNXLunList(VNXCliResourceList):
    def __init__(self, cli=None, lun_type=None, lun_ids=None, pool=None):
        super(VNXLunList, self).__init__(cli)
        self._lun_type = None
        self._lun_ids = None
        self._pool_name = None

        self._set_filter(lun_type, lun_ids, pool)

    def _set_filter(self, lun_type=None, lun_ids=None, pool=None):
        self._lun_type = VNXLunType.parse(lun_type)
        self._lun_ids = lun_ids
        if isinstance(pool, VNXCliResource):
            self._pool_name = pool._get_name()
        else:
            self._pool_name = pool

    def _filter(self, lun):
        if self._lun_ids is not None:
            ret = VNXLun.get_id(lun) in self._lun_ids
        elif self._pool_name is not None:
            ret = lun.pool_name == self._pool_name
        else:
            ret = True
        return ret

    @classmethod
    def get_resource_class(cls):
        return VNXLun

    @property
    @instance_cache
    def _lun_id_map(self):
        return {lun.lun_id: lun for lun in self}

    def _get_raw_resource(self):
        return self._cli.get_lun(lun_type=self._lun_type, poll=self.poll)

    def get(self, _id):
        if isinstance(_id, VNXLun):
            _id = VNXLun.get_id(_id)

        return self._lun_id_map.get(_id)


class VNXLun(VNXCliResource):
    DEFAULT_TIER = VNXTieringEnum.HIGH_AUTO
    DEFAULT_PROVISION = VNXProvisionEnum.THICK

    def __init__(self, lun_id=None, name=None, cli=None):
        super(VNXLun, self).__init__()
        self._cli = cli
        self._lun_id = lun_id
        self._name = name

    def _get_raw_resource(self):
        if self._cli is None:
            raise ValueError('client is not available for this resource.')
        return self._cli.get_lun(name=self._name, lun_id=self._lun_id,
                                 poll=self.poll)

    @property
    def is_snap_mount_point(self):
        return self.primary_lun is not None

    @staticmethod
    def create(cli,
               pool_id=None,
               pool_name=None,
               lun_id=None,
               lun_name=None,
               size_gb=1,
               provision=None,
               tier=None,
               ignore_thresholds=None):
        cls = storops.vnx.resource.block_pool.VNXPool
        pool = cls(pool_id, pool_name, cli)
        return pool.create_lun(lun_name, size_gb, lun_id, provision,
                               tier, ignore_thresholds)

    def create_mount_point(self, _id=None, name=None):
        lun_id = self.get_id(self)
        out = self._cli.create_mount_point(
            primary_lun_id=lun_id,
            mount_point_name=name,
            mount_point_id=_id,
            poll=self.poll)
        ex.raise_if_err(out, default=ex.VNXCreateMpError)
        return VNXLun(lun_id=_id, name=name, cli=self._cli)

    @property
    def tier(self):
        try:
            tier = VNXTieringEnum.get_tier(
                self.initial_tier,
                self.tiering_policy)
        except AttributeError:
            tier = self.DEFAULT_TIER
        return tier

    @tier.setter
    def tier(self, new_tier):
        new_tier = VNXTieringEnum.parse(new_tier)
        out = self._cli.modify_lun(lun_id=self._lun_id,
                                   lun_name=self._name,
                                   new_tier=new_tier,
                                   poll=self.poll)
        msg = 'error change lun tier.'
        ex.raise_if_err(out, msg, default=ex.VNXModifyLunError)

    @property
    def provision(self):
        ret = self.DEFAULT_PROVISION
        try:
            if self.is_thin_lun:
                ret = VNXProvisionEnum.THIN
            if self.is_compressed:
                ret = VNXProvisionEnum.COMPRESSED
            elif self.is_dedup:
                ret = VNXProvisionEnum.DEDUPED
        except AttributeError:
            pass
        return ret

    @property
    def is_dedup(self):
        return to_bool(self.deduplication_state)

    @is_dedup.setter
    def is_dedup(self, value):
        self._update_dedup_state(value)

    @staticmethod
    def get(cli, lun_id=None, name=None, lun_type=None, lun_ids=None,
            poll=True):
        if lun_id is None and name is None:
            ret = VNXLunList(cli=cli, lun_type=lun_type, lun_ids=lun_ids)
        else:
            ret = VNXLun(lun_id, name, cli)
        ret.poll = poll
        return ret

    def create_snap(self, name, allow_rw=None, auto_delete=None,
                    keep_for=None):
        return VNXSnap.create(self._cli, self.get_id(self), name, allow_rw,
                              auto_delete, keep_for)

    def attach_snap(self, snap):
        snap_name = VNXSnap.get_name(snap)
        out = self._cli.attach_snap(snap_name, lun_id=self.get_id(self),
                                    poll=self.poll)
        ex.raise_if_err(out, 'failed to attach snap {}'.format(snap_name),
                        default=ex.VNXAttachSnapError)

    def detach_snap(self):
        lun_id = self.get_id(self)
        out = self._cli.detach_snap(lun_id=lun_id, poll=self.poll)
        msg = 'failed to detach snap for lun {}.'.format(lun_id)
        ex.raise_if_err(out, msg, default=ex.VNXDetachSnapError)

    def get_snap(self, name=None):
        if name is not None:
            ret = VNXSnap.get(self._cli, name)
        else:
            ret = VNXSnapList(self._cli, res=self.get_id(self))
        return ret

    def delete_snap(self, name):
        VNXSnap(name, self._cli).delete()

    def migrate(self, tgt, rate=VNXMigrationRate.HIGH, on_complete=None,
                on_error=None):
        tgt_id = self.get_id(tgt)
        src_id = self.get_id(self)
        out = self._cli.migrate_lun(src_id, tgt_id, rate, poll=self.poll)
        ex.raise_if_err(out, default=ex.VNXMigrationError)

        if on_complete or on_error:
            ret = daemon(self._wait_for_migration_done, on_complete, on_error)
        else:
            ret = None
        return ret

    @retry(on_error=_IsMigratingError, wait=15, timeout=60 * 60 * 24 * 7)
    def _wait_for_migration_done(self, on_complete=None, on_error=None):
        migration = VNXMigrationSession(source=self, cli=self._cli)
        if migration.is_migrating:
            raise _IsMigratingError()
        elif migration.is_success and on_complete:
            ret = on_complete()
        elif on_error:
            ret = on_error()
        else:
            ret = None
        return ret

    def expand(self, new_size, ignore_thresholds=False):
        out = self._cli.expand_pool_lun(new_size, self.get_id(self),
                                        ignore_thresholds=ignore_thresholds,
                                        poll=self.poll)
        ex.raise_if_err(out, default=ex.VNXLunExtendError)

    def cancel_migrate(self):
        src_id = self.get_id(self)
        out = self._cli.cancel_migrate_lun(src_id, poll=self.poll)
        ex.raise_if_err(out, 'migrate lun {} error.'.format(src_id),
                        default=ex.VNXMigrationError)

    def get_migration_session(self):
        return VNXMigrationSession.get(self._cli, self)

    @staticmethod
    def get_id(lun):
        if isinstance(lun, VNXLun):
            if lun._lun_id is not None:
                lun = lun._lun_id
            else:
                lun = lun.lun_id
        try:
            lun = check_int(lun)
        except ValueError:
            raise ValueError('invalid lun number supplied: {}'
                             .format(lun))
        return lun

    @classmethod
    def get_id_list(cls, *lun_list):
        return list(map(cls.get_id, lun_list))

    def detach_from_sg(self, sg=None):
        if sg is None:
            clz = storops.vnx.resource.sg.VNXStorageGroupList
            obj = clz(cli=self._cli)
        else:
            obj = sg
        obj.detach_alu(self)

    def detach_from_cg(self, cg=None):
        if cg is None:
            clz = storops.vnx.resource.cg.VNXConsistencyGroupList
            obj = clz(cli=self._cli)
        else:
            obj = cg
        obj.delete_member(self)

    def clear_smp(self, force=False):
        smp_list = self.snapshot_mount_points
        if smp_list:
            for smp in self.snapshot_mount_points:
                smp.delete(force=force)

    def delete(self, delete_snapshots=False, force_detach=False,
               detach_from_sg=False, detach_from_cg=False, force=False):
        if force:
            delete_snapshots = True
            force_detach = True
            detach_from_sg = True
            detach_from_cg = True

        while True:
            out = self._do_delete(delete_snapshots, force_detach)
            try:
                ex.raise_if_err(out,
                                'failed to remove lun {}'.format(
                                    self._get_name()),
                                default=ex.VNXDeleteLunError)
                break
            except ex.VNXLunInStorageGroupError:
                if detach_from_sg:
                    self.detach_from_sg()
                else:
                    raise
            except ex.VNXLunInConsistencyGroupError:
                if detach_from_cg:
                    self.detach_from_cg()
                else:
                    raise
            except ex.VNXLunHasSnapMountPointError:
                if force:
                    self.clear_smp(force)
                else:
                    raise

    def _do_delete(self, delete_snapshots, force_detach):
        return self._cli.delete_pool_lun(self._lun_id,
                                         self._get_name(),
                                         delete_snapshots=delete_snapshots,
                                         force_detach=force_detach,
                                         poll=self.poll)

    def rename(self, new_name):
        if new_name is not None and self._name != new_name:
            out = self._cli.modify_lun(lun_id=self._lun_id,
                                       lun_name=self._name,
                                       new_name=new_name,
                                       poll=self.poll)
            ex.raise_if_err(out, 'failed to change lun name.',
                            default=ex.VNXModifyLunError)
            self._name = new_name

    def __setattr__(self, key, value):
        if key == 'name':
            self.rename(value)
            return
        elif key == 'is_compressed':
            if value:
                self.enable_compression()
            else:
                self.disable_compression()
            return
        super(VNXLun, self).__setattr__(key, value)

    def enable_compression(self, rate=None, ignore_thresholds=None):
        lun_id = self.get_id(self)
        out = self._cli.enable_compression(
            lun_id=lun_id, rate=rate, ignore_thresholds=ignore_thresholds,
            poll=self.poll)
        msg = 'failed to enable compression on {}.'.format(lun_id)
        ex.raise_if_err(out, msg, ex.VNXCompressionError)

    def disable_compression(self, ignore_thresholds=None):
        lun_id = self.get_id(self)
        out = self._cli.disable_compression(lun_id, ignore_thresholds,
                                            poll=self.poll)
        ex.raise_if_err(
            out, 'failed to disable compression on {}.'.format(lun_id),
            default=ex.VNXCompressionError)

    def _update_dedup_state(self, tgt_state):
        out = self._cli.modify_lun(lun_id=self._lun_id,
                                   lun_name=self._name,
                                   dedup=tgt_state, poll=self.poll)
        ex.raise_if_err(out, default=ex.VNXDedupError)

    def enable_dedup(self):
        self._update_dedup_state(True)

    def disable_dedup(self):
        self._update_dedup_state(False)

    def create_mirror_view(self, name, use_write_intent_log=True):
        clz = storops.vnx.resource.mirror_view.VNXMirrorView
        return clz.create(self._cli, name, self, use_write_intent_log)

    def get_mirror_view(self, as_src=None, as_tgt=None):
        src_lun = None
        tgt_lun = None
        if as_src is None and as_tgt is None:
            src_lun = self
            tgt_lun = self
        if as_src:
            src_lun = self
        if as_tgt:
            tgt_lun = self

        clz = storops.vnx.resource.mirror_view.VNXMirrorViewList
        return clz(self._cli, src_lun=src_lun, tgt_lun=tgt_lun)
