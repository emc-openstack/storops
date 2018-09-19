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
import random
from itertools import chain

import six

from retryz import retry

from storops import exception as ex
from storops.lib import common
from storops.lib import converter
from storops.lib.version import version
from storops.unity.enums import HostTypeEnum, HostInitiatorTypeEnum
from storops.unity.resource import UnityResource, UnityResourceList, \
    UnityAttributeResource
from storops.unity.resource.tenant import UnityTenant

# from storops.unity.resource import lun

__author__ = 'Cedric Zhuang'

log = logging.getLogger(__name__)


class UnityBlockHostAccess(UnityAttributeResource):
    pass


class UnityBlockHostAccessList(UnityResourceList):
    @classmethod
    def get_resource_class(cls):
        return UnityBlockHostAccess

    def get_host_id(self):
        return [access.host.id for access in self]


class UnitySnapHostAccess(UnityAttributeResource):
    pass


class UnitySnapHostAccessList(UnityResourceList):
    @classmethod
    def get_resource_class(cls):
        return UnitySnapHostAccess


DUMMY_LUN_NAME = 'storops_dummy_lun'
MAX_HLU_NUMBER = 255  # Unity supports 16381 but uses 255 here due to GH-238


class UnityHost(UnityResource):
    @classmethod
    def get_nested_properties(cls):
        return (
            'fc_host_initiators.initiator_id',
            'fc_host_initiators.paths.initiator.type',
            'fc_host_initiators.paths.is_logged_in',
            'fc_host_initiators.paths.fc_port.wwn',
            'iscsi_host_initiators.initiator_id',
            'hostLUNs.hlu',
            'hostLUNs.lun.id',
            'hostLUNs.lun.name',
            'hostLUNs.snap.id',
            'hostIPPorts.address',
        )

    @classmethod
    def create(cls, cli, name, host_type=None, desc=None, os=None,
               tenant=None):
        if host_type is None:
            host_type = HostTypeEnum.HOST_MANUAL

        if tenant is not None:
            tenant = UnityTenant.get(cli, tenant)

        resp = cli.post(cls().resource_class,
                        type=host_type,
                        name=name,
                        description=desc,
                        osType=os,
                        tenant=tenant)
        resp.raise_if_err()
        return cls(_id=resp.resource_id, cli=cli)

    @classmethod
    def get_host(cls, cli, _id, force_create=False, tenant=None):
        if isinstance(_id, six.string_types) and ('.' in _id or ':' in _id):
            # it looks like an ip address, find or create the host
            address, prefix, netmask = converter.parse_host_address(_id)
            ports = UnityHostIpPortList(cli=cli, address=address)
            # since tenant is not supported by all kinds of system. So we
            # should avoid send the tenant request if tenant is None
            tenant = None if tenant is None else UnityTenant.get(cli, tenant)
            ports = [port for port in ports if port.host.tenant == tenant]

            if len(ports) == 1:
                ret = ports[0].host
            elif force_create:
                log.info('cannot find an existing host with ip {}.  '
                         'create a new host "{}" to attach it.'
                         .format(address, address))
                host_type = (HostTypeEnum.SUBNET if netmask
                             else HostTypeEnum.HOST_MANUAL)
                host_name = ('{}_{}'.format(address, netmask) if netmask
                             else address)
                host = cls.create(cli, host_name, host_type=host_type,
                                  tenant=tenant)
                if ':' in address:  # ipv6
                    host.add_ip_port(address, v6_prefix_length=prefix)
                else:  # ipv4
                    host.add_ip_port(address, netmask=netmask)
                ret = host.update()
            else:
                ret = None
        else:
            ret = cls.get(cli=cli, _id=_id)
        return ret

    def modify(self, name=None, desc=None, os=None):
        req_body = self._cli.make_body(
            name=name,
            description=desc,
            osType=os,
        )
        resp = self._cli.modify(self.resource_class,
                                self.get_id(), **req_body)
        resp.raise_if_err()
        return self

    def modify_host_lun(self, lun_or_snap, new_hlu):
        host_lun = self.get_host_lun(lun_or_snap)
        if not host_lun:
            raise ex.UnityResourceNotAttachedError
        self._modify_hlu(host_lun, new_hlu)

    def _modify_hlu(self, host_lun, new_hlu):
        resp = self._cli.action(self.resource_class, self.get_id(),
                                'modifyHostLUNs',
                                hostLunModifyList=[{'hostLUN': host_lun,
                                                    'hlu': new_hlu}])
        resp.raise_if_err()

    def _get_host_luns(self, lun=None, snap=None, hlu=None):
        ret = self.host_luns

        if ret is None:
            log.debug('No lun attached to the host: {}.'.format(self.name))
            return []
        else:
            lun_id = lun.id if lun is not None else None
            snap_id = snap.id if snap is not None else None
            hlu_no = hlu if hlu is not None else None

            if lun_id is not None:
                ret = filter(lambda x: x.lun and x.lun.get_id() == lun_id, ret)

            if snap_id is None:
                # get rid of the `Snapshot` type of host access
                ret = filter(lambda x: x.snap is None, ret)
            else:
                ret = filter(lambda x: x.snap and x.snap.get_id() == snap_id,
                             ret)

            if hlu_no is not None:
                ret = filter(lambda x: x.hlu == hlu_no, ret)

            ret = list(ret)
            msg = ('Found {num} host luns attached to this host. '
                   'Filter: lun={lun_id}, snap={snap_id}, '
                   'hlu={hlu_no}.').format(num=len(ret), lun_id=lun_id,
                                           snap_id=snap_id, hlu_no=hlu_no)
            log.debug(msg)

            return ret

    def detach(self, lun_or_snap):
        if self.host_luns:
            # To detach the `dummy luns` which are attached via legacy storops.
            dummy_lun_ids = [lun.get_id() for lun in self.host_luns.lun
                             if lun.name == DUMMY_LUN_NAME]
            if dummy_lun_ids:
                from storops.unity.resource.lun import UnityLun
                dummy_lun = UnityLun(cli=self._cli, _id=dummy_lun_ids[0])
                try:
                    dummy_lun.delete(None)
                except ex.UnityException:
                    pass
        return lun_or_snap.detach_from(self)

    def detach_alu(self, lun):
        log.warn('Method detach_alu is deprecated. Use detach instead.')
        return lun.detach_from(self)

    def _random_hlu_number(self):
        existing_hlus = [host_lun.hlu for host_lun in self._get_host_luns()]
        try:
            candidate = random.choice(
                list(hlu for hlu in range(1, MAX_HLU_NUMBER + 1)
                     if hlu not in existing_hlus))
            log.debug('Random choose hlu: {hlu} from range [1, {max}].'.format(
                hlu=candidate, max=MAX_HLU_NUMBER))
            return candidate
        except IndexError:
            raise ex.UnityNoHluAvailableError(
                'No hlu available. Random choose hlu from range [1, {max}] '
                'but not in existing hlu: {exist}'.format(exist=existing_hlus,
                                                          max=MAX_HLU_NUMBER))

    @version('<4.4.0')  # noqa
    @retry(limit=5, on_error=ex.UnityHluNumberInUseError)
    def _attach_with_retry(self, lun_or_snap, skip_hlu_0):
        # Before 4.4.0 (Osprey), it didn't support to pass in hlu when
        # attaching.
        lun_or_snap.attach_to(self)
        self.update()
        host_lun = self.get_host_lun(lun_or_snap)
        if skip_hlu_0 and host_lun.hlu == 0:
            candidate_hlu = self._random_hlu_number()
            self._modify_hlu(host_lun, candidate_hlu)
            return candidate_hlu
        else:
            return host_lun.hlu

    @version('>=4.4.0')  # noqa
    @retry(limit=5, on_error=ex.UnityHluNumberInUseError)
    def _attach_with_retry(self, lun_or_snap, skip_hlu_0):
        # From 4.4.0 (Osprey), it supported to pass in hlu when attaching LUN,
        # but not when attaching snap.
        from storops.unity.resource.lun import UnityLun as _UnityLun
        if skip_hlu_0 and isinstance(lun_or_snap, _UnityLun):
            candidate_hlu = self._random_hlu_number()
            lun_or_snap.attach_to(self, hlu=candidate_hlu)
            self.update()
            return candidate_hlu
        else:
            lun_or_snap.attach_to(self)
            self.update()
            host_lun = self.get_host_lun(lun_or_snap)
            return host_lun.hlu

    def attach(self, lun_or_snap, skip_hlu_0=False):
        """ Attaches lun, snap or member snap of cg snap to host.

        Don't pass cg snapshot in as `lun_or_snap`.

        :param lun_or_snap: the lun, snap, or a member snap of cg snap
        :param skip_hlu_0: whether to skip hlu 0
        :return: the hlu number
        """

        # `UnityResourceAlreadyAttachedError` check was removed due to there
        # is a host cache existing in Cinder driver. If the lun was attached to
        # the host and the info was stored in the cache, wrong hlu would be
        # returned.
        # And attaching a lun to a host twice would success, if Cinder retry
        # triggers another attachment of same lun to the host, the cost would
        # be one more rest request of `modifyLun` and one for host instance
        # query.
        try:
            return self._attach_with_retry(lun_or_snap, skip_hlu_0)

        except ex.SystemAPINotSupported:
            # Attaching snap to host not support before 4.1.
            raise
        except ex.UnityAttachExceedLimitError:
            # The number of luns exceeds system limit
            raise
        except:  # noqa
            # other attach error, remove this lun if already attached
            self.detach(lun_or_snap)
            raise

    def attach_alu(self, lun):
        log.warn('Method attach_alu is deprecated. Use attach instead.')
        if self.has_alu(lun):
            raise ex.UnityAluAlreadyAttachedError()

        try:
            lun.attach_to(self)
            self.update()
            hlu = self.get_hlu(lun)
        except ex.UnityAttachAluExceedLimitError:
            # The number of luns exceeds system limit
            raise
        except:  # noqa
            # other attach error, remove this lun if already attached
            self.detach_alu(lun)
            raise

        return hlu

    def has_hlu(self, lun_or_snap, cg_member=None):
        """Returns True if `lun_or_snap` is attached to the host.

        :param lun_or_snap: can be lun, lun snap, cg snap or a member snap of
            cg snap.
        :param cg_member: the member lun of cg if `lun_or_snap` is cg snap.
        :return: True - if `lun_or_snap` is attached, otherwise False.
        """
        hlu = self.get_hlu(lun_or_snap, cg_member=cg_member)
        return hlu is not None

    def has_alu(self, lun):
        log.warn('Method has_alu is deprecated. Use has_hlu instead.')
        alu = self.get_hlu(lun)
        if alu is None:
            return False
        else:
            return True

    def get_host_lun(self, lun_or_snap, cg_member=None):
        """Gets the host lun of a lun, lun snap, cg snap or a member snap of cg
        snap.

        :param lun_or_snap: can be lun, lun snap, cg snap or a member snap of
            cg snap.
        :param cg_member: the member lun of cg if `lun_or_snap` is cg snap.
        :return: the host lun object.
        """
        import storops.unity.resource.lun as lun_module
        import storops.unity.resource.snap as snap_module
        which = None
        if isinstance(lun_or_snap, lun_module.UnityLun):
            which = self._get_host_luns(lun=lun_or_snap)
        elif isinstance(lun_or_snap, snap_module.UnitySnap):
            if lun_or_snap.is_cg_snap():
                if cg_member is None:
                    log.debug('None host lun for CG snap {}. '
                              'Use its member snap instead or pass in '
                              'cg_member.'.format(lun_or_snap.id))
                    return None
                lun_or_snap = lun_or_snap.get_member_snap(cg_member)
                which = self._get_host_luns(lun=cg_member, snap=lun_or_snap)
            else:
                which = self._get_host_luns(snap=lun_or_snap)
        if not which:
            log.debug('Resource(LUN or Snap) {} is not attached to host {}'
                      .format(lun_or_snap.name, self.name))
            return None
        return which[0]

    def get_hlu(self, resource, cg_member=None):
        """Gets the hlu number of a lun, lun snap, cg snap or a member snap of
        cg snap.

        :param resource: can be lun, lun snap, cg snap or a member snap of cg
            snap.
        :param cg_member: the member lun of cg if `lun_or_snap` is cg snap.
        :return: the hlu number.
        """
        host_lun = self.get_host_lun(resource, cg_member=cg_member)
        return host_lun if host_lun is None else host_lun.hlu

    def add_initiator(self, uid, force_create=True, **kwargs):
        initiators = UnityHostInitiatorList.get(cli=self._cli,
                                                initiator_id=uid)

        if not initiators:
            # Set the ISCSI or FC type
            if common.is_fc_uid(uid):
                uid_type = HostInitiatorTypeEnum.FC
            elif common.is_iscsi_uid(uid):
                uid_type = HostInitiatorTypeEnum.ISCSI
            else:
                uid_type = HostInitiatorTypeEnum.UNKNOWN

            if force_create:
                initiator = UnityHostInitiator.create(self._cli, uid,
                                                      self, uid_type, **kwargs)
            else:
                raise ex.UnityHostInitiatorNotFoundError(
                    'name {} not found under host {}.'.format(uid, self.name))
        else:
            initiator = initiators.first_item
            log.debug('initiator {} is existed in unity system.'.format(uid))

        initiator.modify(self)
        return initiator.update()

    def delete_initiator(self, uid):
        initiators = []
        if self.fc_host_initiators:
            initiators += self.fc_host_initiators
        if self.iscsi_host_initiators:
            initiators += self.iscsi_host_initiators
        for item in initiators:
            if item.initiator_id == uid:
                resp = item.delete()
                resp.raise_if_err()
                break
        else:
            raise ex.UnityHostInitiatorNotFoundError(
                'name {} not found under host {}.'.format(uid, self.name))

        return resp

    def add_ip_port(self, address, netmask=None, v6_prefix_length=None,
                    is_ignored=None):
        return UnityHostIpPort.create(self._cli,
                                      host=self,
                                      address=address,
                                      netmask=netmask,
                                      v6_prefix_length=v6_prefix_length,
                                      is_ignored=is_ignored)

    def delete_ip_port(self, address):
        for ip_port in self.host_ip_ports:
            if ip_port.address == address:
                resp = ip_port.delete()
                break
        else:
            resp = None
            log.info('ip {} not found under host {}.'
                     .format(address, self.name))
        return resp

    def update_initiators(self, iqns=None, wwns=None):
        """Primarily for puppet-unity use.

        Update the iSCSI and FC initiators if needed.
        """
        # First get current iqns
        iqns = set(iqns) if iqns else set()
        current_iqns = set()
        if self.iscsi_host_initiators:
            current_iqns = {initiator.initiator_id
                            for initiator in self.iscsi_host_initiators}
        # Then get current wwns
        wwns = set(wwns) if wwns else set()
        current_wwns = set()
        if self.fc_host_initiators:
            current_wwns = {initiator.initiator_id
                            for initiator in self.fc_host_initiators}
        updater = UnityHostInitiatorUpdater(
            self, current_iqns | current_wwns, iqns | wwns)
        return updater.update()

    @property
    def ip_list(self):
        if self.host_ip_ports:
            ret = [port.address for port in self.host_ip_ports]
        else:
            ret = []
        return ret


class UnityHostInitiatorUpdater(object):
    def __init__(self, host, current, new_initiators):
        self.host = host
        self.current = current
        self.new_initiators = new_initiators

    def compute(self):
        to_add = self.new_initiators - self.current
        to_delete = self.current - self.new_initiators
        return to_add, to_delete

    def update(self):
        to_add, to_delete = self.compute()
        for a in to_add:
            self.host.add_initiator(a)
        for d in to_delete:
            self.host.delete_initiator(d)
        return len(to_add | to_delete)


class UnityHostList(UnityResourceList):
    @classmethod
    def get_resource_class(cls):
        return UnityHost

    @property
    def ip_list(self):
        return list(chain.from_iterable([host.ip_list for host in self]))


class UnityHostContainer(UnityResource):
    pass


class UnityHostContainerList(UnityResourceList):
    @classmethod
    def get_resource_class(cls):
        return UnityHostContainer


class UnityHostInitiator(UnityResource):
    @classmethod
    def create(cls, cli, uid, host, type, is_ignored=None,
               chap_user=None, chap_secret=None, chap_secret_type=None):

        if type == HostInitiatorTypeEnum.ISCSI:
            resp = cli.post(cls().resource_class,
                            host=host,
                            initiatorType=type,
                            initiatorWWNorIqn=uid,
                            chapUser=chap_user,
                            chapSecret=chap_secret,
                            chapSecretType=chap_secret_type,
                            isIgnored=is_ignored)
        elif type == HostInitiatorTypeEnum.FC:
            resp = cli.post(cls().resource_class,
                            host=host,
                            initiatorType=type,
                            initiatorWWNorIqn=uid,
                            isIgnored=is_ignored)
        else:
            raise ex.UnityHostInitiatorUnknownType(
                '{} parameter is unknown type'.format(type))

        resp.raise_if_err()
        return cls(_id=resp.resource_id, cli=cli)

    def modify(self, host, is_ignored=None, chap_user=None,
               chap_secret=None, chap_secret_type=None):
        req_body = {'host': host, 'isIgnored': is_ignored}

        if self.type == HostInitiatorTypeEnum.ISCSI:
            req_body['chapUser'] = chap_user
            req_body['chapSecret'] = chap_secret
            req_body['chapSecretType'] = chap_secret_type
        # end if

        resp = self._cli.modify(self.resource_class,
                                self.get_id(), **req_body)
        resp.raise_if_err()
        return resp


class UnityHostInitiatorList(UnityResourceList):
    @classmethod
    def get_resource_class(cls):
        return UnityHostInitiator


class UnityHostInitiatorPath(UnityResource):
    pass


class UnityHostInitiatorPathList(UnityResourceList):
    def __init__(self, cli=None, is_logged_in=None, **filters):
        super(UnityHostInitiatorPathList, self).__init__(cli, **filters)
        self._is_logged_in = None
        self._set_filter(is_logged_in)

    def _set_filter(self, is_logged_in=None, **kwargs):
        self._is_logged_in = is_logged_in

    def _filter(self, initiator_path):
        ret = True
        if self._is_logged_in is not None:
            ret &= (initiator_path.initiator.type == HostInitiatorTypeEnum.FC
                    and initiator_path.is_logged_in == self._is_logged_in)
        return ret

    @classmethod
    def get_resource_class(cls):
        return UnityHostInitiatorPath


class UnityHostIpPort(UnityResource):
    @classmethod
    def create(cls, cli, host, address, netmask=None, v6_prefix_length=None,
               is_ignored=None):
        host = UnityHost.get(cli=cli, _id=host)

        resp = cli.post(cls().resource_class,
                        host=host,
                        address=address,
                        netmask=netmask,
                        v6PrefixLength=v6_prefix_length,
                        isIgnored=is_ignored)
        resp.raise_if_err()
        return cls(_id=resp.resource_id, cli=cli)


class UnityHostIpPortList(UnityResourceList):
    @classmethod
    def get_resource_class(cls):
        return UnityHostIpPort


class UnityHostLun(UnityResource):
    pass


class UnityHostLunList(UnityResourceList):
    @classmethod
    def get_resource_class(cls):
        return UnityHostLun
