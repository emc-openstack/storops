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
import re
from itertools import chain

import six

from storops import exception as ex
from storops.lib import converter
from storops.unity.enums import HostTypeEnum, HostInitiatorTypeEnum
from storops.unity.resource import UnityResource, UnityResourceList, \
    UnityAttributeResource
from storops.unity.resource.tenant import UnityTenant

__author__ = 'Cedric Zhuang'

log = logging.getLogger(__name__)


class UnityBlockHostAccess(UnityAttributeResource):
    pass


class UnityBlockHostAccessList(UnityResourceList):
    @classmethod
    def get_resource_class(cls):
        return UnityBlockHostAccess


class UnitySnapHostAccess(UnityAttributeResource):
    pass


class UnitySnapHostAccessList(UnityResourceList):
    @classmethod
    def get_resource_class(cls):
        return UnitySnapHostAccess


DUMMY_LUN_NAME = 'storops_dummy_lun'


class UnityHost(UnityResource):
    @classmethod
    def get_nested_properties(cls):
        return (
            'fc_host_initiators.initiator_id',
            'fc_host_initiators.paths.is_logged_in',
            'fc_host_initiators.paths.fc_port.wwn',
            'iscsi_host_initiators.initiator_id',
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
            address = converter.url_to_host(_id)
            netmask = converter.url_to_mask(_id)
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
                host.add_ip_port(address, netmask=netmask)
                ret = host
            else:
                ret = None
        else:
            ret = cls.get(cli=cli, _id=_id)
        return ret

    def _get_host_lun(self, lun=None, snap=None, hlu=None):
        lun_id = lun.id if lun is not None else None
        snap_id = snap.id if snap is not None else None
        hlu_no = hlu if hlu is not None else None

        ret = UnityHostLunList.get(self._cli, host=self.id,
                                   lun=lun_id, snap=snap_id, hlu=hlu_no)

        if len(ret) != 1:
            msg = ('Found {num} host luns attached to this host. '
                   'Filter: lun={lun_id}, snap={snap_id}, '
                   'hlu={hlu_no}.').format(num=len(ret), lun_id=lun_id,
                                           snap_id=snap_id, hlu_no=hlu_no)
            log.debug(msg)

        # Need filter again for the hlu of LUN, excluding the hlu of snap.
        if lun_id and snap_id is None:
            ret = list(filter(lambda x: x.snap is None, ret))

        return ret

    def detach(self, lun_or_snap):
        return lun_or_snap.detach_from(self)

    def detach_alu(self, lun):
        log.warn('Method detach_alu is deprecated. Use detach instead.')
        return lun.detach_from(self)

    def _create_attach_dummy_lun(self):
        import storops.unity.resource.lun as lun_module
        import storops.unity.resource.pool as pool_module
        lun_list = lun_module.UnityLunList.get(self._cli, name=DUMMY_LUN_NAME)
        if not lun_list:
            try:
                pool_list = pool_module.UnityPoolList.get(self._cli)
                dummy_lun = pool_list[0].create_lun(lun_name=DUMMY_LUN_NAME)
            except Exception as err:
                # Ignore all errors of creating dummy lun.
                log.warn('Failed to create dummy lun. Message: {}'.format(err))
                dummy_lun = None
        else:
            dummy_lun = lun_list[0]

        if dummy_lun:
            try:
                dummy_lun.attach_to(self)
            except ex.UnityResourceAlreadyAttachedError:
                pass
            except Exception as err:
                # Ignore all errors of attaching dummy lun.
                log.warn('Failed to attach dummy lun. Message: {}'.format(err))

    def attach(self, lun_or_snap, skip_hlu_0=False):
        if self.has_hlu(lun_or_snap):
            raise ex.UnityResourceAlreadyAttachedError()

        if skip_hlu_0:
            hlu_0 = self._get_host_lun(hlu=0)
            if not hlu_0:
                log.debug(
                    'Try to skip the hlu number 0 by attaching a dummy lun.')
                self._create_attach_dummy_lun()

        try:
            lun_or_snap.attach_to(self)
            self.update()
            hlu = self.get_hlu(lun_or_snap)
        except ex.UnityAttachExceedLimitError:
            # The number of luns exceeds system limit
            raise
        except:
            # other attach error, remove this lun if already attached
            self.detach(lun_or_snap)
            raise

        return hlu

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
        except:
            # other attach error, remove this lun if already attached
            self.detach_alu(lun)
            raise

        return hlu

    def has_hlu(self, lun_or_snap):
        hlu = self.get_hlu(lun_or_snap)
        return hlu is not None

    def has_alu(self, lun):
        log.warn('Method has_alu is deprecated. Use has_hlu instead.')
        alu = self.get_hlu(lun)
        if alu is None:
            return False
        else:
            return True

    def get_hlu(self, resource, cg_member=None):
        import storops.unity.resource.lun as lun_module
        import storops.unity.resource.snap as snap_module
        which = None
        if isinstance(resource, lun_module.UnityLun):
            which = self._get_host_lun(lun=resource)
        elif isinstance(resource, snap_module.UnitySnap):
            if cg_member is not None:
                resource = resource.get_member_snap(cg_member)
                which = self._get_host_lun(lun=cg_member, snap=resource)
            else:
                which = self._get_host_lun(snap=resource)
        if not which:
            log.debug('Resource(LUN or Snap) {} is not attached to host {}'
                      .format(resource.name, self.name))
            return None
        return which[0].hlu

    def add_initiator(self, uid, force_create=True, **kwargs):
        initiators = UnityHostInitiatorList.get(cli=self._cli,
                                                initiator_id=uid)

        if not initiators:
            # Set the ISCSI or FC type
            if re.match("(\w{2}:){15}\w{2}", uid, re.I):
                uid_type = HostInitiatorTypeEnum.FC
            elif re.match("iqn.\d{4}-\d{2}.\w+.\w+:\d+:[A-F0-9]+", uid, re.I):
                # iqn.yyyy-mm.<reversed domain name>[:identifier] )
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
                # remove from the host initiator list first,
                # otherwise delete initiator will not work
                item.modify(None)
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

    @property
    def ip_list(self):
        if self.host_ip_ports:
            ret = [port.address for port in self.host_ip_ports]
        else:
            ret = []
        return ret


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
