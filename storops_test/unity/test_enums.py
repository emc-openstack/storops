# coding=utf-8
from __future__ import unicode_literals

from unittest import TestCase

from hamcrest import assert_that, equal_to, contains_string, raises, \
    only_contains

from storops.exception import EnumValueNotFoundError
from storops.unity.enums import HealthEnum

__author__ = 'Cedric Zhuang'


class HealthEnumTest(TestCase):
    def test_parse(self):
        assert_that(HealthEnum.parse(5), equal_to(HealthEnum.OK))

    def test_parse_not_found(self):
        def f():
            HealthEnum.parse(-1)

        assert_that(f, raises(EnumValueNotFoundError, 'HealthEnum'))

    def test_verify(self):
        def f():
            HealthEnum.verify(123)

        assert_that(f, raises(ValueError, 'instance of HealthEnum'))

    def test_verify_none(self):
        HealthEnum.verify(None)
        # do not throw any exception

    def test_to_str(self):
        value = str(HealthEnum.OK)
        assert_that(value, contains_string('"description": "OK"'))
        assert_that(value, contains_string('"value": 5'))
        assert_that(value, contains_string('"name": "OK"'))

    def test_name(self):
        assert_that(HealthEnum.enum_name(), equal_to('HealthEnum'))

    def test_enum_item_name(self):
        assert_that(HealthEnum.MINOR.name, equal_to('MINOR'))

    def test_enum_item_index(self):
        assert_that(HealthEnum.MINOR.index, equal_to(15))

    def test_enum_indices(self):
        assert_that(HealthEnum.indices(),
                    only_contains(0, 5, 7, 10, 15, 20, 25, 30))
