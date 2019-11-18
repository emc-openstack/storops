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

from storops.unity.resource import UnityResource, UnityResourceList, \
    UnityAttributeResource

__author__ = 'Ryan Liang'

log = logging.getLogger(__name__)


class UnityLunMemberReplication(UnityAttributeResource):
    @staticmethod
    def to_embedded(src_lun_id=None, dst_lun_id=None, src_status=None,
                    network_status=None, dst_status=None):
        return {'srcLunId': src_lun_id, 'dstLunId': dst_lun_id,
                'srcStatus': src_status, 'dstStatus': dst_status,
                'networkStatus': network_status}


class UnityLunMemberReplicationList(UnityResourceList):
    @classmethod
    def get_resource_class(cls):
        return UnityLunMemberReplication


class UnitySnapReplicationPolicy(UnityAttributeResource):
    @staticmethod
    def to_embedded(is_replicating_snaps=None,
                    is_retention_same_as_source=None,
                    is_auto_delete=None, retention_duration=None):
        return {'isReplicatingSnaps': is_replicating_snaps,
                'isRetentionSameAsSource': is_retention_same_as_source,
                'isAutoDelete': is_auto_delete,
                'retentionDuration': retention_duration}


class UnityResourceConfig(UnityAttributeResource):
    @staticmethod
    def to_embedded(pool_id=None, is_thin_enabled=None,
                    is_deduplication_enabled=None, is_compression_enabled=None,
                    is_backup_only=None, size=None, tiering_policy=None,
                    request_id=None, src_id=None, name=None, default_sp=None,
                    replication_resource_type=None):
        """
        Constructs an embeded object of `UnityResourceConfig`.

        :param pool_id: storage pool of the resource.
        :param is_thin_enabled: is thin type or not.
        :param is_deduplication_enabled: is deduplication enabled or not.
        :param is_compression_enabled: is in-line compression (ILC) enabled or
            not.
        :param is_backup_only: is backup only or not.
        :param size: size of the resource.
        :param tiering_policy: `TieringPolicyEnum` value. Tiering policy
            for the resource.
        :param request_id: unique request ID for the configuration.
        :param src_id: storage resource if it already exists.
        :param name: name of the storage resource.
        :param default_sp: `NodeEnum` value. Default storage processor for
            the resource.
        :param replication_resource_type: `ReplicationEndpointResourceTypeEnum`
            value. Replication resource type.
        :return:
        """
        return {'poolId': pool_id, 'isThinEnabled': is_thin_enabled,
                'isDeduplicationEnabled': is_deduplication_enabled,
                'isCompressionEnabled': is_compression_enabled,
                'isBackupOnly': is_backup_only, 'size': size,
                'tieringPolicy': tiering_policy, 'requestId': request_id,
                'srcId': src_id, 'name': name, 'defaultSP': default_sp,
                'replicationResourceType': replication_resource_type}


class UnityResourceInfo(UnityAttributeResource):
    @staticmethod
    def to_embedded(res_id=None, name=None, system=None):
        """
        Constructs an embeded object of `UnityResourceInfo`.

        :param res_id: identifier of the resource.
        :param name: name of the resource.
        :param system: system on which the resource exists.
        :return:
        """
        return {'resId': res_id, 'name': name, 'system': system}


class UnityReplicationSession(UnityResource):

    @classmethod
    def get_nested_properties(cls):
        return (
            'remoteSystem.name',
        )

    @classmethod
    def create(cls, cli, src_resource_id, dst_resource_id,
               max_time_out_of_sync, name=None, members=None,
               auto_initiate=None, hourly_snap_replication_policy=None,
               daily_snap_replication_policy=None,
               replicate_existing_snaps=None, remote_system=None,
               src_spa_interface=None, src_spb_interface=None,
               dst_spa_interface=None, dst_spb_interface=None):
        """
        Creates a replication session.

        :param cli: the rest cli.
        :param src_resource_id: id of the replication source, could be
            lun/fs/cg.
        :param dst_resource_id: id of the replication destination.
        :param max_time_out_of_sync: maximum time to wait before syncing the
            source and destination. Value `-1` means the automatic sync is not
            performed. `0` means it is a sync replication.
        :param name: name of the replication.
        :param members: list of `UnityLunMemberReplication` object. If
            `src_resource` is cg, `lunMemberReplication` list need to pass in
            to this parameter as member lun pairing between source and
            destination cg.
        :param auto_initiate: indicates whether to perform the first
            replication sync automatically.
            True - perform the first replication sync automatically.
            False - perform the first replication sync manually.
        :param hourly_snap_replication_policy: `UnitySnapReplicationPolicy`
            object. The policy for replicating hourly scheduled snaps of the
            source resource.
        :param daily_snap_replication_policy: `UnitySnapReplicationPolicy`
            object. The policy for replicating daily scheduled snaps of the
            source resource.
        :param replicate_existing_snaps: indicates whether or not to replicate
            snapshots already existing on the resource.
        :param remote_system: `UnityRemoteSystem` object. The remote system of
            remote replication.
        :param src_spa_interface: `UnityRemoteInterface` object. The
            replication interface for source SPA.
        :param src_spb_interface: `UnityRemoteInterface` object. The
            replication interface for source SPB.
        :param dst_spa_interface: `UnityRemoteInterface` object. The
            replication interface for destination SPA.
        :param dst_spb_interface: `UnityRemoteInterface` object. The
            replication interface for destination SPB.
        :return: the newly created replication session.
        """

        req_body = cli.make_body(
            srcResourceId=src_resource_id, dstResourceId=dst_resource_id,
            maxTimeOutOfSync=max_time_out_of_sync, members=members,
            autoInitiate=auto_initiate, name=name,
            hourlySnapReplicationPolicy=hourly_snap_replication_policy,
            dailySnapReplicationPolicy=daily_snap_replication_policy,
            replicateExistingSnaps=replicate_existing_snaps,
            remoteSystem=remote_system,
            srcSPAInterface=src_spa_interface,
            srcSPBInterface=src_spb_interface,
            dstSPAInterface=dst_spa_interface,
            dstSPBInterface=dst_spb_interface)

        resp = cli.post(cls().resource_class, **req_body)
        resp.raise_if_err()
        return cls.get(cli, resp.resource_id)

    @classmethod
    def create_with_dst_resource_provisioning(
            cls, cli, src_resource_id, dst_resource_config,
            max_time_out_of_sync, name=None, remote_system=None,
            src_spa_interface=None, src_spb_interface=None,
            dst_spa_interface=None, dst_spb_interface=None,
            dst_resource_element_configs=None, auto_initiate=None,
            hourly_snap_replication_policy=None,
            daily_snap_replication_policy=None, replicate_existing_snaps=None,
            no_async_snap_replication=None,
    ):
        """
        Create a replication session along with destination resource
        provisioning.

        :param cli: the rest cli.
        :param src_resource_id: id of the replication source, could be
            lun/fs/cg.
        :param dst_resource_config: `UnityResourceConfig` object. The user
            chosen config for destination resource provisioning. `pool_id` and
            `size` are required for creation.
        :param max_time_out_of_sync: maximum time to wait before syncing the
            source and destination. Value `-1` means the automatic sync is not
            performed. `0` means it is a sync replication.
        :param name: name of the replication.
        :param remote_system: `UnityRemoteSystem` object. The remote system to
            which the replication is being configured. When not specified, it
            defaults to local system.
        :param src_spa_interface: `UnityRemoteInterface` object. The
            replication interface for source SPA.
        :param src_spb_interface: `UnityRemoteInterface` object. The
            replication interface for source SPB.
        :param dst_spa_interface: `UnityRemoteInterface` object. The
            replication interface for destination SPA.
        :param dst_spb_interface: `UnityRemoteInterface` object. The
            replication interface for destination SPB.
        :param dst_resource_element_configs: List of `UnityResourceConfig`
            objects. The user chose config for each of the member element of
            the destination resource.
        :param auto_initiate: indicates whether to perform the first
            replication sync automatically.
            True - perform the first replication sync automatically.
            False - perform the first replication sync manually.
        :param hourly_snap_replication_policy: `UnitySnapReplicationPolicy`
            object. The policy for replicating hourly scheduled snaps of the
            source resource.
        :param daily_snap_replication_policy: `UnitySnapReplicationPolicy`
            object. The policy for replicating daily scheduled snaps of the
            source resource.
        :param replicate_existing_snaps: indicates whether or not to replicate
            snapshots already existing on the resource.
        :param no_async_snap_replication: whether or not snap replication is
            enabled in asynchronous replication session. When enabled, snap
            replication is controlled by snap replication policy setting or
            user action.
        :return: the newly created replication session.
        """

        req_body = cli.make_body(
            srcResourceId=src_resource_id,
            dstResourceConfig=dst_resource_config,
            maxTimeOutOfSync=max_time_out_of_sync,
            name=name, remoteSystem=remote_system,
            srcSPAInterface=src_spa_interface,
            srcSPBInterface=src_spb_interface,
            dstSPAInterface=dst_spa_interface,
            dstSPBInterface=dst_spb_interface,
            dstResourceElementConfigs=dst_resource_element_configs,
            autoInitiate=auto_initiate,
            hourlySnapReplicationPolicy=hourly_snap_replication_policy,
            dailySnapReplicationPolicy=daily_snap_replication_policy,
            replicateExistingSnaps=replicate_existing_snaps,
            noAsyncSnapReplication=no_async_snap_replication,
        )

        resp = cli.type_action(
            cls().resource_class,
            'createReplicationSessionWDestResProvisioning',
            **req_body)
        resp.raise_if_err()
        # response is like:
        # "content": {
        #     "id": {
        #         "id": "42949676351_FNM00150600267_xxxx"
        #     }
        session_resp = resp.first_content['id']
        return cls.get(cli, _id=session_resp['id'])

    def modify(self, max_time_out_of_sync=None, name=None,
               hourly_snap_replication_policy=None,
               daily_snap_replication_policy=None,
               src_spa_interface=None, src_spb_interface=None,
               dst_spa_interface=None, dst_spb_interface=None):
        """
        Modifies properties of a replication session.

        :param max_time_out_of_sync: same as the one in `create` method.
        :param name: same as the one in `create` method.
        :param hourly_snap_replication_policy: same as the one in `create`
            method.
        :param daily_snap_replication_policy: same as the one in `create`
            method.
        :param src_spa_interface: same as the one in `create` method.
        :param src_spb_interface: same as the one in `create` method.
        :param dst_spa_interface: same as the one in `create` method.
        :param dst_spb_interface: same as the one in `create` method.
        """
        req_body = self._cli.make_body(
            maxTimeOutOfSync=max_time_out_of_sync, name=name,
            hourlySnapReplicationPolicy=hourly_snap_replication_policy,
            dailySnapReplicationPolicy=daily_snap_replication_policy,
            srcSPAInterface=src_spa_interface,
            srcSPBInterface=src_spb_interface,
            dstSPAInterface=dst_spa_interface,
            dstSPBInterface=dst_spb_interface)

        resp = self.action('modify', **req_body)
        resp.raise_if_err()
        return resp

    def resume(self, force_full_copy=None,
               src_spa_interface=None, src_spb_interface=None,
               dst_spa_interface=None, dst_spb_interface=None):
        """
        Resumes a replication session.

        This can be applied on replication session when it's operational status
        is reported as Failed over, or Paused.

        :param force_full_copy: needed when replication session goes out of
            sync due to a fault.
            True - replicate all data.
            False - replicate changed data only.
        :param src_spa_interface: same as the one in `create` method.
        :param src_spb_interface: same as the one in `create` method.
        :param dst_spa_interface: same as the one in `create` method.
        :param dst_spb_interface: same as the one in `create` method.
        """
        req_body = self._cli.make_body(forceFullCopy=force_full_copy,
                                       srcSPAInterface=src_spa_interface,
                                       srcSPBInterface=src_spb_interface,
                                       dstSPAInterface=dst_spa_interface,
                                       dstSPBInterface=dst_spb_interface)

        resp = self.action('resume', **req_body)
        resp.raise_if_err()
        return resp

    def pause(self):
        """
        Pauses a replication session.

        This can be applied on replication session when in `OK` state.
        """
        resp = self.action('pause')
        resp.raise_if_err()
        return resp

    def sync(self):
        """
        Syncs a replication session.

        This can be applied to initiate a sync on demand independent of type of
        replication session - auto or manual sync.
        """
        resp = self.action('sync')
        resp.raise_if_err()
        return resp

    def failover(self, sync=None, force=None):
        """
        Fails over a replication session.

        :param sync: True - sync the source and destination resources before
            failing over the asynchronous replication session or keep them in
            sync after failing over the synchronous replication session.
            False - don't sync.
        :param force: True - skip pre-checks on file system(s) replication
            sessions of a NAS server when a replication failover is issued from
            the source NAS server.
            False - don't skip pre-checks.
        """
        req_body = self._cli.make_body(sync=sync, force=force)
        resp = self.action('failover', **req_body)
        resp.raise_if_err()
        return resp

    def failback(self, force_full_copy=None):
        """
        Fails back a replication session.

        This can be applied on a replication session that is failed over. Fail
        back will synchronize the changes done to original destination back to
        original source site and will restore the original direction of
        session.

        :param force_full_copy: indicates whether to sync back all data from
            the destination SP to the source SP during the failback session.
            True - Sync back all data.
            False - Sync back changed data only.
        """
        req_body = self._cli.make_body(forceFullCopy=force_full_copy)
        resp = self.action('failback', **req_body)
        resp.raise_if_err()
        return resp


class UnityReplicationSessionList(UnityResourceList):
    @classmethod
    def get_resource_class(cls):
        return UnityReplicationSession

    @staticmethod
    def filter_by_source_destination(src_system_name, src_resource_id,
                                     dst_system_name, dst_resource_id):
        UnityReplicationSessionList.get()
