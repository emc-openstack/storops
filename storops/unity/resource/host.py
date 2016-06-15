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

__author__ = 'Cedric Zhuang'

log = logging.getLogger(__name__)


class UnityBlockHostAccess(UnityAttributeResource):
    pass


class UnityBlockHostAccessList(UnityResourceList):
    @classmethod
    def get_resource_class(cls):
        return UnityBlockHostAccess


class UnityHost(UnityResource):
    @classmethod
    def create(cls, cli, name, host_type=None, desc=None, os=None):
        if host_type is None:
            host_type = HostTypeEnum.HOST_MANUAL

        resp = cli.post(cls().resource_class,
                        type=host_type,
                        name=name,
                        description=desc,
                        osType=os)
        resp.raise_if_err()
        return cls(_id=resp.resource_id, cli=cli)

    @classmethod
    def get_host(cls, cli, _id, force_create=False):
        if isinstance(_id, six.string_types) and ('.' in _id or ':' in _id):
            # it looks like an ip address, find or create the host
            address = converter.url_to_host(_id)
            netmask = converter.url_to_mask(_id)
            ports = UnityHostIpPortList(cli=cli, address=address)
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
                host = cls.create(cli, host_name, host_type=host_type)
                host.add_ip_port(address, netmask=netmask)
                ret = host
            else:
                ret = None
        else:
            ret = cls.get(cli=cli, _id=_id)
        return ret

    def _get_host_lun(self, lun=None):
        if lun:
            ret = UnityHostLunList.get(self._cli, host=self.id, lun=lun.id)
        else:
            ret = UnityHostLunList.get(self._cli, host=self.id)
            log.debug('Found {} host luns attached to this host'
                      .format(len(ret)))
        return ret

    def detach_alu(self, lun):
        return lun.detach_from(self)

    def attach_alu(self, lun):
        if self.has_alu(lun):
            raise ex.UnityAluAlreadyAttachedError()

        try:
            lun.attach_to(self)
            self.update()
            hlu = self.get_hlu(lun)
        except ex.UnityAttachAluExceedLimitError:
            # The number of luns exceeds system limit
            raise
        except ex.UnityException:
            # other attach error, remove this lun if already attached
            self.detach_alu(lun)
            raise ex.UnityAttachAluError()

        return hlu

    def has_alu(self, lun):
        alu = self.get_hlu(lun=lun)
        if alu is None:
            return False
        else:
            return True

    def get_hlu(self, lun):
        which = self._get_host_lun(lun=lun)
        if not which:
            log.debug('lun {} is not attached to host {}'
                      .format(lun.name, self.name))
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
                    'name {} not found under host {}.'
                    .format(uid, self.name))
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
            resp = None
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
        req_body = {'host': host}
        req_body['isIgnored'] = is_ignored

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
