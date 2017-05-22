SlapOS Core
===========

The core of SlapOS - universal grid management tool based on *Python* and *Buildout*.

Core components

* SLAP Library
* SLAP Grid
* SLAP Format
* SLAP Proxy

Detailed documentation at <https://slaposcore.readthedocs.io/en/latest/>  
Commercial deployment <https://slapos.vifib.com>  


SLAP Format
-----------

Physically prepares computer according to `/etc/opt/slapos/slapos.cfg` and response from the *SlapOS Master*.

Format creates *Partitions* inside `/srv/slapgrid/` with names `slappart<N>` and assign each partition to different user `slapuser<N>`. All users are part of the same group `slapsoft` so they can share some resources.
