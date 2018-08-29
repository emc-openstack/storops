# coding=utf-8
# Copyright (c) 2017 Dell Inc. or its subsidiaries.
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

from persistqueue import PDict

from storops import exception
from storops.lib.tasks import PQueue
from storops.unity.enums import ThinCloneActionEnum

log = logging.getLogger(__name__)


class TCHelper(object):
    _tc_cache = {}
    _gc_candidates = {}
    _gc_background = None
    _GC_INTERVAL = 3600

    @staticmethod
    def set_up(persist_path):
        log.debug('Set up TCHelper, persist path: %s.', persist_path)
        TCHelper._tc_cache = PDict(persist_path, 'tc_cache',
                                   multithreading=True)
        TCHelper._gc_candidates = PDict(persist_path, 'gc_candidates',
                                        multithreading=True)
        TCHelper._gc_background = PQueue(persist_path,
                                         interval=TCHelper._GC_INTERVAL)
        TCHelper._gc_background.start()

    @staticmethod
    def clean_up():
        TCHelper._gc_background.stop()
        TCHelper._gc_background = None
        TCHelper._tc_cache = {}
        TCHelper._gc_candidates = {}

    @staticmethod
    def _compose_thin_clone(cli, name=None, snap=None, description=None,
                            io_limit_policy=None):
        return cli.make_body(name=name, snap=snap, description=description,
                             lunParameters=cli.make_body(
                                 ioLimitParameters=cli.make_body(
                                     ioLimitPolicy=io_limit_policy)))

    @staticmethod
    def thin_clone(cli, lun_or_snap, name, io_limit_policy=None,
                   description=None):
        from storops.unity.resource.lun import UnityLun
        from storops.unity.resource.storage_resource import \
            UnityStorageResource

        snap_to_tc = None  # None means to create a temp snap for thin clone
        if isinstance(lun_or_snap, UnityLun):
            tc_node = lun_or_snap
        else:
            # `lun_or_snap` is an UnitySnap, use it for thin clone directly.
            tc_node = lun_or_snap.lun
            snap_to_tc = lun_or_snap

        _id = lun_or_snap.get_id()
        if _id in TCHelper._tc_cache:
            tc_node = TCHelper._tc_cache[_id]
            snap_to_tc = None
            log.debug('Found %(id)s in TCHelper cache. Use it: %(cache)s as '
                      'the base to thin clone.',
                      {'id': _id, 'cache': tc_node})

        if snap_to_tc is None:
            snap_to_tc = tc_node.create_snap(name='tmp-{}'.format(name),
                                             is_auto_delete=False)
            log.debug('Temp snap used for thin clone is created: %s.',
                      snap_to_tc.get_id())

        req_body = TCHelper._compose_thin_clone(
            cli, name=name, snap=snap_to_tc, description=description,
            io_limit_policy=io_limit_policy)
        resp = cli.action(UnityStorageResource().resource_class,
                          tc_node.get_id(), 'createLunThinClone', **req_body)
        if snap_to_tc != lun_or_snap:
            # Delete the temp snap
            snap_to_tc.delete()
        resp.raise_if_err()
        return UnityLun(cli=cli, _id=resp.resource_id)

    @staticmethod
    def _gc_resources(lun_or_snap):
        lun_or_snap_id = lun_or_snap.get_id()
        if lun_or_snap_id in TCHelper._tc_cache:
            base_lun = TCHelper._tc_cache[lun_or_snap_id]
            log.debug('Found %(id)s in TCHelper cache. Base lun: %(base)s.',
                      {'id': lun_or_snap_id, 'base': base_lun.get_id()})
            TCHelper._gc_base_lun(base_lun)

    @staticmethod
    def _gc_base_lun(base_lun):
        TCHelper._gc_candidates[base_lun.get_id()] = base_lun.get_id()
        log.debug('Put base lun: %s to gc candidates list.',
                  base_lun.get_id())
        if TCHelper._gc_background is not None:
            TCHelper._gc_background.put(TCHelper._delete_base_lun,
                                        base_lun=base_lun)
            log.debug('Put base lun: %s to background gc process.',
                      base_lun.get_id())
        else:
            log.warning('LUN will not be deleted because background GC thread'
                        'is not running. Invoke TCHelper.set_up first.')

    @staticmethod
    def _delete_thin_clone(thin_clone):
        try:
            TCHelper._delete_base_lun(thin_clone.family_base_lun)
        except exception.UnityBaseHasThinCloneError:
            log.info('Failed to delete base lun %s due to it still has other '
                     'thin clones. The background gc will delete it later.',
                     thin_clone.family_base_lun.get_id())
        except exception.UnityTCSnapUnderDestroyError:
            log.info('Failed to delete base lun %s due to the underlying '
                     'snapshot for thin clone still under destroying. '
                     'The background gc will delete it later.',
                     thin_clone.family_base_lun.get_id())

    @classmethod
    def _delete_base_lun(cls, base_lun):
        if base_lun.get_id() in TCHelper._gc_candidates:
            if base_lun.family_clone_count > 0:
                # Raising exception will let the job re-enter the background gc
                # queue
                raise exception.UnityBaseHasThinCloneError()

            base_lun.delete()
            del TCHelper._gc_candidates[base_lun.get_id()]
            log.debug('Base lun %s deleted. And removed from gc candidates.',
                      base_lun.get_id())

    @staticmethod
    def _update_cache(lun_or_snap, action_enum, *args):
        lun_or_snap_id = lun_or_snap.get_id()
        if action_enum in (ThinCloneActionEnum.DD_COPY,):
            TCHelper._gc_resources(lun_or_snap)
            log.debug('Garbage collected for base lun of %(id)s, triggered by '
                      '%(action)s action.',
                      {'id': lun_or_snap_id, 'action': action_enum.name})
            TCHelper._tc_cache[lun_or_snap_id] = args[0]
            log.debug('Cache updated for base lun of %(id)s to %(new)s.',
                      {'id': lun_or_snap_id, 'new': args[0]})
        elif action_enum in (ThinCloneActionEnum.LUN_ATTACH,):
            TCHelper._gc_resources(lun_or_snap)
            log.debug('Garbage collected for base lun of %(id)s, triggered by '
                      '%(action)s action.',
                      {'id': lun_or_snap_id, 'action': action_enum.name})
            if lun_or_snap_id in TCHelper._tc_cache:
                del TCHelper._tc_cache[lun_or_snap_id]
                log.debug('Removed base lun of %s from cache.', lun_or_snap_id)
        elif action_enum in (ThinCloneActionEnum.BASE_LUN_DELETE,):
            # `lun_or_snap` is a base lun here.
            TCHelper._gc_base_lun(lun_or_snap)
            log.debug('Garbage collected for base lun of %(id)s, triggered by '
                      '%(action)s action.',
                      {'id': lun_or_snap_id, 'action': action_enum.name})

    @staticmethod
    def notify(lun_or_snap, action_enum, *args):
        if action_enum in (ThinCloneActionEnum.TC_DELETE,):
            log.debug('Try to delete base lun of %s actively.',
                      lun_or_snap.get_id())
            # Delete the base lun of thin-clone actively.
            TCHelper._delete_thin_clone(lun_or_snap)

        TCHelper._update_cache(lun_or_snap, action_enum, *args)
