grid
====

.. warning::
  This section is outdated, ``slapgrid`` command was reorganised in ``slapos`` sub-commands.


slapgrid is a client of SlapOS. SlapOS provides support for deploying a SaaS
system in a minute.
Slapgrid allows you to easily deploy instances of softwares based on buildout
profiles.
For more informations about SLAP and SlapOS, please see the SLAP documentation.


Requirements
------------

A working SLAP server with informations about your computer, in order to
retrieve them.

As Vifib servers use IPv6 only, we strongly recommend an IPv6 enabled UNIX
box.

For the same reasons, Python >= 2.6 with development headers is also strongly
recommended (IPv6 support is not complete in previous releases).

For now, gcc and glibc development headers are required to build most software
releases.


Concepts
--------

Here are the fundamental concepts of slapgrid : 
A Software Release (SR) is just a software.
A Computer Partition (CP) is an instance of a Software Release.
Imagine you want to install with slapgrid some software and run it. You will
have to install the software as a Software Release, and then instantiate it,
i.e configuring it for your needs, as a Computer Partition.


How it works
------------

When run, slapgrid will authenticate to the SLAP library with a computer_id and
fetch the list of Software Releases to install or remove and Computer
Partitions to start or stop.
Then, it will process each Software Release, and each Computer Partition.
It will also periodically send to SLAP the usage report of each Computer
Partition.


Installation
------------

With easy_install::

  $ easy_install slapgrid

slapgrid needs several directories to be created and configured before being
able to run : a software releases directory, and an instances directory with
configured computer partition directory(ies).
You should create for each Computer Partition directory created a specific user
and associate it with its Computer Partition directory. Each Computer Partition
directory should belongs to this specific user, with permissions of 0750.


Usage
-----

slapgrid needs several informations in order to run. You can specify them by
adding arguments to the slapgrid command line, or by putting then in a
configuration file.
Beware : you need a valid computer resource on server side.


Examples
--------

simple example : 
Just run slapgrid:

  $ slapgrid --instance-root /path/to/instance/root --software-root
  /path/to/software_root --master-url https://some.server/some.resource
  --computer-id my.computer.id


configuration file example::

  [slapgrid]
  instance_root = /path/to/instance/root
  software_root = /path/to/software/root
  master_url = https://slapos.server/slap_service
  computer_id = my.computer.id

then run slapgrid::

  $ slapgrid --configuration-file = path/to/configuration/file


Detaching a partition from SlapOS Master
----------------------------------------

A partition can be detached from SlapOS Master, aspect by aspect, by creating
a file in the partition directory. While an aspect is detached, what would
have crossed to or from Master for that aspect does not: queries replay the
last answer recorded while attached, and modifications are recorded but not
sent.

A detached partition is still processed. ``slapos node instance`` keeps
repairing its buildout, checking its promises and restarting its services --
only Master's influence is held. Detaching is not stopping.

``.slapgrid/master-detach-lock/`` in the partition holds one JSON file per
recorded call, written while the aspect was attached. That is what a query
replays, and where a suppressed modification is kept so that reattaching shows
what the partition wanted to say.

The files, all in the partition directory:

.. list-table::
   :header-rows: 1
   :widths: 24 46 30

   * - File name
     - Description
     - Produced file
   * - ``.slapos-master-detach-lock-query``
     - Stop asking Master anything: requested state, instance parameters,
       software release, connection parameters, instance guid, certificate,
       hosting IP list. The partition uses what it last saw.
     - ``query-<method>-<hash>.json``, one per query answered while attached
   * - ``.slapos-master-detach-lock-modify-state``
     - Stop telling Master the partition started, stopped, or was destroyed.
     - ``modify-state-<method>-<hash>.json``, holding the suppressed report
   * - ``.slapos-master-detach-lock-modify-connection``
     - Stop publishing connection parameters and the related instance list.
     - ``modify-connection-<method>-<hash>.json``, holding what would have
       been published
   * - ``.slapos-master-detach-lock-modify-request``
     - Stop asking Master to create or change other instances; ``request()``
       replays the answer it last got for the same instance name.
     - ``modify-request-request-<hash>.json``, one per requested instance
   * - ``.slapos-master-detach-lock-modify-error``
     - Stop reporting errors and stop asking Master for re-processing.
     - ``modify-error-<method>-<hash>.json``, holding the suppressed message

``.slapos-master-detach-*`` files contents are ignored, so a note about who
detached the partition and why can be left inside.

A file whose name is not one of the above is an error, not something to ignore.

``touch`` and ``rm`` operations are atomic and simple to implement.

Listing that directory therefore says what the partition has recorded and
which aspect governs it::

  $ ls /srv/slapgrid/slappartNN/.slapgrid/master-detach-lock/
  modify-error-error-1cee599c...json
  query-getInstanceParameterDict-5c46839c...json
  query-getState-625e2ea3...json
  modify-request-request-b394a0e1...json

The hash keys the arguments the call was made with, so a method called several
ways has one file per way. Each file holds the method, those arguments and the
recorded answer::

  $ cat .../modify-error-error-1cee599c...json
  {"args": [null], "method": "error",
   "response": "[detached:modify-error] Instance correctly started"}

A partition detached for an aspect it never exercised while attached has
nothing to replay, and the call fails loudly rather than quietly reaching
Master.

A detached partition reports ``#error [detached:...]`` to Master and shows red
in monitoring. That is deliberate: it is not healthy, it is held. Detaching
``modify-error`` suppresses that report, which leaves the partition silent and
indistinguishable from a node that died -- do it only knowingly.

Attention: Software release must also use same this feature
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The partition's own buildout and recipes reach SlapOS Master through the
``slapos.slap`` shipped in the software release, not the one on the node,
so the software release has to be built with a slapos.core that knows
about detaching. A partition built without it keeps its requested state
and software release while still fetching everything else from Master.

Example usage: Upgrading a cluster
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

::

  # before executing the upgrade on partitions which shall not be modified
  touch /srv/slapgrid/slappartNN/.slapos-master-detach-lock-query

  # confirm it took: the partition reports itself detached to Master
  #   #error [detached:query] Instance correctly started

  # ... upgrade, verify, roll back if needed ...

  # release, one partition at a time
  rm /srv/slapgrid/slappartNN/.slapos-master-detach-lock-query

``query`` on its own is the useful default: it is what stops a bad software
release, or a bad Master, from changing a partition that is serving traffic.
The four ``modify`` files are additions on top, needed only when outbound
traffic to Master must stop as well.

Detach **before** upgrading. A partition is protected from the moment the file
exists, and not before; a partition requested for the first time during an
upgrade is not protected at all, because there is nothing recorded for it yet.
