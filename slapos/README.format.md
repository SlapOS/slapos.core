SlapOS Format
=============

slap.format is an application to prepare SlapOS-ready node (machine). SlapOS-ready
means that SlapOS package was installed and you edited `/etc/opt/slapos/slapos.cfg`
where you define for example SlapOS master URL, certificates and networking.

It "formats" the machine by:

 - creating users and groups
 - creating and bridging TAP and TUN interfaces
 - creating needed directories with proper ownership and permissions
 - creating custom cgroup groups for better resource controlling

In the end, a report is posted to SlapOS Master and files `.slapos-resources` are
created per-partition so each partition knows what interfaces, network ranges and
other computer resources are assigned to it.

This program shall be only run by root.


Requirements
------------

Linux with IPv6, bridging and tap interface support.

Binaries:

 * brctl
 * groupadd
 * ip
 * useradd
