import functools
from unittest import TestCase

import ddt
from hamcrest import assert_that, equal_to, raises

from storops.exception import SystemAPINotSupported
from storops.lib.resource import Resource
from storops.lib.version import version, Criteria
from test.unity.rest_mock import t_rest, patch_rest
from test.vnx.cli_mock import patch_cli, t_cli


class ParentResource(Resource):
    @classmethod
    def parent_cls_method(cls, cli, o):
        return o

    @staticmethod
    def parent_static_method(cli, o):
        return o


@version('>2')
class DemoResource1(ParentResource):
    def __init__(self, cli):
        super(DemoResource1, self).__init__()
        self._cli = cli

    @classmethod
    def cls_method(cls, cli, o):
        return o

    @classmethod
    def cls_method_wo_param(cls):
        return True

    @staticmethod
    def static_method(cli, o):
        return o

    @staticmethod
    def static_method_wo_param():
        return True

    @classmethod
    def _get_parser(cls):
        pass

    def method(self, o):
        return o

    @property
    def system_version(self):
        return self._cli.system_version


class RequireVersionDecorateClassTest(TestCase):
    @patch_cli
    def test_cls_method_in_parent_support(self):
        self._test_cls_or_static_method_support(t_cli('3'),
                                                'parent_cls_method')

    @patch_rest
    def test_cls_method_in_parent_unsupport(self):
        self._test_cls_or_static_method_unsupport(t_rest('2'),
                                                  'parent_cls_method')

    @patch_rest
    def test_static_method_in_parent_support(self):
        self._test_cls_or_static_method_support(t_rest('3'),
                                                'parent_static_method')

    @patch_cli
    def test_static_method_in_parent_unsupport(self):
        self._test_cls_or_static_method_unsupport(t_cli('2'),
                                                  'parent_static_method')

    @patch_cli
    def test_cls_method_support(self):
        self._test_cls_or_static_method_support(t_cli('3'),
                                                'cls_method')

    @patch_rest
    def test_cls_method_unsupport(self):
        self._test_cls_or_static_method_unsupport(t_rest('2'),
                                                  'cls_method')

    @patch_rest
    def test_static_method_support(self):
        self._test_cls_or_static_method_support(t_rest('3'),
                                                'static_method')

    @patch_cli
    def test_static_method_unsupport(self):
        self._test_cls_or_static_method_unsupport(t_cli('2'),
                                                  'static_method')

    def test_static_method_wo_param(self):
        assert_that(DemoResource1.static_method_wo_param(), equal_to(True))

    def test_cls_method_wo_param(self):
        assert_that(DemoResource1.cls_method_wo_param(), equal_to(True))

    @patch_cli
    def test_new_instance_support(self):
        a = DemoResource1(t_cli('3'))
        assert_that(a.method('a'), equal_to('a'))

    @patch_rest
    def test_new_instance_unsupport(self):
        new_obj = functools.partial(DemoResource1, t_rest('2'))
        assert_that(new_obj, raises(SystemAPINotSupported))

    def _test_cls_or_static_method_support(self, cli, method):
        assert_that(getattr(DemoResource1, method)(cli, 'a'), 'a')

    def _test_cls_or_static_method_unsupport(self, cli, method):
        call = functools.partial(getattr(DemoResource1, method), cli, 'a')
        assert_that(call, raises(SystemAPINotSupported))


class DemoResource2(Resource):
    def __init__(self, version):
        super(DemoResource2, self).__init__()
        self.version = version

    @classmethod
    @version('>2')
    def cls_method(cls, cli, o=None):
        return o

    @staticmethod
    @version('>2')
    def static_method(cli, o=None):
        return o

    @version('>2')
    def method(cls):
        return True

    @version('>2')
    def versioned_method(self):
        return '>2'

    @version('<2')  # noqa
    def versioned_method(self):
        return '<2'

    @property
    def system_version(self):
        return self.version


class RequireVersionDecorateMethodTest(TestCase):
    def test_decorate_method(self):
        res = DemoResource2('3')
        re = res.method()
        assert_that(re, equal_to(True))
        res = DemoResource2('1')
        assert_that(res.method, raises(SystemAPINotSupported))

    @patch_cli
    def test_decorate_cls_method_support(self):
        assert_that(DemoResource2.cls_method(t_cli('3'), 'b'), equal_to('b'))

    @patch_cli
    def test_decorate_cls_method_unsupport(self):
        cls_method = functools.partial(DemoResource2.cls_method, t_cli('2'))
        assert_that(cls_method, raises(SystemAPINotSupported))

    @patch_cli
    def test_decorate_static_method_support(self):
        assert_that(DemoResource2.static_method(t_cli('3'), 'b'),
                    equal_to('b'))

    @patch_cli
    def test_decorate_static_method_unsupport(self):
        static_method = functools.partial(DemoResource2.static_method,
                                          t_cli('2'))
        assert_that(static_method, raises(SystemAPINotSupported))

    def test_versioned_method(self):
        res = DemoResource2('3')
        re = res.versioned_method()
        assert_that(re, equal_to('>2'))
        res = DemoResource2('1')
        re = res.versioned_method()
        assert_that(re, equal_to('<2'))
        res = DemoResource2('2')
        assert_that(res.versioned_method, raises(SystemAPINotSupported))


@ddt.ddt
class CriteriaTest(TestCase):
    @ddt.data({'version': '5.0.1', 'criteria': '>5.0', 'result': True},
              {'version': None, 'criteria': '>5.0', 'result': True},
              {'version': '1.0', 'criteria': '>=1.0', 'result': True},
              {'version': '1.0.1', 'criteria': '>=1.0', 'result': True},
              {'version': '2.0.2.1', 'criteria': '<2.0.3', 'result': True},
              {'version': '2.1.a', 'criteria': '<2.0.3', 'result': False},
              {'version': '2.0.3', 'criteria': '<=2.0.3', 'result': True},
              {'version': '2.1.a', 'criteria': '<=2.0.3', 'result': False},
              {'version': '5.0', 'criteria': '=5.0', 'result': True},
              {'version': '5.0', 'criteria': '==5.0', 'result': True},
              {'version': '5.0.1', 'criteria': '= 5.0', 'result': False},
              {'version': '5.0.1', 'criteria': '!= 5.0', 'result': True},
              {'version': '5.0', 'criteria': '!=5.0', 'result': False},
              {'version': '2.1.0.2', 'criteria': '2.0.5<>4.0.3', 'result':
                  True},
              {'version': '4.0.3.1', 'criteria': '2.0.5<>4.0.3',
               'result': False},
              {'version': '5.0.1', 'criteria': '2.0.5<>4.0.3',
               'result': False})
    @ddt.unpack
    def test_criteria_test(self, version, criteria, result):
        criteria = Criteria.parse(criteria)
        assert_that(criteria.test(version), equal_to(result))
