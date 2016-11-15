# coding=utf-8
# Copyright (c) 2016 EMC Corporation.
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

from storops.lib.common import instance_cache, clear_instance_cache
from storops.unity.calculator import IdValues
from storops.unity.resource import UnityResource, UnityResourceList

__author__ = 'Cedric Zhuang'


class UnityMetric(UnityResource):
    pass


class UnityMetricList(UnityResourceList):
    @classmethod
    def get_resource_class(cls):
        return UnityMetric


class UnityMetricRealTimeQuery(UnityResource):
    @classmethod
    def get_query_list(cls, cli, interval, paths):
        queries = UnityMetricRealTimeQueryList(cli=cli, interval=interval)
        queries.sort_by_path()
        paths = set(paths)
        id_list = []
        for query in queries:
            query_paths = set(query.paths)
            if query_paths.intersection(paths):
                id_list.append(query.get_id())
                paths -= query_paths
        if paths:
            id_list.append(cls.create(cli, interval, list(paths)).get_id())
            queries.update()
        return queries.set_id_list(id_list)

    @classmethod
    def create(cls, cli, interval, paths):
        resp = cli.post(cls().resource_class, interval=interval, paths=paths)
        resp.raise_if_err()
        return cls(_id=resp.resource_id, cli=cli)

    def get_query_result(self, paths=None):
        results = UnityMetricQueryResultList(
            cli=self._cli, query_id=self.get_id())
        return results.filtered_by_path(paths)


class UnityMetricRealTimeQueryList(UnityResourceList):
    def __init__(self, cli=None, interval=None, id_list=None):
        super(UnityMetricRealTimeQueryList, self).__init__(cli)
        self._interval = interval
        self._id_list = id_list

    def set_id_list(self, id_list):
        self._id_list = id_list
        self._apply_filter()
        return self

    @classmethod
    def get_resource_class(cls):
        return UnityMetricRealTimeQuery

    def sort_by_path(self, reverse=True):
        if self._list is None:
            self.update()
        if self._list is not None:
            self._list.sort(key=lambda q: len(q.paths), reverse=reverse)

    def _filter(self, item):
        ret = True
        if self._interval is not None:
            ret &= item.interval == self._interval
        if self._id_list is not None:
            ret &= item.id in self._id_list

        return ret

    def get_query_result(self, paths=None):
        ret = None
        for query in self:
            result = query.get_query_result(paths)
            if ret is None:
                ret = result
            else:
                ret.merge(result)
        return ret


class UnityMetricQueryResult(UnityResource):
    @instance_cache
    def sum_sp(self):
        return sum(self.numeric_values)

    @property
    @instance_cache
    def numeric_values(self):
        if self.values is None:
            ret = []
        else:
            ret = [IdValues({k: int(v) for k, v in value.items()})
                   for value in self.values.values()]
        return ret

    @property
    def sp_values(self):
        if self.values is None:
            ret = IdValues()
        else:
            ret = IdValues({k: int(v) for k, v in self.values.items()})
        return ret

    def diff_timestamp(self, other):
        if other is None:
            ret = None
        else:
            ret = self.timestamp - other.timestamp
        return ret

    def diff_seconds(self, other):
        if other is None:
            ret = None
        else:
            ret = abs(self.diff_timestamp(other).total_seconds())
        return ret


class UnityMetricQueryResultList(UnityResourceList):
    def __init__(self, cli=None, **the_filter):
        super(UnityMetricQueryResultList, self).__init__(cli, **the_filter)
        self._path_result_map = {}

    @classmethod
    def get_resource_class(cls):
        return UnityMetricQueryResult

    @clear_instance_cache
    def update(self, data=None):
        super(UnityMetricQueryResultList, self).update(data)
        self._path_result_map = {}

    def by_path(self, path):
        if not self._path_result_map:
            for r in self:
                self._path_result_map[r.path] = r
        return self._path_result_map.get(path)

    def diff_seconds(self, other):
        if other is None or len(other) == 0 or len(self) == 0:
            ret = None
        else:
            ret = self[0].diff_seconds(other[0])
        return ret

    def filtered_by_path(self, paths=None):
        if paths is not None:
            self._list = [q for q in self if q.path in paths]
        return self

    def merge(self, other):
        if other is not None:
            my_paths = self.path
            to_add = [r for r in other if r.path not in my_paths]
            if self._list is None:
                self._list = []
            self._list.extend(to_add)
