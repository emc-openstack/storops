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

import os

import yaml

from storops.lib.common import RepeatedTimer, cache
from storops.lib.resource import ResourceList

__author__ = 'Cedric Zhuang'


class MetricCounterRecords(object):
    """ Data structure to save metric counter in memory
    """

    def __init__(self, maximum=None):
        self.enabled = False
        if maximum is None:
            maximum = 2
        self._maximum_len = maximum
        self._records = []

    def add_results(self, result):
        self.enabled = True
        if result is not None:
            self._records.insert(0, result)
            while len(self._records) > self._maximum_len:
                self._records.pop()

    def reset(self):
        self.enabled = False
        self._records = []

    def __len__(self):
        return len(self._records)

    @property
    def curr(self):
        if self.enabled and len(self._records) > 0:
            ret = self._records[0]
        else:
            ret = None
        return ret

    @property
    def prev(self):
        if self.enabled and len(self._records) > 1:
            ret = self._records[1]
        else:
            ret = None
        return ret


class PerfManager(object):
    def __init__(self):
        self.metric_collector = None
        self._rsc_list_2 = None
        self._rsc_clz_list = None
        self.metric_counter_records = MetricCounterRecords()

    def persist_rsc_list_metrics(self):
        persist_rsc_list = self.get_persist_rsc_list()
        if self.prev_counter and persist_rsc_list:
            for rsc_list in persist_rsc_list:
                rsc_list.update()
                rsc_list.persist_metric_data()

    def _is_perf_monitored(self, rsc):
        if self._rsc_clz_list is not None:
            if isinstance(rsc, ResourceList):
                clz = rsc.get_resource_class()
            else:
                clz = type(rsc)
            ret = clz in self._rsc_clz_list
        else:
            ret = True
        return ret

    def get_persist_rsc_list(self):
        if self._rsc_list_2 is not None:
            ret = [rsc_list
                   for rsc_list in self._rsc_list_2
                   if self.is_perf_metric_enabled(rsc_list)]
        else:
            ret = []
        return ret

    def enable_perf_metric(self, interval, callback, rsc_clz_list=None):
        self._rsc_clz_list = rsc_clz_list

        def f():
            self.metric_counter_records.add_results(callback())
            self.persist_rsc_list_metrics()

        if self.metric_counter_records.enabled:
            self.disable_perf_metric()

        self.metric_counter_records.enabled = True
        if interval > 0:
            self.metric_collector = RepeatedTimer(interval, f)
            self.metric_collector.start()

    def disable_perf_metric(self):
        if self.metric_collector:
            self.metric_collector.stop()
        self.metric_counter_records.reset()

    def is_perf_metric_enabled(self, rsc=None):
        ret = self.metric_counter_records.enabled
        if rsc is not None and ret:
            ret &= self._is_perf_monitored(rsc)
        return ret

    @property
    def prev_counter(self):
        return self.metric_counter_records.prev

    @property
    def curr_counter(self):
        return self.metric_counter_records.curr

    def __del__(self):
        self.disable_perf_metric()

    def persist_perf_stats(self, perf_rsc_list):
        self._rsc_list_2 = perf_rsc_list

    def is_perf_stats_persisted(self):
        return self._rsc_list_2 is not None and len(self._rsc_list_2) > 0

    def add_metric_record(self, record):
        self.metric_counter_records.add_results(record)


class MetricConfigList(object):
    def __init__(self, inputs):
        if inputs is None:
            inputs = []
        self._metric_configs = {
            config.get('name'): self.init_metric_config(config)
            for config in inputs}

    def init_metric_config(self, raw_config):
        raise NotImplementedError('should be implemented by child class.'
                                  'init config from dict.')

    def metric_names(self):
        return sorted(self._metric_configs.keys())

    def get_calculator(self, metric_name):
        return self.get_metric_config(metric_name).calculator

    def get_metric_config(self, metric_name):
        if metric_name not in self._metric_configs:
            raise ValueError('calculator for metric "{}" not found in {}.'
                             .format(metric_name, self._metric_configs))
        return self._metric_configs[metric_name]

    def paths(self):
        return [path
                for config in self._metric_configs.values()
                for path in config.paths]


class MetricConfigParser(object):
    config_filename = 'metric_configs.yaml'

    @classmethod
    def get_folder(cls):
        raise NotImplementedError('should be implemented by child class.'
                                  'returns the folder of metric_configs.yaml')

    @classmethod
    def get_config(cls, name):
        raise NotImplementedError('should be implemented by child class.'
                                  'return the metric config instance.')

    @classmethod
    @cache
    def _read_configs(cls):
        filename = os.path.join(cls.get_folder(), cls.config_filename)
        with open(filename, 'r') as stream:
            ret = yaml.load(stream)
        return ret

    @classmethod
    def _get_clz_name(cls, name):
        if isinstance(name, type):
            name = name.__name__.split('.')[-1]
        return name


class CalculatorMetaInfo(object):
    def __init__(self):
        self._metric_config = self.get_config_parser()

    def get_config_parser(self):
        raise NotImplementedError('should be implemented by child class.'
                                  'return the config parser class.')

    def get_calculator(self, clz, metric_name):
        config_list = self.get_config(clz)
        return config_list.get_calculator(metric_name)

    def get_config(self, clz):
        return self._metric_config.get_config(clz)

    def get_metric_names(self, clz):
        return self.get_config(clz).metric_names()

    def get_metric_value(self, clz, metric_name, cli, obj=None):
        raise NotImplementedError('should be implemented by child class.'
                                  'return the calculated metric value.')


class MetricsDumper(object):
    def __init__(self, rsc_list, dft_hdr=None, dft_hdr_cb=None):
        if dft_hdr is None:
            dft_hdr = []
        if dft_hdr_cb is not None and not callable(dft_hdr_cb):
            raise TypeError('dft_hdr_cb should be a function takes in a rsc '
                            'and returns a string list.')

        self._rsc_list = rsc_list
        self._dft_hdr = dft_hdr
        self._dft_hdr_cb = dft_hdr_cb

    @property
    def metric_names(self):
        return self._rsc_list.metric_names()

    def get_metrics_csv(self, sep=None):
        if sep is None:
            sep = ','
        content = [self.get_metrics_csv_header(sep),
                   self.get_metrics_csv_data(sep)]
        return '\n'.join(content)

    def data_line(self, rsc):
        if self._dft_hdr_cb is not None:
            metrics = self._dft_hdr_cb(rsc)
        else:
            metrics = []
        metrics += [str(self.get_attr(rsc, name))
                    for name in self.metric_names]
        return metrics

    @staticmethod
    def get_attr(rsc, name):
        if hasattr(rsc, name):
            ret = getattr(rsc, name)
        else:
            ret = rsc.get(name)
        return ret

    def get_metrics_csv_data(self, sep=None):
        if sep is None:
            sep = ','
        return '\n'.join(sep.join(self.data_line(r)) for r in self._rsc_list)

    def get_metrics_csv_header(self, sep=None):
        if sep is None:
            sep = ','
        return sep.join(self._dft_hdr + self.metric_names)

    def persist_metric_data(self, filename=None):
        if filename is None:
            raise ValueError('filename should not be none.')

        if os.path.exists(filename):
            to_write = self.get_metrics_csv_data()
        else:
            to_write = self.get_metrics_csv()

        with open(filename, 'a+') as f:
            f.write(to_write)
            f.write('\n')
