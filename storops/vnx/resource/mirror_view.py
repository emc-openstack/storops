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

from storops.exception import raise_if_err, \
    VNXMirrorException, VNXMirrorImageNotFoundError
from storops.lib.common import check_text, instance_cache
from storops.vnx.enums import VNXMirrorViewRecoveryPolicy
from storops.vnx.enums import VNXMirrorViewSyncRate
import storops.vnx.resource.lun
from storops.vnx.resource import VNXCliResource, VNXCliResourceList

__author__ = 'Cedric Zhuang'


class VNXMirrorViewImage(VNXCliResource):
    @staticmethod
    def get_id(image):
        if isinstance(image, VNXMirrorViewImage):
            image = image.uid
        try:
            image = check_text(image)
        except ValueError:
            raise ValueError('invalid image id supplied: {}'
                             .format(image))
        return image

    @property
    def wwn(self):
        return self.uid


class VNXMirrorViewImageList(VNXCliResourceList):
    @classmethod
    def get_resource_class(cls):
        return VNXMirrorViewImage


class VNXMirrorView(VNXCliResource):
    def __init__(self, name=None, cli=None):
        super(VNXMirrorView, self).__init__()
        self._cli = cli
        self._name = name

    def _get_raw_resource(self):
        return self._cli.get_mirror_view(name=self._name, poll=self.poll)

    @classmethod
    def create(cls, cli, name, src_lun, use_write_intent_log=True):
        lun_clz = storops.vnx.resource.lun.VNXLun
        lun_id = lun_clz.get_id(src_lun)
        out = cli.create_mirror_view(name, lun_id, use_write_intent_log)
        raise_if_err(out, default=VNXMirrorException)
        return VNXMirrorView(name, cli=cli)

    @classmethod
    def get(cls, cli, name=None):
        if name is None:
            ret = VNXMirrorViewList(cli)
        else:
            ret = VNXMirrorView(name, cli)
        return ret

    def add_image(self, sp_ip, lun_id,
                  recovery_policy=VNXMirrorViewRecoveryPolicy.AUTO,
                  sync_rate=VNXMirrorViewSyncRate.HIGH):
        if hasattr(sp_ip, 'spa_ip'):
            sp_ip = sp_ip.spa_ip

        lun_clz = storops.vnx.resource.lun.VNXLun
        lun_id = lun_clz.get_id(lun_id)
        out = self._cli.add_mirror_view_image(self._get_name(), sp_ip, lun_id,
                                              recovery_policy, sync_rate,
                                              poll=self.poll)
        raise_if_err(out, default=VNXMirrorException)

    def get_image(self, image_id):
        for image in self.images:
            if image.uid == image_id:
                ret = image
                break
        else:
            raise VNXMirrorImageNotFoundError(
                'image {} not found in mirror view {}.'.format(
                    image_id, self._get_name()))
        return ret

    @staticmethod
    def _get_image_id(image_id):
        return VNXMirrorViewImage.get_id(image_id)

    @property
    @instance_cache
    def primary_image(self):
        for image in self.images:
            if image.is_primary:
                ret = image
                break
        else:
            ret = None
        return ret

    @property
    @instance_cache
    def secondary_image(self):
        for image in self.images:
            if not image.is_primary:
                ret = image
                break
        else:
            ret = None
        return ret

    @property
    def is_primary(self):
        return self.remote_mirror_status == 'Mirrored'

    @property
    def primary_image_id(self):
        return self.primary_image.uid

    @property
    def secondary_image_id(self):
        image = self.secondary_image
        if image is None:
            raise VNXMirrorImageNotFoundError(
                'no secondary image exists for this mirror view.')
        return image.uid

    def remove_image(self, image_id=None):
        if image_id is None:
            image_id = self.secondary_image_id

        image_id = self._get_image_id(image_id)
        out = self._cli.delete_mirror_view_image(self._get_name(), image_id,
                                                 poll=self.poll)
        raise_if_err(out, default=VNXMirrorException)

    def fracture_image(self, image_id=None):
        if image_id is None:
            image_id = self.secondary_image_id

        image_id = self._get_image_id(image_id)
        out = self._cli.mirror_view_fracture_image(self._get_name(), image_id,
                                                   poll=self.poll)
        raise_if_err(out, default=VNXMirrorException)

    def sync_image(self, image_id=None):
        if image_id is None:
            image_id = self.secondary_image_id

        image_id = self._get_image_id(image_id)
        out = self._cli.mirror_view_sync_image(self._get_name(), image_id,
                                               poll=self.poll)
        raise_if_err(out, default=VNXMirrorException)

    def promote_image(self, image_id=None):
        if image_id is None:
            image_id = self.secondary_image_id

        image_id = self._get_image_id(image_id)
        out = self._cli.mirror_view_promote_image(self._get_name(), image_id,
                                                  poll=self.poll)
        raise_if_err(out, default=VNXMirrorException)

    def delete(self, force=False):
        if force:
            if self.secondary_image:
                self.remove_image()

        out = self._cli.delete_mirror_view(self._get_name())
        raise_if_err(out, default=VNXMirrorException)


class VNXMirrorViewList(VNXCliResourceList):
    @classmethod
    def get_resource_class(cls):
        return VNXMirrorView

    def __init__(self, cli=None, src_lun=None, tgt_lun=None):
        super(VNXMirrorViewList, self).__init__()
        self._cli = cli
        self._src_lun = src_lun
        self._tgt_lun = tgt_lun

    def _filter(self, item):
        if self._src_lun is None and self._tgt_lun is None:
            ret = True
        else:
            ret = False
            pi = item.primary_image
            si = item.secondary_image
            if self._src_lun is not None:
                ret |= self._src_lun.wwn == pi.logical_unit_uid
            if self._tgt_lun is not None and si is not None:
                ret |= self._tgt_lun.wwn == si.logical_unit_uid
        return ret

    def _get_raw_resource(self):
        return self._cli.get_mirror_view(poll=self.poll)
