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
import six
from xml import etree

__author__ = 'Jay Xu'

log = logging.getLogger(__name__)


class XMLAPIParser(object):
    def __init__(self):
        # The following Boolean acts as the flag for the common sub-element.
        # For instance:
        #     <CifsServers>
        #         <li> server_1 </li>
        #     </CifsServers>
        #     <Alias>
        #         <li> interface_1 </li>
        #     </Alias>
        self.tag = None

        self.elt = {}
        self.stack = []

    @staticmethod
    def _delete_ns(tag):
        i = tag.find('}')
        if i >= 0:
            tag = tag[i + 1:]
        return tag

    def parse(self, xml):
        result = {
            'type': None,
            'taskId': None,
            'maxSeverity': None,
            'objects': [],
            'problems': [],
        }

        events = ("start", "end")

        context = etree.ElementTree.iterparse(six.BytesIO(xml.encode('utf-8')),
                                              events=events)
        for action, elem in context:
            self.tag = self._delete_ns(elem.tag)

            func = self._get_func(action, self.tag)
            self.track_stack(action, elem)

            if func in vars(XMLAPIParser):
                if action == 'start':
                    eval('self.' + func)(elem, result)
                elif action == 'end':
                    eval('self.' + func)(elem, result)

        return result

    def track_stack(self, action, elem):
        if action == 'start':
            self.stack.append(elem)
        elif action == 'end':
            self.stack.pop()

    @staticmethod
    def _get_func(action, tag):
        if tag == 'W2KServerData':
            return action + '_' + 'w2k_server_data'

        temp_list = re.sub(r"([A-Z])", r" \1", tag).split()
        if temp_list:
            func_name = action + '_' + '_'.join(temp_list)
        else:
            func_name = action + '_' + tag
        return func_name.lower()

    @staticmethod
    def _copy_property(source, target):
        for key in source:
            target[key] = source[key]

    @classmethod
    def _append_elm_property(cls, elm, result, identifier):
        for obj in result['objects']:
            if cls.has_identifier(obj, elm, identifier):
                for key, value in elm.attrib.items():
                    obj[key] = value

    @staticmethod
    def has_identifier(obj, elm, identifier):
        return (identifier in obj and
                identifier in elm.attrib and
                elm.attrib[identifier] == obj[identifier])

    def _append_element(self, elm, result, identifier):
        sub_elm = {}
        self._copy_property(elm.attrib, sub_elm)

        for obj in result['objects']:
            if self.has_identifier(obj, elm, identifier):
                if self.tag in obj:
                    obj[self.tag].append(sub_elm)
                else:
                    obj[self.tag] = [sub_elm]

    def start_task_response(self, elm, result):
        result['type'] = 'TaskResponse'
        self._copy_property(elm.attrib, result)

    @staticmethod
    def start_fault(_, result):
        result['type'] = 'Fault'

    def _parent_tag(self):
        if len(self.stack) >= 2:
            parent = self.stack[-2]
            ret = self._delete_ns(parent.tag)
        else:
            ret = None
        return ret

    def start_status(self, elm, result):
        parent_tag = self._parent_tag()
        if parent_tag == 'TaskResponse':
            result['maxSeverity'] = elm.attrib['maxSeverity']
        elif parent_tag in ['MoverStatus', 'Vdm', 'MoverHost']:
            self.elt['maxSeverity'] = elm.attrib['maxSeverity']

    def start_query_status(self, elm, result):
        result['type'] = 'QueryStatus'
        self._copy_property(elm.attrib, result)

    def start_problem(self, elm, result):
        self.elt = {}
        self._copy_property(elm.attrib, self.elt)
        result['problems'].append(self.elt)

    def start_description(self, elm, _):
        self.elt['Description'] = elm.text

    def start_action(self, elm, _):
        self.elt['Action'] = elm.text

    def start_diagnostics(self, elm, _):
        self.elt['Diagnostics'] = elm.text

    def start_file_system(self, elm, result):
        self._as_object(elm, result)

    def start_file_system_capacity_info(self, elm, result):
        identifier = 'fileSystem'

        self._append_elm_property(elm, result, identifier)

    def start_storage_pool(self, elm, result):
        self._as_object(elm, result)

    def start_system_storage_pool_data(self, elm, _):
        self._copy_property(elm.attrib, self.elt)

    def start_mover(self, elm, result):
        self._as_object(elm, result)

    def start_mover_host(self, elm, result):
        self._as_object(elm, result)

    def start_nfs_export(self, elm, result):
        self._as_object(elm, result)

    def _as_object(self, elm, result):
        self.elt = {}
        self._copy_property(elm.attrib, self.elt)
        result['objects'].append(self.elt)

    def start_mover_status(self, elm, result):
        identifier = 'mover'
        self._append_elm_property(elm, result, identifier)

    def start_mover_route(self, elm, result):
        self._append_element(elm, result, 'mover')

    def start_mover_deduplication_settings(self, elm, result):
        self._append_element(elm, result, 'mover')

    def start_mover_dns_domain(self, elm, result):
        self._append_element(elm, result, 'mover')

    def start_mover_interface(self, elm, result):
        self._append_element(elm, result, 'mover')

    def start_logical_network_device(self, elm, result):
        self._append_element(elm, result, 'mover')

    def start_vdm(self, elm, result):
        self._as_object(elm, result)

    def _add_element(self, name, item):
        if name not in self.elt:
            self.elt[name] = []
        self.elt[name].append(item)

    def start_li(self, elm, _):
        parent_tag = self._parent_tag()
        host_nodes = ('AccessHosts', 'RwHosts', 'RoHosts', 'RootHosts')
        if parent_tag == 'CifsServers':
            self._add_element('CifsServers', elm.text)
        elif parent_tag == 'Aliases':
            self._add_element('Aliases', elm.text)
        elif parent_tag == 'Interfaces':
            self._add_element('Interfaces', elm.text)
        elif parent_tag in host_nodes:
            if parent_tag not in self.elt:
                self.elt[parent_tag] = []
            self.elt[parent_tag].append(elm.text)

    def start_cifs_server(self, elm, result):
        self._as_object(elm, result)

    def start_w2k_server_data(self, elm, _):
        self._copy_property(elm.attrib, self.elt)

    def start_cifs_share(self, elm, result):
        self._as_object(elm, result)

    def start_checkpoint(self, elm, result):
        self._as_object(elm, result)

    def start_ro_file_system_hosts(self, elm, _):
        self._copy_property(elm.attrib, self.elt)

    def start_standalone_server_data(self, elm, _):
        self._copy_property(elm.attrib, self.elt)

    def start_fibre_channel_device_data(self, elm, _):
        self._copy_attrib_to_parent(elm)

    def start_network_device_data(self, elm, _):
        self._copy_attrib_to_parent(elm)

    def _copy_attrib_to_parent(self, elm):
        if len(self.stack) >= 2:
            parent = self.stack[-2]
            for k, v in elm.attrib.items():
                parent.attrib[k] = v

    def start_mover_motherboard(self, elm, result):
        self._append_element(elm, result, 'moverHost')

    def end_physical_device(self, elm, result):
        self._append_element(elm, result, 'moverHost')

    def start_fc_descriptor(self, elm, result):
        self._append_element(elm, result, 'moverHost')

    def start_mount(self, elm, result):
        self._as_object(elm, result)
