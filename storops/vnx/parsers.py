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

from collections import OrderedDict
import logging
import re

import six

from storops.lib.common import Dict, cache
from storops.lib.parser import OutputParser, PropDescriptor, \
    ParserConfigFactory

log = logging.getLogger(__name__)


class VNXPropDescriptor(PropDescriptor):
    pass


class VNXParserConfigFactory(ParserConfigFactory):
    @classmethod
    def get_parser_clz(cls, data_src):
        if data_src == 'cli':
            ret = VNXCliParser
        elif data_src == 'xmlapi':
            ret = VNXXmlApiParser
        else:
            raise ValueError('data_src {} not supported.'.format(data_src))
        return ret

    @classmethod
    def get_converter(cls, value):
        from storops.vnx import converter
        if hasattr(converter, value):
            ret = getattr(converter, value)
        else:
            ret = None
        return ret


_factory_singleton = VNXParserConfigFactory()


@cache
def get_vnx_parser(name):
    return _factory_singleton.get(name)


class VNXCliParser(OutputParser):
    data_src = 'cli'

    def _split_by_index(self, output):
        instances = []

        index_descriptor = self.index_property
        if index_descriptor is not None:
            index_pattern = index_descriptor.index_pattern

            last_start = 0
            has_match = False
            if isinstance(output, bytes):
                output = output.decode("utf-8")
            for match in re.finditer(index_pattern, output):
                has_match = True
                start = match.start()
                if start == 0:
                    continue
                else:
                    instances.append(output[last_start:start])
                    last_start = start
            if has_match:
                instances.append(output[last_start:])
        else:
            instances = [output]
        return instances

    def parse_single(self, output, properties=None):
        if isinstance(output, six.string_types):
            output = output.strip()
            ret = Dict()

            if properties is None:
                properties = self.properties

            for p in properties:
                matched = re.search(p.pattern, output)

                matched_value = None
                if matched is not None:
                    if len(matched.groups()) == 1:
                        value = matched.group(1)
                        value = value.strip()
                    else:
                        value = matched.groups()
                    value = p.convert(value)
                    matched_value = value
                elif p.is_index:
                    # index must have a match, skip this invalid input
                    ret = Dict()
                    break
                ret[p.key] = matched_value
        else:
            ret = output
        return ret

    def parse_all(self, output, properties=None):
        if isinstance(output, six.string_types):
            output = output.strip()
            split_outputs = self._split_by_index(output)
            instances = self._parse_split_output(split_outputs, properties)
            instances = self._merge_instance_with_same_index(instances)
        else:
            instances = output
        return instances

    def _merge_instance_with_same_index(self, instances):
        def key_gen(instance):
            str_keys = []
            for index in indices:
                str_keys.append(
                    '{}: {}'.format(index.key, instance[index.key]))
            return ', '.join(str_keys)

        def update_map(instance):
            key = key_gen(instance)
            if key not in idx_inst_map:
                idx_inst_map[key] = instance
            else:
                existed = idx_inst_map[key]
                for k, v in six.iteritems(instance):
                    if k not in existed or v is not None:
                        existed[k] = v

        idx_inst_map = OrderedDict()
        indices = self.index_property_list
        list(map(update_map, instances))
        return list(idx_inst_map.values())

    def _parse_split_output(self, split_outputs, properties):
        ret = []
        for instance in split_outputs:
            parsed = self.parse_single(instance, properties)
            if len(parsed) > 0:
                ret.append(parsed)
        return ret

    def parse(self, output, properties=None):
        ret = self.parse_all(output, properties)

        if len(ret) == 0:
            ret = Dict()
        elif isinstance(ret, (tuple, list)):
            ret = ret[0]
        return ret


class VNXXmlApiParser(OutputParser):
    data_src = 'xmlapi'

    def parse_all(self, output, properties=None):
        if hasattr(output, 'objects'):
            output = output.objects
        return [self._parse_object(obj) for obj in output]

    def parse(self, output, properties=None):
        if hasattr(output, 'objects') and len(output.objects):
            ret = self._parse_object(output.first_object, properties)
        elif isinstance(output, (list, tuple)) and len(output) > 0:
            ret = self._parse_object(output[0], properties)
        elif isinstance(output, dict):
            ret = output
        else:
            ret = Dict()
        return ret

    def _parse_object(self, obj, properties=None):
        if properties is None:
            properties = self.properties

        ret = {}
        for p in properties:
            if p.label in obj.keys():
                value = p.convert(obj[p.label])
                ret[p.key] = value
        return ret
