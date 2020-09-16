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

from storops.unity.resource import UnityResource, UnityResourceList

__author__ = 'Yong Huang'

LOG = logging.getLogger(__name__)


class UnityMoveSession(UnityResource):
    @classmethod
    def create(cls, cli, source_storage_resource, destination_pool,
               source_member_lun=None, is_dest_thin=None,
               is_data_reduction_applied=None, is_advanced_dedup_applied=None,
               priority=None):
        req_body = cls._compose_move_session_parameter(
            cli, source_storage_resource=source_storage_resource,
            destination_pool=destination_pool,
            source_member_lun=source_member_lun,
            is_dest_thin=is_dest_thin,
            is_data_reduction_applied=is_data_reduction_applied,
            is_advanced_dedup_applied=is_advanced_dedup_applied,
            priority=priority)
        resp = cli.post(cls().resource_class, **req_body)
        resp.raise_if_err()
        move_session = cls.get(cli, resp.resource_id)
        return move_session

    def modify(self, cli, priority=None):
        req_body = self._compose_move_session_parameter(cli,
                                                        priority=priority)
        resp = self.action('modify', **req_body)
        resp.raise_if_err()
        return resp

    def cancel(self):
        resp = self.action('cancel')
        resp.raise_if_err()
        return resp

    @staticmethod
    def _compose_move_session_parameter(cli, source_storage_resource=None,
                                        destination_pool=None,
                                        source_member_lun=None,
                                        is_dest_thin=None,
                                        is_data_reduction_applied=None,
                                        is_advanced_dedup_applied=None,
                                        priority=None):
        req_body = cli.make_body(
            sourceStorageResource=source_storage_resource,
            destinationPool=destination_pool,
            sourceMemberLun=source_member_lun,
            isDestThin=is_dest_thin,
            isDataReductionApplied=is_data_reduction_applied,
            isAdvancedDedupApplied=is_advanced_dedup_applied,
            priority=priority)
        return req_body


class UnityMoveSessionList(UnityResourceList):
    @classmethod
    def get_resource_class(cls):
        return UnityMoveSession
