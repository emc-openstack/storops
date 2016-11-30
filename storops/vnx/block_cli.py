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

import functools
import logging
from multiprocessing.pool import ThreadPool

import six
from retryz import retry

import storops.vnx.resource.system
from storops import exception as ex
from storops.exception import OptionMissingError
from storops.lib.common import check_int, text_var, int_var, enum_var, \
    yes_no_var
from storops.lib.metric import PerfManager
from storops.vnx.enums import VNXSPEnum, VNXTieringEnum, VNXProvisionEnum, \
    VNXMigrationRate, VNXCompressionRate, \
    VNXMirrorViewRecoveryPolicy, VNXMirrorViewSyncRate, VNXLunType, \
    VNXRaidType, VNXPoolRaidType, VNXUserScopeEnum, VNXUserRoleEnum
from storops.vnx.heart_beat import NodeHeartBeat

__author__ = 'Cedric Zhuang'

log = logging.getLogger(__name__)


def _get_commands(f, self, *argv, **kwargs):
    if not isinstance(self, CliClient):
        raise ValueError('self must be an instance of CliClient.')
    no_poll = not kwargs.get('poll', True)
    kwargs.pop('poll', None)
    commands = f(self, *argv, **kwargs)
    if isinstance(commands, six.string_types):
        commands = commands.split()
    commands = list(commands)
    if no_poll:
        commands.insert(0, '-np')
    return commands


def command(f):
    """ indicate it's a command of naviseccli

    :param f: function that returns the command in list
    :return: command execution result
    """

    @functools.wraps(f)
    def func_wrapper(self, *argv, **kwargs):
        if 'ip' in kwargs:
            ip = kwargs['ip']
            del kwargs['ip']
        else:
            ip = None

        commands = _get_commands(f, self, *argv, **kwargs)
        return self.execute(commands, ip=ip)

    return func_wrapper


def duel_command(f):
    """ indicate it's a command need to be called on both SP

    :param f: function that returns the command in list
    :return: command execution result on both sps (tuple of 2)
    """

    @functools.wraps(f)
    def func_wrapper(self, *argv, **kwargs):
        commands = _get_commands(f, self, *argv, **kwargs)
        return self.execute_dual(commands)

    return func_wrapper


class CliClient(PerfManager):
    def __init__(self, ip=None, username=None, password=None, scope=None,
                 sec_file=None, timeout=None, heartbeat_interval=None,
                 naviseccli=None):
        super(CliClient, self).__init__()
        if heartbeat_interval is None:
            heartbeat_interval = 60
        if scope is None:
            scope = 0
        self._heart_beat = NodeHeartBeat(
            username=username,
            password=password,
            scope=scope,
            sec_file=sec_file,
            interval=heartbeat_interval,
            timeout=timeout,
            naviseccli=naviseccli)
        self._heart_beat.add(VNXSPEnum.SP_A, ip)
        self._system_version = None

    def persist_rsc_list_metrics(self):
        persist_rsc_list = self.get_persist_rsc_list()
        if self.prev_counter and persist_rsc_list:
            for rsc_list in persist_rsc_list:
                rsc_list.persist_metric_data()

    def get_persist_rsc_list(self):
        if self.curr_counter is not None:
            ret = [rsc_list
                   for rsc_list in self.curr_counter.get_rsc_list_collection()
                   if self.is_perf_metric_enabled(rsc_list)]
        else:
            ret = []
        return ret

    def set_binary(self, binary):
        if binary is not None:
            log.info('update naviseccli binary location to: {}'.format(binary))
            self._heart_beat.set_binary(binary)

    def set_credential(self, username=None, password=None, scope=None,
                       sec_file=None):
        self._heart_beat.set_credential(username, password, scope, sec_file)

    def __del__(self):
        del self._heart_beat

    def set_ip(self, spa, spb=None, cs=None):
        self._heart_beat.add(VNXSPEnum.SP_A, spa)
        self._heart_beat.add(VNXSPEnum.SP_B, spb)
        self._heart_beat.add(VNXSPEnum.CONTROL_STATION, cs)

    @staticmethod
    def _select_one(items, allow_empty=False):
        for item in items:
            if not item:
                continue
            if item:
                ret = item
                break
        else:
            ret = []
        if not ret and not allow_empty:
            raise OptionMissingError(
                'at least one option should be available.')
        return ret

    @property
    def heartbeat(self):
        return self._heart_beat

    @command
    def get_control(self):
        return 'getcontrol'

    @command
    def get_agent(self):
        return 'getagent'

    @command
    def get_domain(self):
        return 'domain -list'

    @command
    def get_pool(self, name=None, pool_id=None):
        cmd = 'storagepool -list -all'.split()
        cmd += self._get_id_name_opt(pool_id, name, allow_empty=True)
        return cmd

    @command
    def get_lun(self, name=None, lun_id=None, lun_type=None):
        cmd = 'lun -list -all'.split()
        cmd += self._get_lun_opt(lun_id, name, lun_type, allow_empty=True)
        return cmd

    @command
    def get_cg(self, name=None):
        cmd = 'snap -group -list'.split()
        cmd += text_var('-id', name)
        cmd.append('-detail')
        return cmd

    @command
    def get_sp_port(self):
        return 'port -list -sp -all'

    @command
    def get_sp(self):
        return 'getsp'

    @command
    def get_connection_port(self, sp=None, port_id=None, vport_id=None):
        cmd = 'connection -getport -all'.split()
        if sp is not None:
            cmd += ['-sp', VNXSPEnum.get_sp_index(sp)]

        cmd += int_var('-portid', port_id)
        if port_id is not None:
            cmd += int_var('-vportid', vport_id)

        return cmd

    @command
    def get_sg(self, name=None, engineering=False):
        cmd = ['storagegroup']
        if engineering:
            cmd.append('-messner')
        cmd += '-list -host -iscsiAttributes'.split()
        cmd += text_var('-gname', name)
        return cmd

    @command
    def get_pool_feature(self):
        return ('storagepool -feature -info -isVirtualProvisioningSupported '
                '-maxPools -maxDiskDrivesPerPool -maxDiskDrivesAllPools '
                '-maxDiskDrivesPerOp -maxPoolLUNs -minPoolLUNSize '
                '-maxPoolLUNSize -numPools -numPoolLUNs -numThinLUNs '
                '-numDiskDrivesAllPools -availableDisks')

    @classmethod
    def _get_id_name_opt(cls, _id, name, allow_empty=False):
        try:
            ret = cls._select_one(
                [int_var('-id', _id), text_var('-name', name)],
                allow_empty)
        except OptionMissingError:
            raise ValueError('id or name need to be specified.')
        return ret

    @classmethod
    def _get_pool_opt(cls, pool_id, pool_name, allow_empty=False):
        try:
            ret = cls._select_one([int_var('-poolId', pool_id),
                                   text_var('-poolName', pool_name)],
                                  allow_empty=allow_empty)
        except OptionMissingError:
            raise ValueError('pool_id or pool_name need to be specified.')
        return ret

    @classmethod
    def _get_lun_opt(cls, lun_id=None, lun_name=None,
                     lun_type=None, allow_empty=False):
        try:
            ret = cls._select_one([int_var('-l', lun_id),
                                   text_var('-name', lun_name),
                                   enum_var('-showOnly', lun_type,
                                            VNXLunType)],
                                  allow_empty=allow_empty)
        except OptionMissingError:
            raise ValueError(
                'lun_id, lun_name or lun_type need to be specified.')
        return ret

    @classmethod
    def _get_primary_lun_opt(cls, primary_lun_id=None, primary_lun_name=None):
        try:
            ret = cls._select_one([int_var('-primaryLun', primary_lun_id),
                                   text_var('-primaryLunName',
                                            primary_lun_name)])
        except OptionMissingError:
            raise ValueError(
                'primary_lun_id or primary_lun_name need to be specified.')
        return ret

    @staticmethod
    def _get_provision_opt(provision):
        ret = []
        if provision is not None:
            possible_types = VNXProvisionEnum.get_all()
            if provision in possible_types:
                ret += VNXProvisionEnum.get_opt(provision)
            else:
                raise ValueError('not supported provisioning type: {}.'
                                 '  valid candidates: {}'
                                 .format(provision, possible_types))
        return ret

    @staticmethod
    def _get_tier_opt(tier):
        ret = []
        if tier is not None:
            possible_tiers = VNXTieringEnum.get_all()
            if tier in possible_tiers:
                ret += VNXTieringEnum.get_opt(tier)
            else:
                raise ValueError('not supported tiering type: {}.  '
                                 'valid candidates: {}'
                                 .format(tier, possible_tiers))
        return ret

    @command
    def create_pool_lun(self,
                        pool_name=None,
                        pool_id=None,
                        lun_name=None,
                        lun_id=None,
                        size_gb=1,
                        provision=None,
                        tier=None,
                        ignore_thresholds=None):

        cmd = ['lun', '-create', '-capacity', size_gb, '-sq', 'gb']
        cmd += self._get_pool_opt(pool_id, pool_name)
        cmd += self._get_lun_opt(lun_id, lun_name)
        cmd += self._get_provision_opt(provision)
        cmd += self._get_tier_opt(tier)
        if ignore_thresholds:
            cmd.append('-ignoreThresholds')
        return cmd

    @command
    def modify_lun(self,
                   lun_id=None,
                   lun_name=None,
                   new_name=None,
                   new_tier=None,
                   dedup=None):
        cmd = ['lun', '-modify']
        cmd += self._get_lun_opt(lun_id, lun_name)

        cmd += text_var('-newName', new_name)
        cmd += self._get_tier_opt(new_tier)

        if dedup is not None:
            dedup_op = 'on' if dedup else 'off'
            cmd += ['-deduplication', dedup_op]

        cmd.append('-o')
        return cmd

    @command
    def enable_compression(self, lun_id=None, rate=None, pool_id=None,
                           pool_name=None, ignore_thresholds=False):
        cmd = ['compression', '-on']
        cmd += int_var('-l', lun_id)
        cmd += int_var('-destPoolId', pool_id)
        cmd += text_var('-destPoolName', pool_name)
        cmd += enum_var('-rate', rate, VNXCompressionRate)
        if ignore_thresholds:
            cmd.append('-ignoreThresholds')
        cmd.append('-o')
        return cmd

    @command
    def disable_compression(self, lun_id, ignore_thresholds=False):
        cmd = ['compression', '-off']
        cmd += int_var('-l', lun_id)
        if ignore_thresholds:
            cmd.append('-ignoreThresholds')
        cmd.append('-o')
        return cmd

    @command
    def create_mount_point(self,
                           primary_lun_id=None,
                           primary_lun_name=None,
                           mount_point_name=None,
                           mount_point_id=None):
        cmd = 'lun -create -type snap'.split()
        cmd += self._get_primary_lun_opt(primary_lun_id, primary_lun_name)
        cmd += self._get_lun_opt(lun_id=mount_point_id,
                                 lun_name=mount_point_name)
        return cmd

    @command
    def attach_snap(self, snap_name, lun_id=None, lun_name=None):
        cmd = ['lun', '-attach']
        cmd += self._get_lun_opt(lun_id, lun_name)
        cmd += text_var('-snapName', snap_name)
        return cmd

    @command
    def detach_snap(self, lun_id=None, lun_name=None):
        cmd = ['lun', '-detach']
        cmd += self._get_lun_opt(lun_id, lun_name)
        cmd.append('-o')
        return cmd

    @command
    def delete_pool_lun(self,
                        lun_id=None,
                        lun_name=None,
                        delete_snapshots=False,
                        force_detach=False):
        cmd = 'lun -destroy'.split()
        cmd += self._get_lun_opt(lun_id, lun_name)

        if delete_snapshots:
            cmd.append('-destroySnapshots')

        if force_detach:
            cmd.append('-forceDetach')

        cmd.append('-o')
        return cmd

    @command
    def expand_pool_lun(self, new_size, lun_id=None, lun_name=None,
                        ignore_thresholds=False):
        cmd = ['lun', '-expand']
        cmd += self._get_lun_opt(lun_id, lun_name)
        cmd += int_var('-capacity', new_size)
        cmd += ['-sq', 'gb']
        if ignore_thresholds:
            cmd += ['-ignoreThresholds']
        cmd.append('-o')
        return cmd

    @command
    def migrate_lun(self, src_id, dst_id, rate=VNXMigrationRate.HIGH):
        cmd = ['migrate', '-start']
        cmd += int_var('-source', src_id)
        cmd += int_var('-dest', dst_id)
        cmd += enum_var('-rate', rate, VNXMigrationRate)
        cmd.append('-o')
        return cmd

    @command
    def get_migration_session(self, src_id=None):
        cmd = ['migrate', '-list']
        if src_id is not None:
            cmd += int_var('-source', src_id)
        return cmd

    @command
    def cancel_migrate_lun(self, src_id):
        if src_id is None:
            raise ValueError('source LUN id missing for cancel migration.')
        cmd = ['migrate', '-cancel']
        cmd += int_var('-source', src_id)
        cmd.append('-o')
        return cmd

    @command
    def create_sg(self, name):
        cmd = ['storagegroup', '-create']
        cmd += text_var('-gname', name)
        return cmd

    @command
    def sg_add_hlu(self, sg_name, hlu_id, alu_id):
        cmd = ['storagegroup', '-addhlu']
        cmd += int_var('-hlu', hlu_id)
        cmd += int_var('-alu', alu_id)
        cmd += text_var('-gname', sg_name)
        cmd.append('-o')
        return cmd

    @command
    def sg_delete_hlu(self, sg_name, hlu_id):
        cmd = ['storagegroup', '-removehlu']
        cmd += int_var('-hlu', hlu_id)
        cmd += text_var('-gname', sg_name)
        cmd.append('-o')
        return cmd

    @staticmethod
    def _sg_host_op(sg_name, host_name, op):
        cmd = ['storagegroup', op]
        cmd += text_var('-host', host_name)
        cmd += text_var('-gname', sg_name)
        cmd.append('-o')
        return cmd

    @command
    def sg_connect_host(self, sg_name, host_name):
        return self._sg_host_op(sg_name, host_name, '-connecthost')

    @command
    def sg_disconnect_host(self, sg_name, host_name):
        return self._sg_host_op(sg_name, host_name, '-disconnecthost')

    @command
    def config_iscsi_ip(self, sp, port_id, ip, netmask, gateway,
                        vport_id=None, vlan_id=None):
        if vport_id is None:
            vport_id = 0

        cmd = ['connection', '-setport', '-iscsi']
        cmd += ['-sp', VNXSPEnum.get_sp_index(sp)]
        cmd += int_var('-portid', port_id)
        cmd += int_var('-vportid', vport_id)
        cmd += int_var('-vlanid', vlan_id)
        cmd += text_var('-address', ip)
        cmd += text_var('-subnetmask', netmask)
        cmd += text_var('-gateway', gateway)
        cmd.append('-o')
        return cmd

    @command
    def delete_iscsi_ip(self, sp, port_id, vport_id=None):
        if vport_id is None:
            vport_id = 0

        cmd = ['connection', '-delport']
        cmd += ['-sp', VNXSPEnum.get_sp_index(sp)]
        cmd += int_var('-portid', port_id)
        cmd += int_var('-vportid', vport_id)
        cmd.append('-o')
        return cmd

    @command
    def set_path(self, sg_name, hba_uid, sp, port_id,
                 ip, host, vport_id=None):

        cmd = ['storagegroup', '-setpath']
        cmd += text_var('-gname', sg_name)
        cmd += text_var('-hbauid', hba_uid)
        cmd += ['-sp', VNXSPEnum.get_sp_index(sp)]
        cmd += int_var('-spport', port_id)
        cmd += int_var('-spvport', vport_id)
        cmd += text_var('-ip', ip)
        cmd += text_var('-host', host)
        cmd.append('-o')
        return cmd

    @command
    def delete_hba(self, hba_uid):
        return ['port', '-removeHBA', '-hbauid', hba_uid, '-o']

    @command
    def delete_sg(self, sg_name):
        cmd = ['storagegroup', '-destroy']
        cmd += text_var('-gname', sg_name)
        cmd.append('-o')
        return cmd

    @command
    def get_snap(self, name=None, res=None):
        cmd = ['snap', '-list']
        cmd += text_var('-id', name)
        cmd += int_var('-res', res)
        cmd.append('-detail')
        return cmd

    @command
    def create_snap(self, res_id, snap_name,
                    allow_rw=True, auto_delete=False, keep_for=None):
        cmd = ['snap', '-create']
        try:
            cmd += int_var('-res', res_id)
        except ValueError:
            # string type meaning cg name
            cmd += text_var('-res', res_id)
            cmd += ['-resType', 'CG']

        cmd += text_var('-name', snap_name)
        # -keepFor and -allowAutoDelete cannot co-exist
        if keep_for:
            cmd += text_var('-keepFor', keep_for)
        else:
            cmd += yes_no_var('-allowAutoDelete', auto_delete)
        cmd += yes_no_var('-allowReadWrite', allow_rw)

        return cmd

    @command
    def copy_snap(self, src_name, tgt_name,
                  ignore_migration_check=False,
                  ignore_dedup_check=False):
        cmd = ['snap', '-copy']
        cmd += text_var('-id', src_name)
        cmd += text_var('-name', tgt_name)
        if ignore_migration_check:
            cmd.append('-ignoreMigrationCheck')
        if ignore_dedup_check:
            cmd.append('-ignoreDeduplicationCheck')
        return cmd

    @command
    def modify_snap(self, name, new_name=None, desc=None,
                    auto_delete=None, allow_rw=None, keep_for=None):
        opt = []
        if new_name is not None and name != new_name:
            opt += text_var('-name', new_name)
        opt += text_var('-descr', desc)
        # -keepFor and -allowAutoDelete cannot co-exist
        if keep_for:
            opt += text_var('-keepFor', keep_for)
        else:
            opt += yes_no_var('-allowAutoDelete', auto_delete)
        opt += yes_no_var('-allowReadWrite', allow_rw)
        if len(opt) > 0:
            cmd = ['snap', '-modify', '-id', name] + opt
        else:
            cmd = []
        return cmd

    @command
    def delete_snap(self, snap_name):
        cmd = ['snap', '-destroy']
        cmd += text_var('-id', snap_name)
        cmd.append('-o')
        return cmd

    @staticmethod
    def _get_cg_member_repr(members):
        def member_converter(member):
            return six.text_type(check_int(member))

        return ','.join(map(member_converter, members))

    @command
    def create_cg(self, name, members=None, auto_delete=None):
        cmd = 'snap -group -create'.split()
        cmd += text_var('-name', name)
        cmd += yes_no_var('-allowSnapAutoDelete', auto_delete)

        if members is not None and len(members) > 0:
            cmd += ['-res', self._get_cg_member_repr(members)]

        return cmd

    @classmethod
    def _cg_member_op(cls, name, op, members):
        if len(members) == 0:
            cmd = []
            log.warn('no member to add to cg: {}'.format(name))
        else:
            cmd = 'snap -group {} -id'.format(op).split()
            cmd.append(name)
            cmd += ['-res', cls._get_cg_member_repr(members)]
        return cmd

    @command
    def add_cg_member(self, name, *members):
        return self._cg_member_op(name, '-addmember', members)

    @command
    def delete_cg_member(self, name, *members):
        return self._cg_member_op(name, '-rmmember', members)

    @command
    def replace_cg_member(self, name, *members):
        return self._cg_member_op(name, '-replmember', members)

    @command
    def delete_cg(self, name):
        cmd = 'snap -group -destroy'.split()
        cmd += text_var('-id', name)
        return cmd

    @command
    def get_ndu(self, name=None):
        cmd = 'ndu -list'.split()
        if name is not None:
            cmd += text_var('-name', name)
        return cmd

    @command
    def create_mirror_view(self, name, lun_id, use_write_intent_log=True):
        cmd = 'mirror -sync -create'.split()
        cmd += text_var('-name', name)
        cmd += int_var('-lun', lun_id)
        if use_write_intent_log:
            cmd.append('-usewriteintentlog')
        else:
            cmd.append('-nowriteintentlog')
        cmd.append('-o')
        return cmd

    @command
    def delete_mirror_view(self, name):
        cmd = 'mirror -sync -destroy'.split()
        cmd += text_var('-name', name)
        cmd.append('-o')
        return cmd

    @command
    def add_mirror_view_image(self, name, sp_ip, lun_id,
                              recovery_policy=VNXMirrorViewRecoveryPolicy.AUTO,
                              sync_rate=VNXMirrorViewSyncRate.HIGH):
        cmd = 'mirror -sync -addimage'.split()
        cmd += text_var('-name', name)
        cmd += text_var('-arrayhost', sp_ip)
        cmd += int_var('-lun', lun_id)
        cmd += VNXMirrorViewRecoveryPolicy.get_opt(recovery_policy)
        cmd += enum_var('-syncrate', sync_rate, VNXMirrorViewSyncRate)
        return cmd

    @staticmethod
    def _mirror_view_image_op(op, name, image_id):
        cmd = ['mirror', '-sync', op]
        cmd += text_var('-name', name)
        cmd += text_var('-imageuid', image_id)
        cmd.append('-o')
        return cmd

    @command
    def delete_mirror_view_image(self, name, image_id):
        return self._mirror_view_image_op(
            '-removeimage', name, image_id)

    @command
    def mirror_view_fracture_image(self, name, image_id):
        return self._mirror_view_image_op(
            '-fractureimage', name, image_id)

    @command
    def mirror_view_sync_image(self, name, image_id):
        return self._mirror_view_image_op(
            '-syncimage', name, image_id)

    @command
    def mirror_view_promote_image(self, name, image_id):
        return self._mirror_view_image_op(
            '-promoteimage', name, image_id)

    @command
    def get_mirror_view(self, name=None):
        cmd = 'mirror -sync -list'.split()
        cmd += text_var('-name', name)
        return cmd

    @command
    def get_disk(self, bus=None, enclosure=None, disk=None):
        cmd = ['getdisk']
        if bus is not None and enclosure is not None and disk is not None:
            disk_index = '{}_{}_{}'.format(bus, enclosure, disk)
            cmd.append(disk_index)
        elif bus is None and enclosure is None and disk is None:
            pass
        else:
            raise ValueError('you must specify bus, enclosure and disk id'
                             ' together to retrieve a specified disk.')
        return cmd

    @command
    def get_rg(self, rg_id=None):
        cmd = ['getrg']
        cmd += int_var(None, rg_id)
        return cmd

    @command
    def create_rg(self, disks=None, rg_id=None, raid_type=None):
        if rg_id is None:
            raise ValueError('RAID group id not specified.')
        if not disks:
            raise ValueError('disks not specified.')
        if raid_type is None:
            raid_type = VNXRaidType.RAID5
        cmd = ['createrg']
        cmd += int_var(None, rg_id)
        cmd += disks
        cmd += enum_var('-raidtype', raid_type, VNXRaidType)
        cmd.append('-o')
        return cmd

    @command
    def delete_rg(self, rg_id):
        cmd = ['removerg']
        cmd += int_var(None, rg_id)
        return cmd

    @command
    def create_pool(self, name, disks, raid_type=None):
        cmd = ['storagepool', '-create', '-disks']
        cmd += disks
        cmd += enum_var('-rtype', raid_type, VNXPoolRaidType)
        cmd += text_var('-name', name)
        cmd.append('-skiprules')
        return cmd

    @command
    def delete_pool(self, name=None, pool_id=None):
        cmd = ['storagepool', '-destroy']
        cmd += self._get_id_name_opt(pool_id, name)
        cmd.append('-o')
        return cmd

    @command
    def modify_storage_pool(self, name=None, pool_id=None,
                            new_name=None):
        cmd = ['storagepool', '-modify']
        cmd += self._get_id_name_opt(pool_id, name)
        cmd += text_var('-newName', new_name)
        cmd.append('-o')
        return cmd

    @command
    def sp_network_status(self, sp):
        sp = VNXSPEnum.get_sp_index(sp)
        return 'networkadmin -get -sp {} -all'.format(sp).split()

    @duel_command
    def delete_disk(self, disk_index):
        return 'cru_on_off -messner {} 0'.format(disk_index).split()

    @duel_command
    def install_disk(self, disk_index):
        return 'cru_on_off -messner {} 1'.format(disk_index).split()

    @command
    def ping_node(self, address, sp, port_id, vport_id=None, packet_size=None,
                  count=None, timeout=None, delay=None):
        if vport_id is None:
            vport_id = 0
        cmd = ['connection', '-pingnode']
        sp = VNXSPEnum.get_sp_index(sp)
        cmd += text_var('-sp', sp)
        cmd += int_var('-portid', port_id)
        cmd += int_var('-vportid', vport_id)
        cmd += text_var('-address', address)
        cmd += int_var('-packetSize', packet_size)
        cmd += int_var('-count', count)
        cmd += int_var('-timeout', timeout)
        cmd += int_var('-delay', delay)
        return cmd

    @command
    def list_user(self, name=None):
        cmd = ['security', '-list']
        cmd += text_var('-user', name)
        cmd.append('-type')
        return cmd

    @command
    def add_user(self, name, password, scope=None, role=None):
        if scope is None:
            scope = VNXUserScopeEnum.GLOBAL
        if role is None:
            role = VNXUserRoleEnum.ADMIN

        cmd = ['security', '-adduser']
        cmd += text_var('-user', name)
        cmd += text_var('-password', password)
        cmd += enum_var('-scope', scope, VNXUserScopeEnum)
        cmd += enum_var('-role', role, VNXUserRoleEnum)
        cmd.append('-o')
        return cmd

    @command
    def delete_user(self, name, scope=None):
        if scope is None:
            scope = VNXUserScopeEnum.GLOBAL

        cmd = ['security', '-rmuser']
        cmd += text_var('-user', name)
        cmd += enum_var('-scope', scope, VNXUserScopeEnum)
        cmd.append('-o')
        return cmd

    @command
    def get_array_name(self):
        return ['arrayname']

    @command
    def set_array_name(self, new_name):
        cmd = text_var('arrayname', new_name)
        cmd.append('-o')
        return cmd

    @command
    def set_stats(self, enable=None):
        cmd = ['setstats']
        if enable is not None:
            if enable:
                cmd.append('-on')
            else:
                cmd.append('-off')
        return cmd

    @property
    def ip(self):
        return self._heart_beat.get_alive_sp_ip()

    @retry(on_error=ex.VNXSPDownError)
    def execute(self, params, ip=None):
        if params is not None and len(params) > 0:
            if ip is None:
                ip = self.ip
            output = self.do(ip, params)
        else:
            log.info('no command to execute.  return empty.')
            output = ''
        return output

    @retry(on_error=ex.VNXDropConnectionError)
    def do(self, ip, params):
        cmd = self._heart_beat.get_cmd_prefix(ip) + params
        return self._heart_beat.execute_cmd(ip, cmd)

    def execute_dual(self, params):
        ip_list = self._heart_beat.get_all_alive_sps_ip()
        if not self._heart_beat.is_all_sps_alive():
            raise ex.VNXSPDownError(
                'this command requires all sps available.  '
                'currently alive ips are: {}.'.format(ip_list))

        output = []
        if params is not None and len(params) > 0:
            pool = ThreadPool(len(ip_list))
            output = pool.map(lambda ip: self.do(ip, params), ip_list)
        return tuple(output)

    def set_system_version(self, version):
        self._system_version = version

    @property
    def system_version(self):
        clz = storops.vnx.resource.system.VNXAgent
        if self._system_version is None:
            self._system_version = clz(self).revision
        return self._system_version
