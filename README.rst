StorOps: The Python Library for VNX & Unity
===========================================

.. image:: https://img.shields.io/travis/emc-openstack/storops.svg
    :target: https://travis-ci.org/emc-openstack/storops
    
.. image:: https://img.shields.io/coveralls/emc-openstack/storops.svg
    :target: https://coveralls.io/github/emc-openstack/storops
    
.. image:: https://img.shields.io/pypi/v/storops.svg
    :target: https://pypi.python.org/pypi/storops

.. image:: https://landscape.io/github/emc-openstack/storops/master/landscape.svg?style=flat
    :target: https://landscape.io/github/emc-openstack/storops/

VERSION: 0.4.2

A minimalist Python library to manage VNX/Unity systems.
This document lies in the source code and go with the release.
Check different release branch/tag for matched documents. 

License
-------

`Apache License version 2`_

Installation
------------

You could use "pip" to install "storops".

.. code-block:: bash

    $ pip install storops

Make sure naviseccli is installed if you want to manage VNX.

*PIP Install Failed?*

Feature List
------------

- Manage VNX System
    - supported resources
        - show system properties
        - list installed features
        - list/create/delete storage pools
        - list/create/delete pool based LUN
        - list/create/delete RAID groups
        - list/create/delete snapshots
        - list/create/delete storage groups
        - list/create/delete consistency groups
        - list/create/delete users
        - list disks
        - list ports
        - list data mover/virtual data mover
        - list NAS storage pool
        - list/create/delete CIFS server
        - list CIFS share
        - list/create/delete file system
        - list/create/delete file system snap
        - list/create/delete NFS share
        - show system domain information
        - list hosts
        - show system capacity
    - supported feature/operations
        - list/start/cancel migration sessions
        - enable/disable LUN deduplication
        - enable/disable LUN compression
        - insert/delete disk simulation
        - create/attach/detach mount points
        - initiator and connection management
        - create/delete mirror view
        - create/delete DNS
    - supported metrics
        - VNXStorageProcessor
            - read/write/total IOPS
            - read/write/total MBPS
            - read/write size KB
        - VNXLun
            - read/write/total IOPS
                - read/write IOPS of SPA
                - read/write IOPS of SPB
            - read/write/total MBPS
                - read/write MBPS of SPA
                - read/write MBPS of SPB
            - implicit/explicit trespasses per second
                - implicit/explicit trespasses per second of SPA
                - implicit/explicit trespasses per second of SPB
            - utilization
                - utilization of SPA
                - utilization of SPB
            - read/write size KB
        - VNXDisk
            - read/write/total IOPS
            - read/write/total MBPS
            - utilization
            - read/write size KB
        - VNXSPPort
            - read/write/total IOPS
            - read/write/total MBPS
            - read/write size KB
        - VNXStorageGroup
            - read/write/total IOPS
            - read/write/total MBPS
            - read/write size KB
        - VNXStoragePool
            - read/write/total IOPS
            - read/write/total MBPS
            - read/write size KB
- Manage Unity System
    - supported resources
        - show system properties
        - list storage pools
        - list/create/delete remote hosts
        - list/create/delete host initiator
        - list/create/delete luns
        - list/create/delete file systems
        - list/create/delete snapshots
        - list/create/delete NAS servers
        - list/create/delete CIFS servers
        - list/create/delete CIFS shares
        - list/create/delete NFS servers
        - list/create/delete NFS shares
        - list/create/delete DNS servers
        - list ip ports
        - list/create/delete link aggregations
        - list/create/delete Consistency Groups
        - list/create/delete metric real time query
        - list metrics query result
        - list disks
        - list/create/delete tenants
    - supported feature/operations
        - CIFS share access control
        - NFS share access control
        - Remote hosts access
        - Persist historical metric data to csv files
    - supported metrics
        - disk
            - read/write IOPS
            - read/write bandwidth
            - utilization
        - lun
            - read/write IOPS
            - read/write bandwidth
            - utilization
        - filesystem
            - read/write IOPS
            - read/write bandwidth
        - storage processor
            - net in/out bandwidth
            - block read/write IOPS
            - block read/write bandwidth
            - CIFS read/write IOPS
            - CIFS read/write bandwidth
            - NFS read/write IOPS
            - NFS read/write bandwidth
            - utilization
            - block cache read/write hit ratio

Tutorial
--------

User may reference three kinds of classes directly.
All of them are available under the storops module.

- system classes: like VNXSystem and UnitySystem
- exceptions: like UnityException, VNXException, etc.
- enums: like VNXProvisionEnum, NFSTypeEnum, etc.

We recommend to try the library with IPython notebook or shell.

All operation/resource are accessed from the system instance.

Here are some examples of the typical usage:

Get the VNX System Instance
```````````````````````````
Use the vnx instance to access all sorts of resource and features.

.. code-block:: python

    # initialize the VNX system instance
    >>> from storops import VNXSystem
    >>> vnx = VNXSystem('10.1.1.1', 'sysadmin', 'password')
    >>> vnx
    {
        "VNXSystem": {
            "existed": true,
            "hash": 5339308,
            "name": "K10",
            "agent_rev": "7.33.8 (2.97)",
            "model_type": "Rackmount",
            "model": "VNX5800",
            "serial": "APM00123456789",
            "revision": "05.33.008.3.297"
        }
    }

Get the Unity System Instance
`````````````````````````````

.. code-block:: python

    from storops import UnitySystem
    unity = UnitySystem('<management ip>', '<user>', '<password>')

Get Resources from System or Other Resources
````````````````````````````````````````````

.. code-block:: python

    # get all pools
    >>> pools = vnx.get_pool()
    {
    "VNXPoolList": [
        {
            "VNXPool": {
                "luns": [
                    1,
                    0
                ],
                "status": "OK(0x0)",
                "current_operation_status": "N/A",
                ...
                "disks": {
                    "VNXDiskList": [
                        {
                            "VNXDisk": {
                                "private": {},
                                "clariion_tla_part_number": "005050344PWR",
                                "prct_bound": {},
    ...

Get a Resource
``````````````

Attention: you could still initialize the python object even
if the resource doesn't exists on array.
You could use the "existed" property to check the existance of the
resource.

.. code-block:: python

    # get a existing LUN
    >>> lun = vnx.get_lun(lun_id=1)
    >>> lun
    {
        "VNXLun": {
            "status": "OK(0x0)",
            "existed": true,
            ...
            "default_owner": "VNXSPEnum.SP_B",
            "name": "l0"
        }
    }

    # get a non-existing lun
    >>> vnx.get_lun(name='hello')
    {
        "VNXLun": {
            "existed": false,
            "hash": 5699430
        }
    }


Access Resource Properties
``````````````````````````
Each properties printed in the json output could be accessed directly.

.. code-block:: python

    # access resource properties
    >>> lun.status
    u'OK(0x0)'


Update the Resource Property
````````````````````````````

All properties of a resource will be updated if any of them is accessed.
For performance concern, the lib won't send query to array once properties
are initialized.
Explicitly call the *"update()"* function if you need a refresh.

.. code-block:: python

    >>> vnx = VNXSystem('10.1.1.3')     # no query to the system
    >>> vnx.model
    u'VNX5800'                          # send query, initialize all properties
    >>> vnx.name
    u'k10'                              # no query
    >>> vnx.update()                    # send query, update all properties


Executing Operations
````````````````````
Most of the create/modify operations can be found on the instance.
Call these instance methods to execute the operation.

.. code-block:: python

    # create lun
    >>> pool = pools[0]
    >>> lun1 = pool.create_lun('lun1', size_gb=2)

Remove a Resource
`````````````````

.. code-block:: python

    # delete a resource
    >>> lun1.delete()

Getting Help
````````````

- If you are using IPython, use "?" to check the document and
  method signature.

.. code-block::

    >>> pool.create_lun?
    Signature: pool.create_lun(lun_name=None, size_gb=1, lun_id=None,
               provision=None, tier=None, ignore_thresholds=None)
    Docstring: Create a pool LUN in the pool.
    File:      c:\work\python\storops\storops\vnx\resource\block_pool.py
    Type:      instancemethod

-  In IPython, use tab to check all extrinsic methods/properties
   of the resource.  Print the resource to check all intrinsic properties.

.. code-block::

    >>> vnx.
    vnx.control_station_ip           vnx.get_property_key             vnx.parse_all
    vnx.create_cg                    vnx.get_property_label           vnx.parsed_resource
    vnx.create_pool                  vnx.get_rg                       vnx.poll
    vnx.create_rg                    vnx.get_sg                       vnx.property_names
    vnx.create_sg                    vnx.get_snap                     vnx.delete_cg
    vnx.domain                       vnx.get_sp_port                  vnx.delete_disk
    vnx.existed                      vnx.heartbeat                    vnx.delete_pool
    vnx.get_available_disks          vnx.install_disk                 vnx.delete_rg
    vnx.get_cg                       vnx.is_auto_tiering_enabled      vnx.delete_sg
    vnx.get_connection_port          vnx.is_compression_enabled       vnx.delete_snap
    vnx.get_dict_repr                vnx.is_dedup_enabled             vnx.set_block_credential
    vnx.get_disk                     vnx.is_fast_cache_enabled        vnx.set_cli
    vnx.get_fc_port                  vnx.is_mirror_view_async_enabled vnx.set_naviseccli
    vnx.get_fcoe_port                vnx.is_mirror_view_enabled       vnx.spa_ip
    vnx.get_index                    vnx.is_mirror_view_sync_enabled  vnx.spb_ip
    vnx.get_iscsi_port               vnx.is_sancopy_enabled           vnx.stop_heart_beat
    vnx.get_lun                      vnx.is_snap_enabled              vnx.update
    vnx.get_migration_session        vnx.is_thin_enabled              vnx.update_nodes_ip
    vnx.get_ndu                      vnx.is_valid                     vnx.with_no_poll
    vnx.get_pool                     vnx.json                         vnx.with_poll
    vnx.get_pool_feature             vnx.parse


How to Contribute
-----------------

#. Open an issue at the `GitHub storops project`_.
#. Fork the repository on GitHub and make changes on your branch.
#. Add tests to cover your change.
#. Send a pull request.
#. Make sure to add yourself to "Contributors" listed below.

Contributors
------------

EMC Contributors
````````````````

- Cedric Zhuang <cedric.zhuang@emc.com>
- Jay Xu <jay.xu@emc.com>
- Ray Chen <ray.chen@emc.com>
- Tina Tang <tina.tang@emc.com>
- Ryan Liang <ryan.liang@emc.com>
- Wang Peter <peter.wang13@emc.com>

Community Contributors
``````````````````````

- Paulo Matias <matias@ufscar.br>

Patches and Suggestions
```````````````````````


.. _GitHub storops project: https://github.com/emc-openstack/storops
.. _Apache License version 2: LICENSE.txt
