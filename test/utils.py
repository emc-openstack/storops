# coding=utf-8
from __future__ import unicode_literals

import doctest
import logging

import mock
import six
from lxml import doctestcompare

__author__ = 'Jay Xu'

log = logging.getLogger(__name__)

CHECKER = doctestcompare.LXMLOutputChecker()
PARSE_XML = doctest.register_optionflag('PARSE_XML')


class RequestSideEffect(object):
    def __init__(self):
        self.actions = []
        self.started = False

    def append(self, resp=None, ex=None):
        if not self.started:
            self.actions.append((resp, ex))

    def __call__(self, *args, **kwargs):
        if not self.started:
            self.started = True
            self.actions.reverse()
        item = self.actions.pop()
        if item[1]:
            raise item[1]
        else:
            return item[0]


class SSHSideEffect(object):
    def __init__(self):
        self.actions = []
        self.started = False

    def append(self, resp=None, err=None, ex=None):
        if not self.started:
            self.actions.append((resp, err, ex))

    def __call__(self, rel_url, req_data=None, method=None,
                 return_rest_err=True, *args, **kwargs):
        if not self.started:
            self.started = True
            self.actions.reverse()
        item = self.actions.pop()
        if item[2]:
            raise item[2]
        else:
            if return_rest_err:
                return item[0:2]
            else:
                return item[1]


class EMCMock(mock.Mock):
    @staticmethod
    def _get_req_from_call(call):
        if len(call) == 3:
            return call[1][0]
        elif len(call) == 2:
            return call[0][0]

    def assert_has_calls(self, calls):
        if len(calls) != len(self.mock_calls):
            raise AssertionError(
                'Mismatch error.\nExpected: %r\n'
                'Actual: %r' % (calls, self.mock_calls)
            )

        iter_expect = iter(calls)
        iter_actual = iter(self.mock_calls)

        while True:
            try:
                expect = self._get_req_from_call(next(iter_expect))
                actual = self._get_req_from_call(next(iter_actual))
            except StopIteration:
                return True

            if not isinstance(expect, six.binary_type):
                expect = six.b(expect)
            if not isinstance(actual, six.binary_type):
                actual = six.b(actual)
            if not CHECKER.check_output(expect, actual, PARSE_XML):
                raise AssertionError(
                    'Mismatch error.\nExpected: %r\n'
                    'Actual: %r' % (calls, self.mock_calls)
                )


class EMCNFSShareMock(mock.Mock):
    def assert_has_calls(self, calls):
        if len(calls) != len(self.mock_calls):
            raise AssertionError(
                'Mismatch error.\nExpected: %r\n'
                'Actual: %r' % (calls, self.mock_calls)
            )

        iter_expect = iter(calls)
        iter_actual = iter(self.mock_calls)

        while True:
            try:
                expect = next(iter_expect)[1][0]
                actual = next(iter_actual)[1][0]
            except StopIteration:
                return True

            if not self._option_check(expect, actual):
                raise AssertionError(
                    'Mismatch error.\nExpected: %r\n'
                    'Actual: %r' % (calls, self.mock_calls)
                )

    @staticmethod
    def _option_parser(option):
        option_map = {}
        for item in option.split(','):
            key, value = item.split('=')
            option_map[key] = value

        return option_map

    def _option_check(self, expect, actual):
        if '-option' in actual and '-option' in expect:
            exp_option = expect[expect.index('-option') + 1]
            act_option = actual[actual.index('-option') + 1]

            exp_opt_map = self._option_parser(exp_option)
            act_opt_map = self._option_parser(act_option)

            for key in exp_opt_map:
                exp_set = set(exp_opt_map[key].split(':'))
                act_set = set(act_opt_map[key].split(':'))
                if exp_set != act_set:
                    return False

        return True
