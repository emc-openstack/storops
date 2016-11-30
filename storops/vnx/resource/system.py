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

import time

import functools
from retryz import retry

from storops.exception import VNXDiskUsedError, raise_if_err, \
    VNXSetArrayNameError
from storops.lib.common import daemon, instance_cache, clear_instance_cache
from storops.lib.resource import ResourceList, ResourceListCollection
from storops.vnx.resource.host import VNXHost
from storops.vnx.resource.metric import VNXStats
from storops.vnx.resource.nfs_share import VNXNfsShare
from storops.vnx.resource.fs_snap import VNXFsSnap
from storops.vnx.resource.mover import VNXMover
from storops.vnx.resource.vdm import VNXVdm
from storops.vnx.resource.cifs_share import VNXCifsShare
from storops.vnx.resource.cifs_server import VNXCifsServer
from storops.vnx.resource.nas_pool import VNXNasPool
from storops.vnx.nas_client import VNXNasClient
from storops.vnx.resource.fs import VNXFileSystem
from storops.vnx.resource.mirror_view import VNXMirrorView
from storops.vnx.enums import VNXPortType, VNXPoolRaidType, VNXSPEnum
from storops.vnx.block_cli import CliClient
from storops.vnx.resource.block_pool import VNXPool, VNXPoolFeature
from storops.vnx.resource.cg import VNXConsistencyGroup
from storops.vnx.resource.disk import VNXDisk, VNXDiskList
from storops.vnx.resource.security import VNXBlockUser
from storops.vnx.resource.vnx_domain import VNXDomainMemberList, \
    VNXNetworkAdmin, VNXDomainNodeList, VNXStorageProcessor, \
    VNXStorageProcessorList
from storops.vnx.resource.lun import VNXLun
from storops.vnx.resource.migration import VNXMigrationSession
from storops.vnx.resource.ndu import VNXNdu, VNXNduList
from storops.vnx.resource.port import VNXConnectionPort, VNXSPPort
from storops.vnx.resource import VNXCliResource
from storops.vnx.resource.rg import VNXRaidGroup
from storops.vnx.resource.sg import VNXStorageGroup
from storops.vnx.resource.snap import VNXSnap
from storops.vnx.resource.capacity import VNXCapacity

__author__ = 'Cedric Zhuang'

log = logging.getLogger(__name__)


class VNXSystem(VNXCliResource):
    """ The system class for VNX

    This class act as the entry point for VNX system.
    Various VNX resources could be retrieved with methods/properties
    of this class.
    """

    def __init__(self, ip=None,
                 username=None, password=None, scope=0, sec_file=None,
                 timeout=None,
                 heartbeat_interval=None,
                 naviseccli=None,
                 file_username=None, file_password=None):
        """ initialize a `VNXSystem` instance

        The `VNXSystem` instance act as a entry point for all
        VNX resources.

        :param ip: ip of one block sp
        :param username: username for block system
        :param password: password for the specified block user
        :param scope: scope of the specified block user
        :param sec_file: security file used by naviseccli
        :param timeout: naviseccli command timeout
        :param heartbeat_interval: heartbeat interval used to check the
        alive of sp.  Set to 0 if heart beat is not required.
        :param naviseccli: binary location of naviseccli in your host.
        :param file_username: username for control station login, default to
        username
        :param file_password: password for control station login, default to
        password
        :return: vnx system instance
        """
        super(VNXSystem, self).__init__()
        self._ip = ip
        self._username = username
        self._password = password
        self._scope = scope
        self._sec_file = sec_file
        self._timeout = timeout
        self._hb_interval = heartbeat_interval
        self._naviseccli = naviseccli

        self._file_username = file_username
        self._file_password = file_password

        self._cli = self._init_block_cli()

        if heartbeat_interval:
            daemon(self.update_nodes_ip)

    def _init_block_cli(self):
        return CliClient(
            self._ip,
            self._username, self._password, self._scope, self._sec_file,
            self._timeout, heartbeat_interval=self._hb_interval,
            naviseccli=self._naviseccli)

    def _init_file_cli(self):
        return VNXNasClient(self.control_station_ip,
                            self._file_username,
                            self._file_password)

    def __getstate__(self):
        d = {'ip': self._ip, 'username': self._username,
             'password': self._password, 'scope': self._scope,
             'sec_file': self._sec_file, 'naviseccli': self._naviseccli}
        return d

    def __setstate__(self, state):
        self.__init__(heartbeat_interval=0, **state)

    def __getinitargs__(self):
        # Seems not used by pickle
        return (self._ip, self._username, self._password, self._scope,
                self._sec_file, None, None, self._naviseccli)

    @property
    @instance_cache
    def _file_cli(self):
        return self._init_file_cli()

    @property
    @instance_cache
    def _ndu_list(self):
        ret = VNXNduList(self._cli)
        ret.with_no_poll()
        return ret

    @property
    @instance_cache
    def name(self):
        inst = VNXArrayName(self._cli)
        return inst.name

    @name.setter
    @clear_instance_cache
    def name(self, new_name):
        inst = VNXArrayName(self._cli)
        inst.set_name(new_name)

    def set_naviseccli(self, cli_binary):
        self._cli.set_binary(cli_binary)

    def set_block_credential(self,
                             username=None, password=None, scope=None,
                             sec_file=None):
        self._cli.set_credential(username, password, scope, sec_file)

    def update_nodes_ip(self):
        # do not use the `control_station_ip` property to avoid self loop.
        self._cli.set_ip(self.spa_ip, self.spb_ip, self._get_cs_ip())

    @clear_instance_cache
    def update(self, data=None):
        super(VNXSystem, self).update(data)
        self.update_nodes_ip()

    @property
    def heartbeat(self):
        return self._cli.heartbeat

    @property
    @instance_cache
    def spa_ip(self):
        return VNXNetworkAdmin.get_spa_ip(self._cli)

    @property
    @instance_cache
    def spa(self):
        return VNXStorageProcessor(self._cli, VNXSPEnum.SP_A, self.spa_ip)

    @property
    @instance_cache
    def spb(self):
        return VNXStorageProcessor(self._cli, VNXSPEnum.SP_B, self.spb_ip)

    def get_sp(self):
        return VNXStorageProcessorList(
            VNXStorageProcessor(self._cli, VNXSPEnum.SP_A, self.spa_ip),
            VNXStorageProcessor(self._cli, VNXSPEnum.SP_B, self.spb_ip))

    @property
    @instance_cache
    def spb_ip(self):
        return VNXNetworkAdmin.get_spb_ip(self._cli)

    @property
    def alive_sp_ip(self):
        return self.heartbeat.get_alive_sp_ip()

    @property
    @instance_cache
    def control_station_ip(self):
        return self._get_cs_ip()

    def _get_cs_ip(self):
        return VNXDomainNodeList.get_cs_ip(self.serial, self._cli)

    @property
    def domain(self):
        return VNXDomainMemberList(self._cli)

    def _get_raw_resource(self):
        return self._cli.get_agent(poll=self.poll)

    def get_pool_feature(self, poll=False):
        feature = VNXPoolFeature(self._cli)
        return self._update_poll(feature, poll)

    def get_pool(self, name=None, pool_id=None, system_lun_list=None):
        return VNXPool.get(pool_id=pool_id, name=name, cli=self._cli,
                           system_lun_list=system_lun_list)

    def get_lun(self, lun_id=None, name=None, lun_type=None):
        return VNXLun.get(self._cli, lun_id=lun_id, name=name,
                          lun_type=lun_type)

    def get_cg(self, name=None):
        return VNXConsistencyGroup.get(self._cli, name)

    def get_sg(self, name=None, system_lun_list=None):
        return VNXStorageGroup.get(self._cli, name,
                                   system_lun_list=system_lun_list)

    def get_snap(self, name=None):
        return VNXSnap.get(self._cli, name)

    def get_migration_session(self, src_lun=None):
        return VNXMigrationSession.get(self._cli, src_lun)

    def get_ndu(self, name=None):
        return VNXNdu.get(self._cli, name)

    def get_connection_port(self, sp=None, port_id=None, vport_id=None):
        return VNXConnectionPort.get(self._cli, sp, port_id, vport_id)

    @staticmethod
    def _update_poll(obj, poll):
        if obj is not None:
            obj.poll = poll
        return obj

    def get_sp_port(self, sp=None, port_id=None, poll=False):
        ret = VNXSPPort.get(self._cli, sp, port_id)
        return self._update_poll(ret, poll)

    def get_fc_port(self, sp=None, port_id=None, poll=False):
        ret = VNXSPPort.get(self._cli,
                            sp=sp,
                            port_id=port_id,
                            port_type=VNXPortType.FC)
        return self._update_poll(ret, poll)

    def get_iscsi_port(self, sp=None, port_id=None, vport_id=None,
                       has_ip=None, poll=False):
        ret = VNXConnectionPort.get(self._cli,
                                    sp=sp,
                                    port_id=port_id,
                                    vport_id=vport_id,
                                    port_type=VNXPortType.ISCSI,
                                    has_ip=has_ip)
        return self._update_poll(ret, poll)

    def get_fcoe_port(self, sp=None, port_id=None, vport_id=None, poll=False):
        ret = VNXConnectionPort.get(self._cli,
                                    sp=sp,
                                    port_id=port_id,
                                    vport_id=vport_id,
                                    port_type=VNXPortType.FCOE)

        return self._update_poll(ret, poll)

    def delete_snap(self, name):
        self._delete_resource(VNXSnap(name, self._cli))

    def create_sg(self, name):
        return VNXStorageGroup.create(name, self._cli)

    def delete_sg(self, name):
        self._delete_resource(VNXStorageGroup(name, self._cli))

    def create_cg(self, name, members=None):
        return VNXConsistencyGroup.create(self._cli, name=name,
                                          members=members)

    def delete_cg(self, name):
        self._delete_resource(VNXConsistencyGroup(name, self._cli))

    def delete_lun(self, name):
        self._delete_resource(VNXLun(name=name, cli=self._cli))

    def get_disk(self, disk_index=None):
        return VNXDisk.get(self._cli, disk_index)

    def get_available_disks(self):
        pool_feature = VNXPoolFeature(self._cli)
        pool_feature.poll = self.poll
        disks = pool_feature.available_disks
        if disks:
            disks.poll = self.poll
        else:
            disks = VNXDiskList(cli=self._cli, disk_indices='N/A')
        return disks

    def delete_disk(self, disk_index):
        self._delete_resource(VNXDisk(disk_index, self._cli))

    def install_disk(self, disk_index):
        disk = VNXDisk(disk_index, self._cli)
        disk.install()

    def get_rg(self, rg_id=None):
        return VNXRaidGroup.get(self._cli, rg_id)

    def create_rg(self, rg_id, disks, raid_type=None):
        return VNXRaidGroup.create(self._cli, rg_id, disks, raid_type)

    def delete_rg(self, rg_id):
        self._delete_resource(VNXRaidGroup(rg_id, self._cli))

    def create_pool(self, name, disks=None, raid_type=None):
        @retry(on_error=VNXDiskUsedError)
        def create_with_default_disks():
            _disks = self.get_available_disks()
            disk_count = VNXPoolRaidType.parse(raid_type).min_disk_requirement
            _disks.same_disks(disk_count)
            return VNXPool.create(self._cli, name, _disks, raid_type)

        if raid_type is None:
            raid_type = VNXPoolRaidType.RAID5
        if disks is None:
            ret = create_with_default_disks()
        else:
            ret = VNXPool.create(self._cli, name, disks, raid_type)

        return ret

    def _delete_resource(self, resource):
        resource.poll = self.poll
        resource.delete()

    def delete_pool(self, name=None, pool_id=None):
        self._delete_resource(VNXPool(pool_id, name, self._cli))

    def stop_heart_beat(self):
        self._cli.heartbeat.stop()

    def is_compression_enabled(self):
        return self._ndu_list.is_compression_enabled()

    def is_dedup_enabled(self):
        return self._ndu_list.is_dedup_enabled()

    def is_snap_enabled(self):
        return self._ndu_list.is_snap_enabled()

    def is_mirror_view_async_enabled(self):
        return self._ndu_list.is_mirror_view_async_enabled()

    def is_mirror_view_sync_enabled(self):
        return self._ndu_list.is_mirror_view_sync_enabled()

    def is_mirror_view_enabled(self):
        return self._ndu_list.is_mirror_view_enabled()

    def is_thin_enabled(self):
        return self._ndu_list.is_thin_enabled()

    def is_sancopy_enabled(self):
        return self._ndu_list.is_sancopy_enabled()

    def is_auto_tiering_enabled(self):
        return self._ndu_list.is_auto_tiering_enabled()

    def is_fast_cache_enabled(self):
        return self._ndu_list.is_fast_cache_enabled()

    def delete_hba(self, hba_uid):
        return VNXSPPort.delete_hba(self._cli, hba_uid)

    def get_block_user(self, name=None):
        return VNXBlockUser.get(cli=self._cli, name=name)

    def create_block_user(self, name, password, scope=None, role=None):
        return VNXBlockUser.create(self._cli, name, password, scope, role)

    def get_mirror_view(self, name=None):
        return VNXMirrorView.get(self._cli, name)

    def create_mirror_view(self, name, src_lun, use_write_intent_log=True):
        return VNXMirrorView.create(self._cli, name, src_lun,
                                    use_write_intent_log)

    def get_host(self, name=None):
        return VNXHost.get(self._cli, name)

    def get_capacity(self):
        return VNXCapacity.get(cli=self._cli)

    def get_file_system(self, name=None, fs_id=None):
        return VNXFileSystem.get(cli=self._file_cli, name=name, fs_id=fs_id)

    def get_nas_pool(self, name=None, pool_id=None):
        return VNXNasPool.get(cli=self._file_cli, name=name, pool_id=pool_id)

    def get_cifs_server(self, name=None, mover_id=None, is_vdm=None):
        return VNXCifsServer.get(cli=self._file_cli, name=name,
                                 mover_id=mover_id, is_vdm=is_vdm)

    def create_cifs_server(self, name, mover_id=None, is_vdm=False,
                           workgroup=None, domain=None,
                           interfaces=None, alias_name=None,
                           local_admin_password=None):
        return VNXCifsServer.create(
            cli=self._file_cli, name=name, mover_id=mover_id, is_vdm=is_vdm,
            workgroup=workgroup, domain=domain, interfaces=interfaces,
            alias_name=alias_name, local_admin_password=local_admin_password)

    def get_cifs_share(self, name=None, mover=None, server_name=None):
        return VNXCifsShare.get(
            self._file_cli, name=name, mover=mover, server_name=server_name)

    def get_file_system_snap(self, name=None, snap_id=None):
        return VNXFsSnap.get(cli=self._file_cli, name=name, snap_id=snap_id)

    def get_mover(self, name=None, mover_id=None, is_vdm=False):
        if is_vdm:
            ret = VNXVdm.get(cli=self._file_cli, name=name, vdm_id=mover_id)
        else:
            ret = VNXMover.get(cli=self._file_cli, name=name,
                               mover_id=mover_id)
        return ret

    def get_nfs_share(self, mover=None, path=None):
        return VNXNfsShare.get(cli=self._file_cli, mover=mover, path=path)

    def _default_rsc_list_with_perf_stats(self):
        sps = self.get_sp()
        lun_list = self.get_lun()
        disks = self.get_disk()
        sp_ports = self.get_sp_port()
        pools = self.get_pool(system_lun_list=lun_list)
        sgs = self.get_sg(system_lun_list=lun_list)
        ret = (sps, lun_list, disks, sp_ports, pools, sgs)

        for resource_list in ret:
            resource_list.with_no_poll()
        return ret

    def get_rsc_list_2(self, rsc_clz_list=None):
        """get the list of resource list to collect based on clz list

        :param rsc_clz_list: the list of classes to collect
        :return: filtered list of resource list,
                 like [VNXLunList(), VNXDiskList()]
        """
        rsc_list_2 = self._default_rsc_list_with_perf_stats()
        if rsc_clz_list is None:
            rsc_clz_list = ResourceList.get_rsc_clz_list(rsc_list_2)

        return [rsc_list
                for rsc_list in rsc_list_2
                if rsc_list.get_resource_class() in rsc_clz_list]

    def collect_perf_record(self, clz_list):
        log.info('start collecting counters of vnx {}.'.format(self._ip))
        start = time.time()
        rsc_list_2 = self.get_rsc_list_2(clz_list)
        record = ResourceListCollection(rsc_list_2)
        record.update()
        log.info('end collecting counters of vnx {}.  collection took '
                 '{:.3f} seconds.'.format(self._ip, time.time() - start))
        return record

    def enable_perf_stats(self, rsc_clz_list=None):
        VNXStats.get(self._cli).enable_stats()
        f = functools.partial(self.collect_perf_record, clz_list=rsc_clz_list)
        self._cli.enable_perf_metric(60, f, rsc_clz_list)
        return self.get_rsc_list_2(rsc_clz_list)

    def disable_perf_stats(self, disable_counter_collection=False):
        if disable_counter_collection:
            VNXStats.get(self._cli).disable_stats()
        self._cli.disable_perf_metric()

    def is_perf_stats_enabled(self):
        return self._cli.is_perf_metric_enabled()

    def is_counter_collection_enabled(self):
        return VNXStats.get(self._cli).is_enabled()

    def enable_persist_perf_stats(self):
        rsc_list = self._default_rsc_list_with_perf_stats()
        self._cli.persist_perf_stats(rsc_list)

    def disable_persist_perf_stats(self):
        self._cli.persist_perf_stats(None)

    def is_perf_stats_persisted(self):
        return self._cli.is_perf_stats_persisted()

    def __del__(self):
        del self._cli


class VNXArrayName(VNXCliResource):
    def __init__(self, cli=None):
        super(VNXArrayName, self).__init__()
        self._cli = cli

    def _get_raw_resource(self):
        return self._cli.get_array_name()

    def set_name(self, new_name):
        out = self._cli.set_array_name(new_name)
        raise_if_err(out, default=VNXSetArrayNameError)


class VNXAgent(VNXCliResource):
    def __init__(self, cli=None):
        super(VNXAgent, self).__init__()
        self._cli = cli

    def _get_raw_resource(self):
        return self._cli.get_agent(poll=self.poll)
