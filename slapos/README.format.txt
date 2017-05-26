format
======

slapformat is an application to prepare SlapOS-ready node to be used inside SlapGrid Cloud.

It "formats" the machine by:

 - creating users and groups
 - creating bridge interface
 - creating needed tap interfaces
 - creating TUN interfaces
 - creating needed directories with proper ownership and permissions

It reads configuration from /etc/opt/slapos/slapos.cfg and formats computer
accordingly. The variables are number of partitions, IP addresses, storages
and network interfaces.

Format uploads a into configured SlapOS Master server.

Format dumps allocated resources for the partition into a JSON file per 
partition ~/.slapos-resource. This file contains network interfaces, 
IP address ranges and port ranges. The resource constraints can be 
recursively folded. 

This program shall be only run by root.

Requirements
------------

Linux with IPv6, bridging and tap interface support.

Binaries:

 * brctl
 * groupadd
 * ip
 * tunctl
 * useradd
