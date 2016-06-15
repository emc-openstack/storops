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

from storops.exception import NoIndexException, UnityResourceNotFoundError, \
    UnityNameNotUniqueError
from storops.lib.resource import Resource, ResourceList
from storops.unity import parser

__author__ = 'Cedric Zhuang'


class UnityResource(Resource):
    def __init__(self, _id=None, cli=None):
        super(UnityResource, self).__init__()
        self._id = _id
        self._cli = cli

    @classmethod
    def _get_parser(cls):
        return parser.get_unity_parser(cls.__name__)

    def verify(self):
        if not self.existed:
            raise ValueError(
                'specified {}:{} not exists.'.format(
                    self.__class__.__name__, self.get_id()))
        return self

    def get_id(self):
        ret = None
        if self._id is not None:
            ret = self._id
        elif self._parsed_resource is not None:
            ret = self._parsed_resource.get('id')
            if ret is not None:
                self._id = ret

        if ret is None:
            raise NoIndexException('id is not available for this resource.')
        return ret

    def delete(self, async=False):
        resp = self._cli.delete(self.resource_class, self.get_id(),
                                async=async)
        resp.raise_if_err()
        return resp

    @property
    def resource_class(self):
        return self._get_parser().name

    def _get_raw_resource(self):
        _id = self.get_id()
        return self._cli.get(self.resource_class, _id)

    def _is_updated(self):
        ret = super(UnityResource, self)._is_updated()
        if ret:
            ret &= not (len(self._parsed_resource) == 1 and
                        len(self.property_names()) > 1)
        return ret

    def _get_properties(self, dec=0):
        if dec < 0 and not self._is_updated():
            props = {'hash': self.__hash__(),
                     'id': self.get_id()}
        else:
            props = super(UnityResource, self)._get_properties(dec)
        return props

    def _get_property_from_raw(self, item):
        value = super(UnityResource, self)._get_property_from_raw(item)
        if isinstance(value, UnityResource):
            value.set_cli(self._cli)
        return value

    def set_cli(self, cli):
        if cli is not None:
            self._cli = cli

    @classmethod
    def get(cls, cli, _id=None):
        if not isinstance(_id, cls):
            ret = cls(_id=_id, cli=cli)
        else:
            ret = _id
        return ret

    def _get_unity_rsc(self, clz, _id=None, **filters):
        ret = clz.get(cli=self._cli, _id=_id, **filters)
        if 'name' in filters and filters['name'] is not None:
            name = filters['name']
            clz_name = clz.get_resource_class().__name__
            if len(ret) == 0:
                raise UnityResourceNotFoundError(
                    '{}:{} not found.'.format(clz_name, name))
            elif len(ret) > 1:
                raise UnityNameNotUniqueError(
                    'multiple {} with name {} found.'.format(clz_name, name),
                    # throw out the found multiple objects for later analysis
                    objects=ret)
            else:
                ret = ret[0]
        return ret

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            ret = (self.get_id() == other.get_id())
        else:
            ret = False
        return ret

    def __hash__(self):
        return super(UnityResource, self).__hash__()

    @property
    def doc(self):
        """ Document string of all retrieved properties.

        Return the string that including the description of this resource
        and the the property description of this resource.
        :return: string
        """
        return self._cli.get_doc(self.__class__)

    def action(self, action, **kwargs):
        return self._cli.action(self.resource_class,
                                self.get_id(),
                                action,
                                **kwargs)


class UnitySingletonResource(UnityResource):
    def __init__(self, cli=None):
        super(UnitySingletonResource, self).__init__(self.singleton_id(), cli)

    @classmethod
    def singleton_id(cls):
        return '0'

    @classmethod
    def get(cls, cli, _id=None):
        if not isinstance(_id, cls):
            ret = cls(cli=cli)
        else:
            ret = _id
        return ret


class UnityAttributeResource(UnityResource):
    """ work as an attributes collection of another resource

    This kind of resource don't have individual get or update methods.
    They work as a collection of the attributes of another resource.
    """

    def _get_raw_resource(self):
        raise '{} is not a independent resource.'.format(
            self.__class__.__name__)


class UnityResourceList(UnityResource, ResourceList):
    def __init__(self, cli=None, **the_filter):
        UnityResource.__init__(self, cli=cli)
        ResourceList.__init__(self)
        self._rsc_filter = the_filter

    @classmethod
    def get_resource_class(cls):
        raise NotImplementedError(
            'resource class for {} not implemented.'.format(cls.__name__))

    @classmethod
    def _get_parser(cls):
        return parser.get_unity_parser(cls.get_resource_class().__name__)

    def update(self, data=None):
        ret = super(UnityResourceList, self).update(data)
        for item in self._list:
            item._cli = self._cli
        return ret

    def _get_raw_resource(self):
        the_filter = {}
        _parser = self._get_parser()
        for k, v in self._rsc_filter.items():
            # if k is like host.id for "host.id eq XXX" rest filter
            keys = k.split('.')
            # ingore the left string after '.' since both are ok
            # 'host=<host_id> or {'host.id': <host_id>}'
            label = _parser.get_property_label(keys[0])
            if not label:
                raise ValueError(
                    '"{}" is not a valid property of {}.'.format(
                        k, self.get_resource_class().__name__))
            # support {'host.id': <host_id>}
            if len(keys) == 2:
                label = k
            the_filter[label] = v
        return self._cli.get_all(self.resource_class, the_filter=the_filter)

    def set_cli(self, cli):
        super(UnityResourceList, self).set_cli(cli)
        for item in self:
            if isinstance(item, UnityResource):
                item.set_cli(cli)

    @classmethod
    def get(cls, cli, _id=None, **filters):
        if _id is None:
            ret = cls(cli=cli, **filters)
        else:
            ret = cls.get_resource_class().get(cli=cli, _id=_id)
        return ret

    @classmethod
    def get_list(cls, cli, value):
        if value is None:
            ret = None
        elif isinstance(value, cls):
            ret = value
        elif isinstance(value, (tuple, list, set)):
            ret = [cls.get_resource_class().get(cli, v) for v in value]
        else:
            ret = [cls.get_resource_class().get(cli, value)]
        return ret

    @property
    def first_item(self):
        if len(self) > 0:
            ret = self[0]
        else:
            raise ValueError('no instance available for "{}".'.format(
                self.get_resource_class().resource_class))
        return ret
