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
from storops.lib.common import JsonPrinter, clear_instance_cache

__author__ = 'Cedric Zhuang'


class Resource(JsonPrinter):
    def __init__(self):
        self._parsed_resource = None
        super(Resource, self).__init__()

    def shadow_copy(self):
        """ Return a copy of the resource with same raw data

        :return: copy of the resource
        """
        ret = self.__class__()
        if not self._is_updated():
            # before copy, make sure source is updated.
            self.update()
        ret._parsed_resource = self._parsed_resource
        return ret

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

    @clear_instance_cache
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

    @property
    def system_version(self):
        # Return the version of backing system
        return None

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
                        value = [v.get_dict_repr(dec - 1)
                                 if isinstance(v, JsonPrinter) else v
                                 for v in value]
                    props[name] = value
                except AttributeError:
                    # skip not available attributes
                    continue
        return props

    def _get_raw_resource(self):
        """get raw input of this resource

        Get the raw input of this resource.
        The input could be retrieved from multiple interface like
        CLI or CIM."""
        return ''

    def __getattr__(self, item):
        if not item.startswith('_'):
            ret = self._get_property_from_raw(item)
        else:
            raise AttributeError(item)
        return ret

    def _is_updated(self):
        return self._parsed_resource is not None

    def get_preloaded_prop_keys(self):
        return []

    def _get_property_from_raw(self, item):
        is_preloaded_prop = item in self.get_preloaded_prop_keys()
        if not self._is_updated() and not is_preloaded_prop:
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

    def shadow_copy(self, *args, **kwargs):
        ret = super(ResourceList, self).shadow_copy()
        ret._list = self._list
        ret.set_filter(*args, **kwargs)
        return ret

    def set_filter(self, *args, **kwargs):
        self._set_filter(*args, **kwargs)
        self._apply_filter()

    def _set_filter(self, *args, **kwargs):
        # implemented by child classes if needed
        pass

    @classmethod
    def get_rsc_clz_list(cls, rsc_list_collection):
        return [l.get_resource_class() for l in rsc_list_collection]

    @clear_instance_cache
    def update(self, data=None):
        self._list = []
        if data is None:
            data = self._get_raw_resource()

        if data is not None and isinstance(data, dict):
            parsed_list = data
        else:
            parsed_list = self._parse_raw(data)

        for i in parsed_list:
            item = self._get_resource_instance()
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

    def get_preloaded_prop_keys(self):
        return []

    def __len__(self):
        return len(self.list)

    def __iter__(self):
        return iter(self.list)

    def __getitem__(self, item):
        return self.list[item]

    def _get_resource_instance(self):
        return self.get_resource_class()()

    def __getattr__(self, v):
        s = self._get_resource_instance()
        ret = None
        if not v.startswith('_'):
            if v in dir(s):
                ret = self.get_member_attr_list(v)
            elif hasattr(s, 'property_names') and v in s.property_names():
                ret = self.get_member_attr_list(v)

        if ret is None:
            raise AttributeError(
                '{} do not has attribute {}.'.format(
                    self.get_resource_class().__name__, v))
        return ret

    def get_member_attr_list(self, v):
        return [getattr(i, v) for i in self]

    def _is_updated(self):
        return self._list is not None

    def __add__(self, other):
        if not isinstance(other, ResourceList):
            raise TypeError('Unsupported type {}'.format(type(other)))
        return self.list + other.list


class ResourceListCollection(object):
    def __init__(self, init_list=None):
        if init_list:
            self._items = {rsc_list.get_resource_class(): rsc_list
                           for rsc_list in init_list}
        else:
            self._items = {}
        self.timestamp = datetime.now()

    def add_rsc_list(self, rsc_list):
        if not hasattr(rsc_list, 'get_resource_class'):
            raise ValueError('expect a ResourceList.')
        self._items[rsc_list.get_resource_class()] = rsc_list

    def get_rsc(self, obj):
        ret = None
        rsc_list = self.get_rsc_list(type(obj))
        if rsc_list:
            try:
                ret = rsc_list.get(obj)
            except TypeError:
                raise TypeError('"get(id)" method not found in ResourceList.')
        return ret

    def get_rsc_list(self, rsc_clz):
        return self._items.get(rsc_clz)

    def get_rsc_list_collection(self):
        return self._items.values()

    def get_rsc_clz_list(self):
        return self._items.keys()

    def __len__(self):
        return len(self._items)

    def update(self):
        for rsc_list in self.get_rsc_list_collection():
            rsc_list.update()
        self.timestamp = datetime.now()
        return self

    def delta_seconds(self, other):
        return (self.timestamp - other.timestamp).total_seconds()
