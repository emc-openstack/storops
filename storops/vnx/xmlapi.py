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

from xml.etree import ElementTree as ET

from storops.lib import converter

__author__ = 'Cedric Zhuang'


class XNode(ET.Element):
    def __init__(self, tag, *sub_nodes, **attrib):
        super(XNode, self).__init__(tag, attrib=attrib)
        for sub in sub_nodes:
            if isinstance(sub, XNode):
                self.append(sub)
            elif sub is not None:
                self.text = str(sub)

    def __str__(self):
        return ET.tostring(self, encoding='utf-8').decode('utf-8')


class XmlBuilder(object):
    def __getattr__(self, name):
        def construct(*sub_nodes, **attrib):
            return XNode(name,
                         *sub_nodes,
                         **{k: converter.boolean_to_str(v)
                            if isinstance(v, bool) else str(v)
                            for k, v in attrib.items() if v is not None})
        return construct

    def list_elements(self, name, elements):
        name_func = getattr(self, name)
        elements_list = [self.li(e) for e in elements]
        return name_func(*elements_list)


_xb = XmlBuilder()
_default_task_timeout = 5 * 60
XML_NS = 'http://www.emc.com/schemas/celerra/xml_api'


class NasXmlBuilder(object):

    @staticmethod
    def query_package(body):
        return _xb.RequestPacket(_xb.Request(_xb.Query(body)),
                                 xmlns=XML_NS)

    @staticmethod
    def task_package(body):
        return _xb.RequestPacket(
            _xb.Request(_xb.StartTask(body, timeout=_default_task_timeout)),
            xmlns=XML_NS)

    @classmethod
    def get_filesystem(cls, name=None, fs_id=None):
        selection_xml = _xb.AspectSelection(
            **cls._flag_true(['fileSystems', 'fileSystemCapacityInfos']))

        alias_xml = None
        fs_xml = None
        if name is not None:
            alias_xml = _xb.Alias(name=name)
        elif fs_id is not None:
            fs_xml = _xb.FileSystem(fileSystem=fs_id)

        body = _xb.FileSystemQueryParams(selection_xml, alias_xml, fs_xml)
        return cls.query_package(body)

    @classmethod
    def create_filesystem(cls, name, size, pool_id,
                          mover_id, is_vdm=False):
        mover = cls._get_mover_id_node(mover_id, is_vdm)

        body = _xb.NewFileSystem(mover,
                                 _xb.StoragePool(pool=pool_id,
                                                 size=size,
                                                 mayContainSlices=True),
                                 name=name)
        return cls.task_package(body)

    @classmethod
    def extend_filesystem(cls, fs_id, delta_size, pool_id=None):
        body = _xb.ExtendFileSystem(
            _xb.StoragePool(pool=pool_id, size=delta_size),
            fileSystem=fs_id)
        return cls.task_package(body)

    @staticmethod
    def _get_mover_id_node(mover_id, is_vdm):
        if not is_vdm:
            ret = _xb.Mover(mover=mover_id)
        else:
            ret = _xb.Vdm(vdm=mover_id)
        return ret

    @classmethod
    def delete_filesystem(cls, fs_id):
        body = _xb.DeleteFileSystem(fileSystem=fs_id)
        return cls.task_package(body)

    @classmethod
    def get_nas_pool(cls):
        return cls.query_package(_xb.StoragePoolQueryParams())

    @staticmethod
    def _flag_true(props):
        return {name: True for name in props}

    @classmethod
    def _get_mover_props(cls, full=True):
        prop_names = ['movers']
        if full:
            prop_names += ['moverDeduplicationSettings',
                           'moverDnsDomains',
                           'moverInterfaces',
                           'moverNetworkDevices',
                           'moverNisDomains',
                           'moverRoutes',
                           'moverStatuses']
        return cls._flag_true(prop_names)

    @classmethod
    def get_mover(cls, mover_id=None, full=True):
        params = _xb.AspectSelection(**cls._get_mover_props(full))
        body = _xb.MoverQueryParams(params, mover=mover_id)
        return cls.query_package(body)

    @classmethod
    def get_fs_snap(cls, name=None, snap_id=None):
        param = None
        if snap_id is not None:
            param = _xb.Checkpoint(checkpoint=snap_id)
        elif name is not None:
            param = _xb.Alias(name=name)
        body = _xb.CheckpointQueryParams(param)
        return cls.query_package(body)

    @classmethod
    def create_snap(cls, name, fs_id, pool_id, snap_size=None):
        pool = _xb.StoragePool(pool=pool_id, size=snap_size)
        body = _xb.NewCheckpoint(_xb.SpaceAllocationMethod(pool),
                                 checkpointOf=fs_id, name=name)
        return cls.task_package(body)

    @classmethod
    def delete_snap(cls, snap_id, force=False):
        body = _xb.DeleteCheckpoint(checkpoint=snap_id, force=force)
        return cls.task_package(body)

    @classmethod
    def create_cifs_server(cls, name, mover_id, is_vdm=False, workgroup=None,
                           domain=None, ip_list=None, alias_name=None,
                           local_admin_password=None):
        if domain is not None:
            ret = cls._create_domain_cifs_server(
                name, domain, mover_id, is_vdm, ip_list, alias_name,
                local_admin_password)
        elif workgroup is not None:
            ret = cls._create_standalone_cifs_server(
                name, workgroup, mover_id, is_vdm, ip_list, alias_name,
                local_admin_password)
        else:
            raise ValueError('either workgroup or domain should be specified.')
        return ret

    @classmethod
    def modify_domain_cifs_server(cls, name, mover_id, is_vdm=False,
                                  join_domain=None, username=None,
                                  password=None):
        body = _xb.ModifyW2KCifsServer(
            _xb.DomainSetting(join_domain=join_domain, username=username,
                              password=password),
            mover=mover_id, moverIdIsVdm=is_vdm, name=name)

        return cls.task_package(body)

    @staticmethod
    def _get_alias_name_li(alias_name, name):
        if alias_name is None:
            alias_name = name[-12:]
        if name != alias_name:
            return _xb.li(alias_name)
        else:
            return None

    @classmethod
    def _create_standalone_cifs_server(cls, name, workgroup, mover_id,
                                       is_vdm=False, ip_list=None,
                                       alias_name=None,
                                       local_admin_password=None):
        if local_admin_password is None:
            raise ValueError('local admin password is required for '
                             'stand alone CIFS server.')

        mover_xml = _xb.MoverOrVdm(mover=mover_id, moverIdIsVdm=is_vdm)

        alias_li = cls._get_alias_name_li(alias_name, name)
        aliases_xml = _xb.Aliases(alias_li)

        body = _xb.NewStandaloneCifsServer(
            mover_xml, aliases_xml, name=name, workgroup=workgroup,
            interfaces=ip_list, localAdminPassword=local_admin_password)
        return cls.task_package(body)

    @classmethod
    def _create_domain_cifs_server(cls, name, domain, mover_id, is_vdm=False,
                                   ip_list=None, alias_name=None,
                                   local_admin_password=None):
        mover_xml = _xb.MoverOrVdm(mover=mover_id, moverIdIsVdm=is_vdm)

        alias_li = cls._get_alias_name_li(alias_name, name)
        aliases_xml = _xb.Aliases(alias_li)

        if domain.comp_name is None:
            domain.comp_name = name

        domain_xml = None
        if domain.user is not None:
            domain_xml = _xb.JoinDomain(userName=domain.user,
                                        password=domain.password)

        body = _xb.NewW2KCifsServer(mover_xml, aliases_xml, domain_xml,
                                    compName=domain.comp_name,
                                    domain=domain.name,
                                    name=name,
                                    interfaces=ip_list,
                                    localAdminPassword=local_admin_password)
        return cls.task_package(body)

    @classmethod
    def get_cifs_server(cls, name=None, mover_id=None, is_vdm=False):
        mover_xml = None
        if mover_id is not None:
            mover_xml = _xb.MoverOrVdm(mover=mover_id, moverIdIsVdm=is_vdm)
        body = _xb.CifsServerQueryParams(mover_xml,
                                         name=(None if name is None
                                               else name.upper()))
        return cls.query_package(body)

    @classmethod
    def delete_cifs_server(cls, name, mover_id, is_vdm=False):
        body = _xb.DeleteCifsServer(mover=mover_id,
                                    moverIdIsVdm=is_vdm,
                                    name=name)
        return cls.task_package(body)

    @classmethod
    def create_dns_domain(cls, mover_id, name, servers, protocol='udp'):
        body = _xb.NewMoverDnsDomain(mover=mover_id,
                                     name=name,
                                     servers=servers,
                                     protocol=protocol)
        return cls.task_package(body)

    @classmethod
    def delete_dns_domain(cls, mover_id, name):
        body = _xb.DeleteMoverDnsDomain(mover=mover_id, name=name)
        return cls.task_package(body)

    @classmethod
    def get_fs_mp(cls, path=None, mover_id=None, is_vdm=False):
        mover_xml = None
        if mover_id is not None:
            mover_xml = _xb.MoverOrVdm(mover=mover_id,
                                       moverIdIsVdm=is_vdm)
        body = _xb.MountQueryParams(mover_xml, path=path)
        return cls.query_package(body)

    @classmethod
    def create_fs_mp(cls, path, fs_id, mover_id, is_vdm=False):
        body = _xb.NewMount(_xb.MoverOrVdm(mover=mover_id,
                                           moverIdIsVdm=is_vdm),
                            fileSystem=fs_id, path=path)
        return cls.task_package(body)

    @classmethod
    def delete_fs_mp(cls, path, mover_id, is_vdm=False):
        body = _xb.DeleteMount(mover=mover_id,
                               moverIdIsVdm=is_vdm,
                               path=path)
        return cls.task_package(body)

    @classmethod
    def get_mover_host(cls, mover_host_id=None):
        aspect = _xb.AspectSelection(
            **cls._flag_true(['moverHosts',
                              'moverMotherboards',
                              'physicalDevices',
                              'fibreChannelConnections']))
        body = _xb.MoverHostQueryParams(aspect, moverHost=mover_host_id)
        return cls.query_package(body)

    @classmethod
    def create_mover_interface(cls, mover_id, device, ip, net_mask,
                               vlan_id=0, name=None):
        if name is None:
            name = '{}-{}'.format(ip, vlan_id)

        body = _xb.NewMoverInterface(device=device,
                                     ipAddress=ip,
                                     mover=mover_id,
                                     name=name,
                                     netMask=net_mask,
                                     vlanid=vlan_id)
        return cls.task_package(body)

    @classmethod
    def delete_mover_interface(cls, mover_id, ip):
        body = _xb.DeleteMoverInterface(ipAddress=ip, mover=mover_id)
        return cls.task_package(body)

    @classmethod
    def create_vdm(cls, mover_id, name, pool_id=None):
        return cls.task_package(_xb.NewVdm(mover=mover_id,
                                           name=name,
                                           storagePool=pool_id))

    @classmethod
    def delete_vdm(cls, vdm_id):
        return cls.task_package(_xb.DeleteVdm(vdm=vdm_id))

    @classmethod
    def get_vdm(cls, vdm_id=None):
        return cls.query_package(_xb.VdmQueryParams(vdm=vdm_id))

    @classmethod
    def get_nfs_export(cls, mover_id=None, path=None):
        return cls.query_package(_xb.NfsExportQueryParams(mover=mover_id,
                                                          path=path))

    @classmethod
    def create_nfs_export(cls, mover_id, path, ro=False, host_config=None):
        host_xml = []
        if host_config is not None:
            host_xml = host_config.get_xml_node()
        body = _xb.NewNfsExport(*host_xml,
                                mover=mover_id, path=path, readOnly=ro)
        return cls.task_package(body)

    @classmethod
    def delete_nfs_export(cls, mover_id, path):
        body = _xb.DeleteNfsExport(mover=mover_id, path=path)
        return cls.task_package(body)

    @classmethod
    def modify_nfs_export(cls, mover_id, path, ro=None, host_config=None):
        host_xml = []
        if host_config is not None:
            host_xml = host_config.get_xml_node()
        body = _xb.ModifyNfsExport(*host_xml, mover=mover_id, path=path,
                                   readOnly=None if ro is None else ro)
        return cls.task_package(body)

    @classmethod
    def create_cifs_share(cls, name, server_name, mover_id,
                          is_vdm=False, path=None):
        if path is None:
            path = r'\{}'.format(name)
        mover = _xb.MoverOrVdm(mover=mover_id,
                               moverIdIsVdm=is_vdm)
        body = _xb.NewCifsShare(mover, _xb.CifsServers(_xb.li(server_name)),
                                name=name, path=path)
        return cls.task_package(body)

    @classmethod
    def get_cifs_share(cls, server_name=None, share_name=None, mover_id=None,
                       is_vdm=False):
        mover_xml = None
        if mover_id is not None:
            mover_xml = _xb.MoverOrVdm(mover=mover_id, moverIdIsVdm=is_vdm)
        body = _xb.CifsShareQueryParams(mover_xml, cifsServer=server_name,
                                        name=share_name)
        return cls.query_package(body)

    @classmethod
    def delete_cifs_share(cls, name, mover_id, server_names, is_vdm=False):
        body = _xb.DeleteCifsShare(_xb.list_elements('CifsServers',
                                                     server_names),
                                   mover=mover_id,
                                   moverIdIsVdm=is_vdm,
                                   name=name)
        return cls.task_package(body)
