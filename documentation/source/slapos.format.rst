SLAP Format
###########

.. command-output:`slap node format --help`

Format sets up hosting operating system to be ready to accept Software Releases from SlapOS Master.

Format is configured by ``/etc/opt/slapos/slapos.cfg`` where it uses sections ``slapos`` and ``slapformat``.

Config options
==============

interface_name
  Name of outside-facing interface. You can most likely obtain it from the first line
  of ``ip route``. It should be yout gateway interface. Either "eth0" or "p2p1".

create_tap
  whether to create a TAP interface with single IP address assigned from IP network ``ipv4_local_network``

partition_amount
  Number of partitions to create. Every partition will have its own interfaces,
  IP address and other resources. Thus provide sufficiently wide ``ipv4_local_network``
  range.

