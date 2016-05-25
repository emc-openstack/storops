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

import six

from storops.exception import UnityHostInitiatorUnknownType, \
    UnityHostInitiatorNotFoundError
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
            ports = UnityHostIpPortList(cli=cli, address=address)
            if len(ports) == 1:
                ret = ports[0].host
            elif force_create:
                log.info('cannot find an existing host with ip {}.  '
                         'create a new host "{}" to attach it.'
                         .format(address, address))
                host = cls.create(cli, address)
                host.add_ip_port(address)
                ret = host
            else:
                ret = None
        else:
            ret = cls.get(cli=cli, _id=_id)
        return ret

    def detach_hlu(self, lun):
        return lun.detach_from(self)

    def has_hlu(self, lun):
        if not self.host_luns or not lun:
            return False

        has = False
        for host_lun in self.host_luns:
            if host_lun.lun is not None:
                if host_lun.lun.id == lun.id:
                    has = True
                    break

        return has

    def get_hlu(self, lun):
        if not self.host_luns or not lun:
            return None

        for host_lun in self.host_luns:
            if host_lun.lun is not None:
                if host_lun.lun.id == lun.id:
                    hlu = host_lun.hlu
                    break
        else:
            log.debug('Lun {} is not attached to host {}'
                      .format(lun.name, self.name))
            # TODO: raise UnityLunNotAttach?
            hlu = None
        return hlu

    def add_initiator(self, name, type, force_create=True, **kwargs):
        initiators = UnityHostInitiatorList.get(cli=self._cli,
                                                initiator_id=name)

        # Even if no initiators are found, the initiators object still contain
        # one fake initiator.
        initiator = initiators.first_item
        if not initiator.existed:
            if force_create:
                initiator = UnityHostInitiator.create(self._cli, name,
                                                      self, type, **kwargs)
            else:
                raise UnityHostInitiatorNotFoundError(
                    'name {} not found under host {}.'
                    .format(name, self.name))
        else:
            log.debug('Initiator {} is existed in unity system.'.format(name))

        initiator.modify(self)
        return initiator.update()

    def delete_initiator(self, name):
        initiators = []
        if self.fc_host_initiators:
            initiators += self.fc_host_initiators
        if self.iscsi_host_initiators:
            initiators += self.iscsi_host_initiators
        for item in initiators:
            if item.initiator_id == name:
                # remove from the host initiator list first,
                # otherwise delete initiator will not work
                item.modify(None)
                resp = item.delete()
                resp.raise_if_err()
                break
        else:
            resp = None
            raise UnityHostInitiatorNotFoundError(
                'name {} not found under host {}.'.format(name, self.name))

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


class UnityHostContainer(UnityResource):
    pass


class UnityHostContainerList(UnityResourceList):
    @classmethod
    def get_resource_class(cls):
        return UnityHostContainer


class UnityHostInitiator(UnityResource):
    @classmethod
    def create(cls, cli, name, host, type, is_ignored=None,
               chap_user=None, chap_secret=None, chap_secret_type=None):

        if type == HostInitiatorTypeEnum.ISCSI:
            resp = cli.post(cls().resource_class,
                            host=host,
                            initiatorType=type,
                            initiatorWWNorIqn=name,
                            chapUser=chap_user,
                            chapSecret=chap_secret,
                            chapSecretType=chap_secret_type,
                            isIgnored=is_ignored)
        elif type == HostInitiatorTypeEnum.FC:
            resp = cli.post(cls().resource_class,
                            host=host,
                            initiatorType=type,
                            initiatorWWNorIqn=name,
                            isIgnored=is_ignored)
        else:
            raise UnityHostInitiatorUnknownType(
                '{} parameter is unknown type'.format(type))

        resp.raise_if_err()
        return cls(_id=resp.resource_id, cli=cli)

    def modify(self, host, is_ignored=None, chap_user=None,
               chap_secret=None, chap_secret_type=None):
        req_body = {'host': host}

        if is_ignored is not None:
            req_body['isIgnored'] = is_ignored

        if self.type == HostInitiatorTypeEnum.ISCSI:
            if chap_user is not None:
                req_body['chapUser'] = chap_user
            if chap_secret is not None:
                req_body['chapSecret'] = chap_secret
            if chap_secret_type is not None:
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
