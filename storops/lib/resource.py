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

from datetime import datetime, timedelta

import storops.exception as ex
import storops.lib.parser
from storops.lib.common import JsonPrinter

__author__ = 'Cedric Zhuang'


class Resource(JsonPrinter):
    def __init__(self):
        self._property_cache = {}
        self._parsed_resource = None
        super(Resource, self).__init__()

    @staticmethod
    def _get(data, key):
        if isinstance(key, storops.lib.parser.PropDescriptor):
            key = key.key
        try:
            ret = data.__getitem__(key)
        except KeyError:
            ret = None
        return ret

    @staticmethod
    def _has_get(data):
        return hasattr(data, '__getitem__')

    def _get_name(self):
        if hasattr(self, '_name') and self._name is not None:
            name = self._name
        else:
            name = self.name
        return name

    @classmethod
    def _get_parser(cls):
        raise NotImplementedError('_get_parser not implemented.')

    @property
    def parsed_resource(self):
        return self._parsed_resource

    def update(self, data=None):
        if data is None:
            data = self._get_raw_resource()

        self._parsed_resource = self._parse_raw(data)
        return self

    def get_index(self):
        parser = self._get_parser()
        index_desc = parser.index_property
        if index_desc is not None:
            ret = getattr(self, index_desc.key)
        else:
            raise ex.NoIndexException('{} does not have index.'
                                      .format(self.__class__.__name__))
        return ret

    @property
    def existed(self):
        try:
            ret = self.get_index() is not None
        except ex.NoIndexException:
            # no index, check if any of the property is available
            prop = self._get_first_not_none_prop()
            ret = prop is not None
        return ret

    def _get_first_not_none_prop(self):
        ret = None
        prop_desc_list = self._get_parser().properties
        for prop_desc in prop_desc_list:
            ret = getattr(self, prop_desc.key)
            if ret is not None:
                break
        return ret

    def is_valid(self):
        return self.existed()

    def _get_parsed_resource(self):
        return self._get_raw_resource()

    def _parse_raw(self, data):
        return self._get_parser().parse(data)

    @classmethod
    def parse(cls, output):
        obj = cls()
        data = cls._get_parser().parse_single(output)
        return obj.update(data)

    @classmethod
    def parse_all(cls, output):
        ret = []
        for data in cls._get_parser().parse_all(output):
            obj = cls()
            ret.append(obj.update(data))
        return ret

    def property_names(self):
        parser = self._get_parser()
        if parser is not None:
            ret = parser.property_names
        else:
            ret = []
        return ret

    @classmethod
    def get_property_label(cls, key):
        parser = cls._get_parser()
        if parser is not None:
            ret = parser.get_property_label(key)
        else:
            ret = None
        return ret

    @classmethod
    def get_property_key(cls, label):
        parser = cls._get_parser()
        if parser is not None:
            ret = parser.get_property_key(label)
        else:
            ret = None
        return ret

    def _get_properties(self, dec=0):
        props = {'hash': self.__hash__()}

        if dec >= 0:
            prop_names = list(self.property_names())
            prop_names.append('existed')
            for name in prop_names:
                try:
                    value = getattr(self, name)
                    if isinstance(value, JsonPrinter):
                        value = value.get_dict_repr(dec - 1)
                    elif isinstance(value, (datetime, timedelta)):
                        value = str(value)
                    elif isinstance(value, (tuple, list, set)):
                        value = [v.get_dict_repr(dec - 1) for v in value]
                    props[name] = value
                except AttributeError:
                    # skip not available attributes
                    continue
        return props

    @property
    def _cache_size(self):
        return len(self._property_cache)

    def _get_raw_resource(self):
        """get raw input of this resource

        Get the raw input of this resource.
        The input could be retrieved from multiple interface like
        CLI or CIM."""
        return ''

    def __getattr__(self, item):
        if item in self._property_cache:
            ret = self._property_cache[item]
        elif not item.startswith('_'):
            ret = self._get_property_from_raw(item)
        else:
            raise AttributeError(item)
        return ret

    def _update_property_cache(self, name, value):
        self._property_cache[name] = value

    def _is_updated(self):
        return self._parsed_resource is not None

    def _get_property_from_raw(self, item):
        if not self._is_updated():
            self.update()
        if item in self.property_names():
            ret = self._get_value_by_key(item)
        else:
            raise AttributeError(
                "'{}' does not contain attribute '{}'".format(
                    self.__class__.__name__, item))
        return ret

    def _get_value_by_key(self, item):
        return self._parsed_resource.get(item, None)


class ResourceList(Resource):
    def __init__(self):
        super(ResourceList, self).__init__()
        self._list = None
        self._iter = None

    def update(self, data=None):
        self._list = []
        if data is None:
            data = self._get_raw_resource()

        if data is not None and isinstance(data, dict):
            parsed_list = data
        else:
            parsed_list = self._parse_raw(data)

        for i in parsed_list:
            item = self.get_resource_class()()
            item.update(i)
            if self._filter(item):
                self._list.append(item)
        return self

    def _apply_filter(self):
        result = []
        for item in self:
            if self._filter(item):
                result.append(item)
        self._list = result

    def _filter(self, _):
        return True

    def _parse_raw(self, data):
        return self._get_parser().parse_all(data)

    @classmethod
    def _get_parser(cls):
        raise NotImplementedError('_get_parser not implemented.')

    @property
    def list(self):
        if self._list is None:
            self.update()
        return self._list

    @classmethod
    def get_resource_class(cls):
        raise NotImplementedError(
            'should return the class ref of the resource in the list.')

    def get_dict_repr(self, dec=1):
        items = [item.get_dict_repr(dec - 1) for item in self.list]
        return {self.__class__.__name__: items}

    def __len__(self):
        return len(self.list)

    def __iter__(self):
        self._iter = self.list.__iter__()
        return self

    def next(self):
        return next(self._iter)

    def __next__(self):
        return self.next()

    def __getitem__(self, item):
        return self.list[item]

    def __getattr__(self, v):
        clz = self.get_resource_class()
        s = clz()
        ret = None
        if not v.startswith('_'):
            if v in dir(s):
                ret = self.get_member_attr_list(v)
            elif hasattr(s, 'property_names') and v in s.property_names():
                ret = self.get_member_attr_list(v)

        if ret is None:
            raise AttributeError(
                '{} do not has attribute {}.'.format(clz.__name__, v))
        return ret

    def get_member_attr_list(self, v):
        return [getattr(i, v) for i in self]

    def _is_updated(self):
        return self._list is not None
