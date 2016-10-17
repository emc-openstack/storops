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

from storops.lib.common import cache
from storops.lib.parser import ParserConfigFactory, OutputParser

__author__ = 'Cedric Zhuang'

log = logging.getLogger(__name__)


class UnityParserConfigFactory(ParserConfigFactory):
    @classmethod
    def get_parser_clz(cls, data_src):
        if data_src is None or data_src == 'rest':
            ret = UnityRestParser
        else:
            raise ValueError('data_src {} not supported.'.format(data_src))
        return ret


_factory_singleton = UnityParserConfigFactory()


@cache
def get_unity_parser(name):
    return _factory_singleton.get(name)


class UnityRestParser(OutputParser):
    data_src = 'rest'

    def __init__(self):
        super(UnityRestParser, self).__init__()
        self.name = None

    def parse_all(self, output, properties=None):
        try:
            output = output.contents
        except AttributeError:
            pass
        return output

    def parse(self, output, properties=None):
        try:
            output = output.first_content
        except AttributeError:
            pass
        return self._parse_object(output, properties=None,
                                  preloaded_props=properties)

    def _parse_object(self, obj, properties=None, preloaded_props=None):
        if properties is None:
            properties = self.properties

        ret = {}
        for p in properties:
            if isinstance(obj, list):
                log.error('cannot parse list: {}.  '
                          'a list converter must be specified.'.format(obj))
                continue
            if p.label in obj.keys():
                value = p.convert(obj[p.label])
                if preloaded_props is not None and isinstance(
                        preloaded_props, NestedProperties):
                    subtree = preloaded_props.get_child_subtree(p.key)
                    if (subtree is not None and
                            hasattr(value, 'set_preloaded_properties')):
                        value.set_preloaded_properties(subtree)
                ret[p.key] = value
        return ret

    def init_from_config(self, config):
        self.name = config.name


class NestedProperty(object):
    def __init__(self, key):
        self.key = key

    @property
    def label(self):
        return self.under_score_to_camel_case(self.key)

    @classmethod
    def under_score_to_camel_case(cls, value):
        ret = re.sub(r'_([a-z])', lambda a: a.group(1).upper(), value)
        return ret

    def get_first_level_key(self):
        return self.key.split('.')[0]

    def remove_first_level_key(self):
        pos = self.key.find('.')
        if pos >= 0:
            return self.key[pos + 1:]
        else:
            return None


class NestedProperties(object):
    def __init__(self, *keys):
        self._props = map(NestedProperty, keys)
        self._map = None
        self._query_fields = None

    @classmethod
    def build(cls, properties):
        ret = None
        if not properties:
            ret = None
        elif isinstance(properties, six.text_type):
            ret = NestedProperties(properties)
        elif isinstance(properties, (list, tuple, set)):
            ret = NestedProperties(*properties)
        else:
            log.error('invalid properties {} to build NestedProperties '
                      'object.'.format(properties))
        return ret

    @property
    def _prop_map(self):
        if not self._map:
            map = {}
            for p in self._props:
                key = p.get_first_level_key()
                child_prop = p.remove_first_level_key()
                if child_prop is not None:
                    map.setdefault(key, []).append(child_prop)
                else:
                    map.setdefault(key, [])
            self._map = map
        return self._map

    def get_properties(self):
        return self._prop_map.keys()

    def get_child_subtree(self, prop):
        if prop not in self._prop_map:
            return None
        if len(self._prop_map[prop]) == 0:
            return None
        return NestedProperties.build(self._prop_map[prop])

    @property
    def query_fields(self):
        if self._query_fields is None:
            self._query_fields = [a.label for a in self._props]
        return tuple(self._query_fields)
