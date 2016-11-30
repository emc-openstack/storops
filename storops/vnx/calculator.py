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

import inspect
import os
import sys

from storops.lib.common import cache, all_not_none
from storops.lib.metric import MetricConfigList, MetricConfigParser, \
    CalculatorMetaInfo

__author__ = 'Cedric Zhuang'


def get_counter(props):
    if isinstance(props, (list, tuple, set)):
        if len(props) != 1:
            raise ValueError('takes in one and only one property.')
        props = next(iter(props))
    return props


NaN = float('nan')


def minus(op1, op2):
    if all_not_none(op1, op2):
        ret = op1 - op2
    else:
        ret = NaN
    return ret


def div(op1, op2):
    if all_not_none(op1, op2) and op2 != 0:
        ret = op1 / op2
    else:
        ret = NaN
    return ret


def round_60(value):
    """ round the number to the multiple of 60

    Say a random value is represented by: 60 * n + r
    n is an integer and r is an integer between 0 and 60.
    if r < 30, the result is 60 * n.
    otherwise, the result is 60 * (n + 1)

    The use of this function is that the counter refreshment on
    VNX is always 1 minute.  So the delta time between samples of
    counters must be the multiple of 60.
    :param value: the value to be rounded.
    :return: result
    """
    t = 60
    if value is not None:
        r = value % t
        if r > t / 2:
            ret = value + (t - r)
        else:
            ret = value - r
    else:
        ret = NaN
    return ret


def delta_ps(prev, curr, obj, counters):
    counter = get_counter(counters)

    prev_rsc = prev.get_rsc(obj)
    curr_rsc = curr.get_rsc(obj)

    if all_not_none(prev_rsc, curr_rsc):
        pv = getattr(prev_rsc, counter)
        cv = getattr(curr_rsc, counter)
        dt = round_60(curr.delta_seconds(prev))
        ret = div(minus(cv, pv), dt)
    else:
        ret = NaN
    return ret


def block_to_mbps(prev, curr, obj, counters):
    return delta_ps(prev, curr, obj, counters) * 512 / 2 ** 20


def kb_to_mbps(prev, curr, obj, counters):
    return delta_ps(prev, curr, obj, counters) / 2 ** 10


@cache
def _module_functions():
    return dict(inspect.getmembers(sys.modules[__name__]))


class VNXMetricConfig(object):
    def __init__(self, config):
        self.name = config.get('name')
        self.calculator = self._get_calculator(config)
        self.counters = config.get('counters')

    @staticmethod
    def _get_calculator(config):
        calc_name = config.get('calculator')
        if not calc_name:
            ret = delta_ps
        else:
            ret = _module_functions().get(calc_name)
        return ret


class VNXMetricConfigList(MetricConfigList):
    @classmethod
    def init_metric_config(cls, raw_config):
        return VNXMetricConfig(raw_config)


class VNXMetricConfigParser(MetricConfigParser):
    @classmethod
    def get_config(cls, name):
        name = cls._get_clz_name(name)
        return VNXMetricConfigList(cls._read_configs().get(name))

    @classmethod
    def get_folder(cls):
        return os.path.dirname(inspect.getfile(cls))


class VNXCalculatorMetaInfo(CalculatorMetaInfo):
    def get_config_parser(self):
        return VNXMetricConfigParser()

    def get_metric_value(self, clz, metric_name, cli, obj=None):
        if not hasattr(cli, 'curr_counter'):
            raise ValueError('cli should has "curr_counter" attribute.')
        if not hasattr(cli, 'prev_counter'):
            raise ValueError('cli should has "prev_counter" attribute.')

        config = self.get_config(clz).get_metric_config(metric_name)
        prev = cli.prev_counter
        curr = cli.curr_counter
        if all_not_none(prev, curr):
            ret = config.calculator(prev, curr, obj, config.counters)
        else:
            ret = NaN
        return ret


calculators = VNXCalculatorMetaInfo()
