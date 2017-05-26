SlapOS Core
===========

The core of SlapOS - universal grid management tool based on *Python* and *Buildout*.


Core components
---------------

* [slapos/README.slap.md][slapos/slap] python library implementing communication protocol between master and nodes via SLAP Protocol
* [slapos/README.grid.md][slapos/grid] tool for software management on nodes
* [slapos/README.format.md][slapos/format] tool for OS preparation to serve as node (does not actually format any hard drives, no worries)
* [slapos/README.proxy.md][slapos/proxy] lightweight local-only implementation of SlapOS Master with limited functionality


ERP5 Modules
------------

* __master/product__ Zope Product for extending ERP5 to become fully-fledged SlapOS Master
* __master/bt5__ ERP5 Business Templates for SlapOS subscription management
* __master/tests__ Test Runner for tests contained within Business Templates


Other links
-----------

Detailed documentation at <https://slaposcore.readthedocs.io/en/latest/>

Commercial deployment <https://slapos.vifib.com>