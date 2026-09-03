slapos.core
===========

The core of SlapOS.
Contains the SLAP library, and the slapos command line tools.
For more information, see https://slapos.nexedi.com/ .

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

The files, all in the partition directory:

``.slapos-master-detach-lock-query``
  Stop asking Master anything: requested state, instance parameters, software
  release, connection parameters, instance guid, certificate, hosting IP list.
  The partition uses what it last saw.

``.slapos-master-detach-lock-modify-state``
  Stop telling Master the partition started, stopped, or was destroyed.

``.slapos-master-detach-lock-modify-connection``
  Stop publishing connection parameters and the related instance list.

``.slapos-master-detach-lock-modify-request``
  Stop asking Master to create or change other instances; ``request()``
  replays the answer it last got for the same instance name.

``.slapos-master-detach-lock-modify-error``
  Stop reporting errors and stop asking Master for re-processing.

File contents are ignored, so a note about who detached the partition and why
can be left inside. A file whose name is not one of the above is an error, not
something to ignore.

touch and rm operations are atomic and simple to implement.

``.slapgrid/master-detach-lock/`` in the partition holds one JSON file per
recorded call, written while the aspect was attached. That is what a query
replays, and where a suppressed modification is kept so that reattaching shows
what the partition wanted to say.

Each file is named ``<aspect>-<method>-<hash>.json``, so listing the directory
says what the partition has recorded and which aspect governs it::

  $ ls /srv/slapgrid/slappartNN/.slapgrid/master-detach-lock/
  modify-error-error-1cee599c...json
  query-getInstanceParameterDict-5c46839c...json
  query-getState-625e2ea3...json
  modify-request-request-b394a0e1...json

The hash keys the arguments the call was made with, so a method called several
ways has one file per way. ``modify-request`` records are keyed on the name of
the instance being requested, one file per instance. Each file holds the
method, those arguments and the recorded answer::

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

Important: Software Release must also use this feature
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

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
