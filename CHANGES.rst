Changes
=======

1.14.2 (2025-01-13)
-------------------
 * slapgrid: prevent file corruption for promise history and stats

1.14.1 (2024-12-24)
-------------------
 * slapgrid: fixup! copy .netrc file to buildout home path
 * cli: make resetLogger a context manager restoring the state
 * util: make buildout.download log as debug level when fetching schema
 * tests/example: use .example TLD to prevent lookups
 * tests: use `assertAlmostEqual` for float comparison

1.14.0 (2024-12-03)
-------------------
 * cli: drop legacy `SafeConfigParser`
 * slapgrid: copy .netrc file to buildout home path
 * slap: Use _access_status rather them re-fetch status
 * testing/utils: add findFreeTCPPortRange
 * cli: Nicer error messages for cachelookup binary-sr
 * testcase: make computer_partition_root_path a pathlib.Path
 * testing: accept `pathlib.Path` objects as software URL in tests

1.13.0 (2024-09-16)
-------------------
 * slap: default software_type is now 'default'
 * testing: allow not to request instance in a test.
 * slap: improve invalid instance parameters reporting
 * proxy/db_version: prevent a ResourceWarning
 * testing: don't check bin/phantomjs in checkSoftware

1.12.0 (2024-07-17)
-------------------
 * format: Allow to log when tap has no name attribute
 * testing: tolerates libquadmath in ldd check
 * testing: tolerates libtermcap in ldd check
 * testing: allow permission execution warnings in ldd check
 * slapgrid: better error handling regarding SoftwareReleaseSchema
 * slapgrid: default software-type is now 'default'
 * slapgrid: stop pushing dummy values to shadir

1.11.0 (2024-01-17)
-------------------
* cli/request: allow enforcing a given serialisation
* format: do not remove user from groups
* slapos/testing/e2e: extend base class so that it can request SRs and have them deleted afterwards

1.10.8 (2023-12-14)
-------------------
* slapos/testing: add e2e.py for slapos/software/end-to-end-testing

1.10.7 (2023-12-04)
-------------------
* slap/proxy: use new portal type "Compute Node" instead of "Computer"

1.10.6 (2023-11-30)
-------------------
* slap/hateoas: use new portal type "Compute Node" instead of "Computer"

1.10.5 (2023-11-24)
-------------------
* SlapObject: Fix supervisord config generation

1.10.4 (2023-10-12)
-------------------
* cli/info: Complete "slapos service info" with service names
* grid/utils: Fix untimeouted request in _ReadAsJson

1.10.3 (2023-09-28)
-------------------
* slap/standalone: Fix format with 0 partitions
* slapos/grid: Improve logging regarding networkcache
* slapos/testing: Improve software checks
* slap/standalone: Improve slapos partition formatting
* slapos/testing: Add utils for IPv6-range-aware tests
* cli/slapgrid: Abort before connecting to master when a process is already running
* slapgrid: Fix offline instance processing

1.10.2 (2023-07-07)
-------------------
 * slap/standalone: Increase slapos error log size

1.10.1 (2023-07-03)
-------------------
 * slap/standalone: Use IPv6 range when available
 * testing: Factor snapshot management

1.10.0 (2023-06-21)
-------------------
 * slapgrid: Start services even without connection to master
 * grid/utils: Improve parsing of instance's python

1.9.3 (2023-04-26)
------------------
 * slapgrid: run promise with clean environment
 * slapproxy: Fix Python2 syntax incompatibility
 * slapproxy: Show shared in slapos service list/info
 * cli/info: Report whether the instance is shared
 * slapformat: Fix crash in specific code path
 * cli/info: Include software-type in output
 * slapformat: Fix ipv6_prefixshift typo

1.9.2 (2023-03-24)
------------------
 * console: support args when passing a script file
 * format: fix sapos node format at boot time
 * client: add getInformation shorthand method

1.9.1 (2023-03-22)
------------------
 * format: use correct IPv6 prefix for tap
 * format: allow customising IPv6 range sizes
 * node promise: support --only-cp argument
 * proxy: Fix hateoas for requested state
 * cli/info: Rename instance-state as requested-state
 * cli/info: Include news digest in output

1.9.0 (2023-03-09)
------------------
 * format: add IPv6 range for partitions and tun
 * cli/service info: support connection dict from SlapOS Master
 * slapgrid: Add shared-parts-list to slap-connection
 * proxy: Fix unready forwarded requests causing crash
 * format: remove unneeded call to iptables for tun creation
 * slapgrid: Implement partition timeout parameter (add "partition-timeout" option)

1.8.6 (2023-01-25)
------------------
 * slappopen: fix select-based timeout reads
 * console: fix namespace problems when using slapos console with scripts

1.8.5 (2022-12-14)
------------------
 * slapos: Update SlapOS website's url
 * slapgrid: fix stalling problem when launching promise with SlapPopen

1.8.4 (2022-10-11)
------------------
 * service list, service info: output json
 * request: don't fetch schema for frontend software release, speeding up slapos node instance
 * proxy: update forwarded_partition_request table after destroying a forwarded partition

1.8.3 (2022-10-17)
------------------
 * format: use correct IPv4 for tun interfaces

1.8.2 (2022-10-10)
------------------
 * slapproxy: make rows unique for forwarded requests
 * slapos boot: start computer partitioning without connecting to master
 * cli/request: raise error when serialization type is unknown

1.8.1 (2022-09-06)
------------------
 * nothing changed, new version to replace 1.8.0 which had a packaging mistake

1.8.0 (2022-09-01)
------------------
 * slapos.cfg: add lab.nxdcdn.com endpoint

1.7.13 (2022-07-28)
-------------------
 * format: add more information in os_type

1.7.12 (2022-07-28)
-------------------
 * slapgrid: fix agregateAndSendUsage in python3

1.7.11 (2022-07-21)
-------------------
 * register: fix slapconfig in python3
 * register: no need to be root if configuration file in /tmp
 * networkcache: fix upload_network_cached in python3
 * slapgrid: fix _updateCertificate in python3

1.7.10 (2022-07-11)
-------------------
 * format: fix for python3

1.7.9 (2022-07-06)
------------------
 * util: fix getSerialisation

1.7.8 (2022-06-27)
------------------
 * cli: `slapos --version` now shows Python version too

1.7.7 (2022-06-22)
------------------
 * slapgrid: fix upload command after libnetworkcache version 0.24
 * console: set __file__ like python interpreter would do
 * testing: make the error message more comprehensible

1.7.6 (2022-04-14)
------------------
 * slapgrid: use distro.linux_distribution() to support python >= 3.8
 * slapproxy: add missing instance parameters
 * tests: several improvements
 * standalone: strip ansi codes in logs
 * slapgrid: fix promise logging with instance python
 * cachelookup: introduce slapos cachelookup {url, binary-sr, pypi} commands
 * cache: remove "slapos cache {lookup, source}" commands

1.7.5 (2022-03-21)
------------------
 * slapgrid: fix invocation of bootstrapBuildout

1.7.4 (2022-03-16)
------------------
 * slapgrid: Fix promises not being logged to logfile
 * format: give IPv4 to tap interface only if tap_gateway_interface option is present
 * format: remove use_unique_local_address_block option as it was never really used. User can add a local IPv6 range on the interface before running "slapos node format".

1.7.3 (2022-02-17)
------------------
 * runpromises: support software releases older than slapos 1.0.118
 * Revert "slap lib: disable 'Unverified HTTPS request is being made' messages.". (effectively warning when using insecure connection to master)
 * complete: completions for --only-sr and --only-cp (fish shell only)
 * testing/check_software: several fixes

1.7.2 (2021-12-15)
------------------
 * Add support for different architecture in binary cache
 * cli/cache lookup: better information displayed (architecture and signature)

1.7.1 (2021-12-10)
------------------
 * Fix a missing dependency in 1.7.0 on python2

1.7.0 (2021-12-10)
------------------

 * prune: add support for new name of signature files
 * slapproxy: Fix software URL migration
 * slapgrid: Process promises with instance python
 * grid/utils/setRunning: detect the case where pid has been recycled
 * cli/request: support passing instance parameters from a file
 * slap/request: emit a warning when requesting with parameters not matching schema
 * cli/request: print instance parameters with a consistent format on PY2/PY3

1.6.19 (2021-10-04)
-------------------

 * grid: fix "log buildout output in realtime"

1.6.18 (2021-08-13)
-------------------

 * core: Update certificates as late as possible (re-implemented)
 * cli/prune: Fix a possible infinite recursion
 * grid: log buildout output in realtime 
 * cli/prune: fix a case where parts where not detected as used from a recursive instance

1.6.17 (2021-08-02)
-------------------

 * Fix a problem introduced in 1.6.16 ( core: Update certificates as late as possible )

1.6.16 (2021-07-30)
-------------------

 * slapos.cfg.example: Fix bug introduced in 1.6.14
 * slapgrid: Update certificates as late as possible
 * slap/standalone: don't use --all in waitForSoftware / waitForInstance
 * slapos_*: rename Hosting Subscription to Instance Tree
 * testing/check_software: many improvements
 * collect: fix test
 * core: Update certificates as late as possible


1.6.14 (2021-06-21)
-------------------

 * collect: enable disk usage by default
 * slap/standalone: enable `slapos node format`
 * slapgrid: add `--force-stop` option

1.6.13 (2021-06-01)
-------------------

 * cli/boot: use logger system to have time in logs
 * cli/boot: prevent keyError when no IPv6 at boot
 * slapgrid: note git revision when installing from a git checkout
 * slapproxy: add --local-software-release-root option

1.6.12 (2021-05-05)
-------------------

 * slap/standalone: Add `slapos_bin` option to specify the path of the slapos executable

1.6.11 (2021-05-05)
-------------------

 * slapformat: Fix python3 bytes/str mismatch in dump

1.6.10 (2021-05-03)
-------------------

 * slap/standalone: enable hateoas support in proxy configuration

1.6.9 (2021-04-27)
------------------

 * proxy: add minimal hateoas support (to support "slapos service list", "slapos computer list", ...)
 * testing: add libanl to the list of whitelist libraries

1.6.8 (2021-03-29)
------------------

 * slapgrid: save firewalld rules also if no change, but file not present
 * proxy: always give a name to partition addresses
 * cli: use https://panel.rapid.space by default (instead of https://slapos.vifib.com)
 * slapgrid: execute manager even if promise fails

1.6.7 (2021-03-29)
------------------

 * manager: new whitelistfirewall

1.6.6 (2021-03-08)
------------------

 * manager: use lsblk only in devperm

1.6.5 (2021-02-25)
------------------

  * proxy: prefix forwarded requests to disambiguate them

1.6.4 (2021-02-09)
------------------

  * proxy: don't set app logger level
  * slap/standalone: add slapos-node-auto service
  * slap/standalone: normalize log files in supervisord
  * cli: Output on the console even with --log-file
  * testing: assorted fixes for software upgrade tests

1.6.3 (2020-11-30)
------------------

  * slap/standalone: let standalone's supervisord control instance supervisord
  * cli: Fix slapos node prune usages with root slapos
  * slapgrid: compare os name in lower case,so that binary cache works with debian and Debian
  * grid/utils: set PYTHONNOUSERSITE to prevent issues with broken user site package
  * testing/testcase: Set proper default software type
  * testing/testcase: check eggs for known vulnerabilities
  * cli: fish shell completions
  * proxy: support partitions destruction

1.6.2 (2020-09-17)
------------------

 * grid: Keep using the previous socket path name if it still exists: repairing critical problem introduced in 1.6.1 causing a second supervisor process to start
 * svcbackend: properly log error when supervisord can not be started
 * testing/testcase: snapshot more files

1.6.1 (2020-08-25)
------------------

 * svcbackend/standalone: use shorter names for supervisor sockets
 * testing: several small bug fixes and minor features
 * tests/test_promise: use a larger timeout to prevent false positives

1.6.0 (2020-07-15)
------------------

 * cli: Allow boot and bang commands in non-root environments
 * collect: disable FolderSizeSnapshot for now
 * collect: small optimization on garbage collect
 * grid: Fix OS detection
 * grid: Support non writable files and folders when removing software or partition directories
 * grid: try 3 times to upload archive to binary cache
 * prune: Several bug fixes
 * proxy: support forwarding requests as a partition
 * standalone: support setting multi-master in slapos.cfg
 * testing/testcase: several bug fixes in ldd check and snapshots
 * util: use safe variant or xml_marshaller
 * util: introduce rmtree, a wrapper for shutil.rmtree with support for non writable files and folders

1.5.12 (2020-04-07)
-------------------

 * slapos/slap: fix "slapos service info" when parameter dict is in JSON format

1.5.11 (2020-04-03)
-------------------

 * slapgrid: Fix manager: section support

1.5.10 (2020-04-02)
-------------------

 * prune: fix detection of parts used in scripts
 * manager: Support manager:devperm allowed-disk-for-vm
 * manager: Follow links in devperm

1.5.9 (2020-02-17)
------------------

 * Fixes for Python 3.6
 * cli/boot: read partition base name from config

1.5.8 (2020-02-03)
------------------

  * slapos/collect: Create index for speed up garbage collection
  * slapos/collect: use memory based journal for accelerate response
  * slapos/collect: set auto-commit
  * slapos/collect: Don't invoke create database by default
  * proxy: Support slave removal
  * Extend tests to detect shared libraries using system libraries

1.5.7 (2020-01-15)
------------------

 * slapos/proxy: Update timestamp partition on slave changes, fixes issues with slaves with slapproxy

1.5.6 (2020-01-09)
------------------

 * slapos/grid/promise: Cleanup plugin folder from removed promises and also stale json files for those
 * slapos/grid: Provide download-from-binary-cache-force-url-list option support in slapos.cfg

1.5.5 (2019-12-17)
------------------

  * slapos/format: minimise IPv6 addresses changes

1.5.4 (2019-11-28)
-------------------

  * slapos/format: fix for newer version of netifaces


1.5.3 (2019-11-25)
-------------------

  * slapos/grid/promise: increase default promise timeout from 3 to 20 seconds
  * slapos/proxy: fix loadComputerConfigurationFromXML
  * slapos/cli: minor improvements in commands' help messages


1.5.2 (2019-11-13)
-------------------

  * slapos/grid/promise: Save global and public states
  * slapos/grid/promise: Extend promise system to generate history and stats
  * testcase: Snapshot on setUpClass failure
  * slapos/collect: getint don't support fallback
  * slapos/proxy: setComputerPartitionConnectionXml don't update timestamp


1.5.1 (2019-10-30)
------------------

 * Add new commands ``slapos node promise`` and ``slapos node prune``
 * promise: include promise output in PromiseError
 * grid: remove temporary directory if an exception happens while setting its ownership
 * grid: always check ownership of software path before building
 * slapos/collect: Use UTC time for collector.db time queries
 * collect: what matters is available memory (contrary to unused memory)
 * slapos/collect: Preserve entries at the database for 15 days
 * slapos/collect: Add PartitionReport to replace slapos.toolbox collect code
 * slapos/collect: Call VACUUM to clean up the sql database size.
 * standalone: also cleanup supervisor configuration
 * standalone: Only include 30 lines of error in waitForInstance
 * testcase: improve leaked partitions detection and cleanup
 * testcase: keep generated files and log files between tests
 * testcase: retry ``slapos node report``
 * testcase: enable logging even when in non verbose

1.5.0 (2019-10-03)
-------------------

 * grid: new ``shared_part_list`` configuration file option to define
   which paths can be used by ``slapos.recipe.cmmi`` for shared builds.
 * proxy: bypass frontends requests for direct and KVM frontends, by
   returning the original URL. This way instance promises are successful.
 * slap: new ``StandaloneSlapOS`` class to easily embed slapos node in
   applications.
 * testing: new ``SlapOSInstanceTestCase`` test case useful for software
   releases tests.

1.4.28 (2019-10-01)
-------------------

 * slapos/slap: Stabilise connection_dict
 * slapos: Synchronise xml2dict and dict2xml
 * grid: report summary of partitions processing/promises

1.4.27 (2019-09-17)
-------------------

  * slap/hateoas: in jio_allDocs, increase query limit to 40 if not set
  * slap/hateoas: cleanup, remove unused getRelatedInstanceInformation

1.4.26 (2019-08-13)
-------------------

  * slap/hateoas: Fixes and optimisations 
  * slap/hateoas: Update remaining part of the API to be JIO Complaint
  * slap/promise: treat CRITICAL like ERROR

1.4.25 (2019-08-02)
-------------------

  * slap/hateoas: Fix path for the hateaos API
  * slapproxy: implement softwareInstanceBang
  * slapproxy: skip instanciation if nothing has changed
  * grid: fix typo in GenericPromise.__bang
  * Fixes for Python 3 support

1.4.24 (2019-07-25)
-------------------

  * slap: New API using hateoas
  * slap: Use cachecontrol to be http cache friendly 
  * New command: slapos cache source to check source cache
  * New command: slapos computer [info|list|token]
  * grid: Stabilize service list to prevent supervisord restart


1.4.23 (2019-06-05)
-------------------

 * grid.promise: accelerate the promises.
 * format: add timeout when getting public IPv4.
 * slapos.slap: don't post information about software if not needed.

1.4.22 (2019-04-11)
-------------------

 * slapproxy: make sure slapproxy starts after "slapos configure local"

1.4.21 (2019-03-26)
-------------------

 * slapproxy: remove old tables when running migration. A backup is made as a separate sql file.
 * slapproxy: update database version to 13, to force removal of old tables.
 * format: fix creation of IPv4 for taps

1.4.20 (2019-03-08)
-------------------

 * proxy: Make compatible with xml-marsheller 1.0.2

1.4.19 (2019-03-06)
-------------------

 * format: Make sure routing is OK withVM inside VM
 * grid.promise: cache some promise information to speedup testless and anomalyless checks
 * slapproxy: fix support of non-string (e.g. int) values in requests
 * slapproxy: Support keys with NULL in slave instance

1.4.18 (2019-02-06)
-------------------

 * grid.promise: do no write execution timestamp if running testless or anomalyless promise
 * grid.promise: send EmptyResult if promise is test less or anomaly less

1.4.17 (2019-02-05)
-------------------

 * grid.promise: add support for promise without test or anomaly

1.4.16 (2019-01-14)
-------------------

 * format: new tap_iv6 configuration file option
 * format: dump partition resources information if not exists yet
 * slapgrid: explicitly close partition file logger for instanciation

1.4.15 (2018-12-11)
-------------------

 * format: Bug for tap configuration

1.4.14 (2018-12-04)
-------------------

 * format: Bug fixes 


1.4.13 (2018-11-26)
-------------------

 * Minor fix on MANIFEST.in

1.4.12 (2018-11-26)
-------------------

 * totally deprecate no_bridge and bridge_name options (there was a warning for a long time)
 * create_tap = True won't create tap attached to bridge anymore
     - it should always be used with option tap_gateway_interface
     - if option tap_gateway_interface is not present, the tap will have a default gateway (10.0.0.1)

1.4.11 (2018-09-28)
-------------------

 * slapgrid-sr: do not rebootstrap unnecessarily

1.4.10 (2018-09-20)
-------------------
 * add ``--buildout-debug`` command line option to ``slapos node software`` and
   ``slapos node instance`` commands which starts buildout debugger on errors.
 * pretty print json serialised instance parameters in ``slapos proxy show``
 * Add devperm plugin

1.4.9 (2018-07-31)
------------------
 * slapgrid: Add tear down methods to IManager interface
 * manager: Add Port Redirection manager
 * proxy: create empty slaproxy database if not exits yet
 * slapgrid: Add methods to SlapObject.Partition for more control on generated supervisord config

1.4.8 (2018-06-26)
------------------
 * format: fix brokend parse_computer_definition
 * grid.promise: kill timed out promise process if terminate is not enough
 * grid.promise: avoid blocking process while sending or receiving message from queue
 * grid.promise: on promise timeout fail only if the problem is occurring a second time
 * slapgrid: Do not set minfds. select() does not support file descriptors greater than 1023
 * slapgrid: Set the minimum number of file descriptors.

1.4.7 (2018-04-08)
------------------
 * grid.promise: loadModule is now done in PromiseProcess class
 * collect: fix minors bugs on collect.db and collet.reporter
 * grid: fix using shutil.rmtree to delete file instead of directory 
 * grid: do not hide `$USER` when running buildout
 * grid: do not leak file descriptors to subprocesses when running e.g. 'node software'.

1.4.6 (2018-03-29)
------------------
 * grid.promise: use previous promise execution result if the promise is skipped because of periodicity.
 * slapgrid: update AccessStatus of instance on Master when checking promise anomaly, if the status change.

1.4.5 (2018-03-22)
------------------
 * slapos.collect.db: Create an index on user table to speed up monitor collect query.
 * slapos.cli.console: support new `slapos console script.py` invocation
 * slapos.grid.promise: implement a new promise design and promise launcher in slapgrid
 * slapos.collect: allow connect without call boostrap, set timeout option

1.4.4 (2018-01-25)
------------------
 * slap.initializeConnection: Cache master node's Hateoas URL
 * slapos.grid: Declare connection_parameter_hash explicitly, UnboundLocalError may occur.
 * slapos.grid: rework checkpromise method to utils so it can be reused

1.4.3 (2017-11-08)
------------------
 * slapos.cli.grid: Allow definition of different pidfiles for each software subcommand in config file
 * slapos.cli.configure_local: Get template locally instead do an http request.
 * slapos.cli: Update API for get person certificates and register computer
 * format: fix some conflicts about tun interfaces when changing the number of partitions

1.4.2 (2017-10-02)
------------------
 * slapos.collect: Make internal API usable as library for third parties

1.4.1 (2017-09-25)
------------------
 * slapos.format: Introduce create_tun config option (default false)
 * slapos.cli: get template directly and not reply on namespaces for register
 * slapos.grid: add pluging which run instance custom script at partition pre-destroy phase

1.4.0 (2017-06-26)
------------------
 * slapos.grid: Use local configuration to extend master configuration
 * slapos.format: Export partition configuration for the partition
 * slapos: improve logs and general cleanup
 * slapos.manager: Added cpuset plugin (for cgroups)
 * slapos.format: Add TUN interface support
 * slapos: Implement plugin system

1.3.18 (2016-11-03)
-------------------
 * update default web url of master to slapos.vifib.com

1.3.17 (2016-10-25)
-------------------
 * slapos.grid: Always remove .timestamp and .slapgrid if partition is destroyed.
 * slapos.proxy: Propagate parent partition state to children
 * slapos.grid: Increase min space (1G)
 * slapos.grid: Save slapgrid state into the partition
 * slapos.format: Remove passwd call while format.
 * svcbackend: explicitely call the executable instead of using Popen 'executable' keyword.
 * slapos.grid: Introduce new garbage collector for instances ignored by buildout

1.3.16 (2016-09-29)
-------------------
 * slapos.format: Include disk usage report. Do not divide cpu_load by number of cpu cores.
 * slapos.format: set login shell for slapuser and lock login by password
 * slapos.slap: Do not post same connection parameters of slaves.
 * slapos.proxy: allow to update software release of partition

1.3.15 (2015-12-08)
-------------------
 * slapos.collect: Include disk usage report. Do not divide cpu_load by number of cpu cores.

1.3.14 (2015-10-27)
-------------------
 * slapos.grid: firewall fix bugs

1.3.13 (2015-10-26)
-------------------
 * slapos.grid: firewall accpet option to specify only list of ip address/wetwork to accept and reject.

1.3.12 (2015-10-15)
-------------------
 * slapos.grid: add support for firewall configuration using firewalld for partition that use tap+route interface (for kvm cluster).

1.3.11 (2015-09-25)
-------------------
 * slapos.grid: support shacache-ca-file and shadir-ca-file options.

1.3.10 (2015-04-28)
-------------------

1.3.9 (2015-02-20)
------------------
 * slapos.format: allow to format additional list of folder for each partition to use as data storage location.
 * slapos.format: allow to create tap without bridge (when using option create_tap and tap_gateway_interface), configure ip route with generated ipv4 for tap to access guest vm from host machine.
 * slapos.grid: update generated buildout file with information to acess partition data storage folder.

1.3.8 (2015-02-04)
------------------

 * slapos proxy: allow to specify/override host/port from command line.

1.3.7 (2015-01-30)
------------------

 * slapos.grid: Don't try to process partition if software_release_url is None. Removes noisy errors in log.
 * slapos node report: retry several time when removing processes from supervisor.

1.3.6.3 (2015-01-23)
--------------------

 * slapos: make forbid_supervisord_automatic_launch generic.

1.3.6.2 (2015-01-22)
--------------------

 * slapos.grid.svcbackend: check if watchdog is started before restarting.

1.3.6.1 (2015-01-19)
--------------------

 * slapos: allow to use supervisorctl without automatically starting supervisord.
 * slapos: Create supervisor configuration when running CLI.

1.3.6 (2015-01-16)
------------------

 * supervisord: allow to start with --nodaemon.
 * rename : zc.buildout-bootstap.py -> zc.buildout-bootstrap.py.
 * update bootstrap.py.
 * slapproxy: add missing getComputerPartitionCertificate method
 * slapos boot: fix error reporting when ipv6 is not available

1.3.5 (2014-12-03)
------------------

 * slapos.grid: do not ALWAYS sleep for promise_timeout. Instead, poll often, and continue if promise finished. This change allows a two-folds speed improvement in processing partitions.
 * slapos.format: don't chown recursively Software Releases.
 * slapos.util: use find to chown in chownDirectory.

1.3.4 (2014-11-26)
------------------

 * slapos.slap hateoas: get 'me' document with no cache.
 * slapos.grid: report: fix unbound 'destroyed' variable.
 * slapos.slap: fix __getattr__ of product collection so that product.foo works.
 * slapos.cli info/list: use raw print instead of logger.

1.3.3 (2014-11-18)
------------------

 * slapos.slap/slapos.proxy: Fix regression: requests library ignores empty parameters.
 * slapos.proxy: fix slave support (again)

1.3.2 (2014-11-14)
------------------

 * slapos.slap: parse ipv6 and adds brackets if missing. Needed for requests, that now NEEDS brackets for ipv6.
 * slapos.slap: cast xml from unicode to string if it is unicode before parsing it.

1.3.1 (2014-11-13)
------------------

 * slapos.proxy: fix slave support.

1.3.0 (2014-11-13)
------------------

 * Introduce slapos list and slapos info CLIs.
 * slapos format: fix use_unique_local_address_block feature, and put default to false in configure_local.

1.2.4.1 (2014-10-09)
--------------------

 * slapos format: Don't chown partitions.
 * slapos format: alter_user is true again by default.

1.2.4 (2014-09-23)
------------------

 * slapos.grid: add support for retention_delay.

1.2.3.1 (2014-09-15)
--------------------

 * General: Add compatibility with cliff 1.7.0.
 * tests: Prevent slap tests to leak its stubs/mocks.

1.2.3 (2014-09-11)
------------------

 * slapos.proxy: Add multimaster basic support.

1.2.2 (2014-09-10)
------------------

 * slapos.collect: Compress historical logs and fix folder permissions.

1.2.1 (2014-08-21)
------------------

 * slapproxy: add automatic migration to new database schema if needed.

1.2.0 (2014-08-18)
------------------

Note: not officially released as egg.

 * slapproxy: add correct support for slaves, instance_guid, state.
 * slapproxy: add getComputerPartitionStatus dummy support.
 * slapproxy: add multi-nodes support

1.1.2 (2014-06-02)
------------------

 * Minor fixes

1.1.1 (2014-05-23)
------------------

 * Drop legacy commands
 * Introduced SlapOS node Collect

1.0.5 (2014-04-29)
------------------

 * Fix slapgrid commands return code
 * slapos proxy start do not need to be launched as root

1.0.2.1 (2014-01-16)
--------------------

Fixes:

 * Add backward compabitility in slap lib with older slapproxy (<1.0.1)

1.0.1 (2014-01-14)
------------------

New features:

 * Add configure-local command for standalone slapos [Cedric de Saint Martin/Gabriel Monnerat]

Fixes:

 * Fix slapproxy missing _connection_dict [Rafael Monnerat]

1.0.0 (2014-01-01)
------------------

New features:

 * slapconsole: Use readline for completion and history. [Jerome Perrin]
 * slapos console: support for ipython and bpython [Marco Mariani]
 * Initial windows support. [Jondy Zhao]
 * Support new/changed parameters in command line tools, defined in documentation. [Marco Mariani]
 * Register: support for one-time authentication token. [Marco Mariani]
 * New command: "slapos configure client" [Marco Mariani]
 * add new "root_check" option in slapos configuration file (true by default) allowing to bypass "am I root" checks in slapos. [Cedric de Saint Martin]
 * Add support for getSoftwareReleaseListFromSoftwareProduct() SLAP method. [Cedric de Saint Martin]
 * Add support for Software Product in request, supply and console. [Cedric de Saint Martin]

Major Improvements:

 * Major refactoring of entry points, clearly defining all possible command line parameters, separating logic from arg/conf parsing and logger setup, sanitizing most parameters, and adding help and documentation for each command. [Marco Mariani]
 * Correct handling of common errors: print error message instead of traceback. [Marco Mariani]
 * Dramatically speed up slapformat. [Cedric de Saint Martin]
 * Remove CONFIG_SITE env var from Buildout environment, fixing support of OpenSuse 12.x. [Cedric de Saint Martin]
 * RootSoftwareInstance is now the default software type. [Cedric de Saint Martin]
 * Allow to use SlapOS Client for instances deployed in shared SlapOS Nodes. [Cedric de Saint Martin]

Other fixes:

 * Refuse to run 'slapos node' commands as non root. [Marco Mariani]
 * Register: Replace all reference to vifib by SlapOS Master. [Cedric de Saint Martin]
 * Watchdog: won't call bang if bang was already called but problem has not been solved. [Cédric de Saint Martin]
 * Slapgrid: avoid spurious empty lines in Popen() stdout/log. [Marco Mariani]
 * Slapgrid: Properly include any partition containing any SR informations in the list of partitions to proceed. [Cedric de Saint Martin]
 * Slapgrid: Remove the timestamp file after defined periodicity. Fixes odd use cases when an instance failing to process after some time is still considered as valid by the node. [Cedric de Saint Martin]
 * Slapgrid: Fix scary but harmless warnings, fix grammar, remove references to ViFiB. [Cedric de Saint Martin, Jérome Perrin, Marco Mariani]
 * Slapgrid: Fixes support of Python >= 2.6. [Arnaud Fontaine]
 * Slapgrid: Check if SR is upload-blacklisted only if we have upload informations. [Cedric de Saint Martin]
 * Slapgrid: override $HOME to be software_path or instance_path. Fix leaking files like /opt/slapgrid/.npm. [Marco Mariani]
 * Slapgrid: Always retrieve certificate and key, update files if content changed. Fix "quick&dirty" manual slapos.cfg swaps (change of Node ID). [Marco Mariani]
 * Slapformat: Make sure everybody can read slapos configuration directory. [Cedric de Saint Martin]
 * Slapformat: Fix support of slapproxy. [Marco Mariani]
 * Slapformat: slapos.xml backup: handle corrupted zip files. [Marco Mariani]
 * Slapformat: Don't erase shell information for each user, every time. Allows easy debugging. [Cédric de Saint Martin]


0.35.1 (2013-02-18)
-------------------

New features:

 * Add ComputerPartition._instance_guid getter in SLAP library. [Cedric de Saint Martin]
 * Add ComputerPartition._instance_guid support in slapproxy. [Cedric de Saint Martin]

Fixes:

 * Fix link existence check when deploying instance if SR is not correctly installed. This fixes a misleading error. [Cedric de Saint Martin]
 * Improve message shown to user when requesting. [Cedric de Saint Martin]
 * Raise NotReady when _requested_state doesn't exist when trying to fetch it from getter. [Cedric de Saint Martin]

0.35 (2013-02-08)
-----------------

 * slapos: display version number with help. [Marco Mariani]
 * slapformat: backup slapos.xml to a zip archive at every change. [Marco Mariani]
 * slapformat: Don't check validity of ipv4 when trying to add address that already exists. [Cedric de Saint Martin]
 * slapgrid: create and run $MD5/buildout.cfg for eaiser debugging. [Marco Mariani]
 * slapgrid: keep running if cp.error() or sr.error() have issues (fixes 20130119-744D94). [Marco Mariani]
 * slapgrid does not crash when there are no certificates (fixes #20130121-136C24). [Marco Mariani]
 * Add slapproxy-query command. [Marco Mariani]
 * Other minor typo / output fixes.

0.34 (2013-01-23)
-----------------

 * networkcache: only match major release number in Debian,
                 fixed platform detection for Ubuntu. [Marco Mariani]
 * symlink to software_release in each partition. [Marco Mariani]
 * slapos client: Properly expand "~" when giving configuration file location.
   [Cedric de Saint Martin]
 * slapgrid: stop instances that should be stopped even if buildout and/or
   reporting failed. [Cedric de Saint Martin]
 * slapgrid: Don't periodically force-process a stopped instance. [Cedric de Saint Martin]
 * slapgrid: Handle pid files of slapgrid launched through different entry points.
   [Cedric de Saint Martin]
 * Watchdog: Bang is called with correct instance certificates. [Cedric Le Ninivin]
 * Watchdog: Fix watchdog call. [Cedric le Ninivin]
 * Add a symlink of the used software release in each partitions. [Marco Mariani]
 * slapformat is verbose by default. [Cedric de Saint Martin]
 * slapproxy: Filter by instance_guid, allow computer partition renames
              and change of software_type and requested_state. [Marco Mariani]
 * slapproxy: Stop instance even if buildout/reporting is wrong. [Cedric de Saint Martin]
 * slapproxy: implement softwareInstanceRename method. [Marco Mariani]
 * slapproxy: alllow requests to software_type. [Marco Mariani]
 * Many other minor fixes. See git diff for details.

0.33.1 (2012-11-05)
-------------------

 * Fix "slapos console" argument parsing. [Cedric de Saint Martin]

0.33 (2012-11-02)
-----------------

 * Continue to improve new entry points. The following are now functional:
     - slapos node format
     - slapos node start/stop/restart/tail
     - slapos node supervisord/supervisorctl
     - slapos node supply

   and add basic usage. [Cedric de Saint Martin]
 * Add support for "SLAPOS_CONFIGURATION" and SLAPOS_CLIENT_CONFIGURATION
   environment variables. (commit c72a53b1) [Cédric de Saint Martin]
 * --only_sr also accepts plain text URIs. [Marco Mariani]

0.32.3 (2012-10-15)
-------------------

 * slapgrid: Adopt new return value strategy (0=OK, 1=failed, 2=promise failed)
   (commit 5d4e1522). [Cedric de Saint Martin]
 * slaplib: add requestComputer (commits 6cbe82e0, aafb86eb). [Łukasz Nowak]
 * slapgrid: Add stopasgroup and killasgroup to supervisor (commit 36e0ccc0).
   [Cedric de Saint Martin]
 * slapproxy: don't start in debug mode by default (commit e32259c8).
   [Cédric Le Ninivin
 * SlapObject: ALWAYS remove tmpdir (commit a652a610). [Cedric de Saint Martin]

0.32.2 (2012-10-11)
-------------------

 * slapgrid: Remove default delay, now that SlapOS Master is Fast as Light
   (tm). (commit 03a85d6b8) [Cedric de Saint Martin]
 * Fix watchdog entry point name, introduced in v0.31. (commit a8651ba12)
   [Cedric de Saint Martin]
 * slapgrid: Better filter of instances, won't process false positives anymore
   (hopefully). (commit ce0a73b41) [Cedric de Saint Martin]
 * Various output improvements. [Cedric de Saint Martin]

0.32.1 (2012-10-09)
-------------------

 * slapgrid: Make sure error logs are sent to SlapOS master. Finish
   implementation began in 0.32. [Cedric de Saint Martin]
 * slapgrid: Fix Usage Report in case of not empty partition with no SR.
   [Cedric de Saint Martin]

0.32 (2012-10-04)
-----------------

 * Introduce new, simpler "slapos" entry point. See documentation for more
   informations. Note: some functionnalities of this new entry point don't work
   yet or is not as simple as it should be. [Cedric de Saint Martin, Cedric Le
   Ninivin]
 * Revamped "slapos request" to work like described in documentation. [Cédric
   Le Ninivin, Cédric de Saint Martin]
 * Rewrote slapgrid logger to always log into stdout. (commits a4d277c881,
   5440626dea)[Cédric de Saint Martin]

0.31.2 (2012-10-02)
-------------------

 * Update slapproxy behavior: when instance already exist, only update
   partition_parameter_kw. (commit 317d5c8e0aee) [Cedric de Saint Martin]

0.31.1 (2012-10-02)
-------------------

 * Fixed Watchdog call in slapgrid. [Cédric Le Ninivin]

0.31 (2012-10-02)
-------------------

 * Added slapos-watchdog to bang exited and failing serices in instance
   in supervisord. (commits 16b2e8b8, 1dade5cd7) [Cédric Le Ninivin]
 * Add safety checks before calling SlapOS Master if mandatory instance
   members of SLAP classes are not properly set. Will result in less calls to
   SlapOS Master in dirty cases. (commits 5097e87c9763, 5fad6316a0f6d,
   f2cd014ea8aa) [Cedric de Saint Martin]
 * Add "periodicty" functionnality support for instances: if an instance has
   not been processed by slapgrid after defined time, process it. (commits
   7609fc7a3d, 56e1c7bfbd) [Cedric Le Ninivin]
 * slapproxy: Various improvements in slave support (commits 96c6b78b67,
   bcac5a397d, fbb680f53b)[Cedric Le Ninivin]
 * slapgrid: bulletproof slapgrid-cp: in case one instance is bad, still
   processes all other ones. (commits bac94cdb56, 77bc6c75b3d, bd68b88cc3)
   [Cedric de Saint Martin]
 * Add support for "upload to binary cache" URL blacklist [Cedric de Saint
   Martin]
 * Request on proxy are identified by requester and name (commit
   0c739c3) [Cedric Le Ninivin]

0.30 (2012-09-19)
-----------------

 * Add initial "slave instances" support in slapproxy. [Cedric Le Ninivin]
 * slapgrid-ur fix: check for partition informations only if we have to
   destroy it. [Cedric de Saint Martin]

0.29 (2012-09-18)
-----------------

 * buildout: Migrate slap_connection magic instance profile part to
   slap-connection, and use variables names separated with '-'. [Cedric de
   Saint Martin]
 * slapgrid: Add support for instance.cfg instance profiles [Cedric de Saint
   Martin]
 * slapgrid-ur: much less calls to master. [Cedric de Saint Martin]

0.28.9 (2012-09-18)
-------------------

 * slapgrid: Don't process not updated partitions (regression introduced in
   0.28.7). [Cedric de Saint Martin]

0.28.8 (2012-09-18)
-------------------

 * slapgrid: Don't process free partitions (regression introduced in 0.28.7).
   [Cedric de Saint Martin]

0.28.7 (2012-09-14)
-------------------

 * slapgrid: --maximal_delay reappeared to be used in special cases. [Cedric
   de Saint Martin]

0.28.6 (2012-09-10)
-------------------

 * register now use slapos.cfg.example from master. [Cédric Le Ninivin]

0.28.5 (2012-08-23)
-------------------

 * Updated slapos.cfg for register [Cédric Le Ninivin]

0.28.4 (2012-08-22)
-------------------

 * Fixed egg building.

0.28.3 (2012-08-22)
-------------------

 * Avoid artificial tap creation on system check. [Łukasz Nowak]

0.28.2 (2012-08-17)
-------------------

 * Resolved path problem in register [Cédric Le Ninivin]


0.28.1 (2012-08-17)
-------------------

 * Resolved critical naming conflict

0.28 (2012-08-17)
-----------------

 * Introduce "slapos node register" command, that will register computer to
   SlapOS Master (vifib.net by default) for you. [Cédric Le Ninivin]
 * Set .timestamp in partitions ONLY after slapgrid thinks it's okay (promises,
   ...). [Cedric de Saint Martin]
 * slapgrid-ur: when destroying (not reporting), only care about instances to
   destroy, completely ignore others. [Cedric de Saint Martin]

0.27 (2012-08-08)
-----------------

 * slapformat: Raise correct error when no IPv6 is available on selected
   interface. [Cedric de Saint Martin]
 * slapgrid: Introduce --only_sr and --only_cp.
     - only_sr filter and force the run of a single SR, and uses url_md5
       (folder_id)
     - only_cp filter which computer patition, will be runned. it can be a
       list, splited by comman (slappartX,slappartY ...) [Rafael Monnerat]
 * slapgrid: Cleanup unused option (--usage-report-periodicity). [Cedric de
   Saint Martin]
 * slapgrid: --develop will work also for Computer Partitions. [Cedric de Saint
   Martin]
 * slaplib: setConnectionDict won't call Master if parameters haven't changed.
   [Cedric de Saint Martin]

0.26.2 (2012-07-09)
-------------------

 * Define UTF-8 encoding in SlapOS Node codebase, as defined in PEP-263.

0.26.1 (2012-07-06)
-------------------

 * slapgrid-sr: Add --develop option to make it ignore .completed files.
 * SLAP library: it is now possible to fetch whole dict of connection
   parameters.
 * SLAP library: it is now possible to fetch single instance parameter.
 * SLAP library: change Computer and ComputerPartition behavior to have proper
   caching of computer partition parameters.

0.26 (2012-07-05)
-----------------

 * slapformat: no_bridge option becomes 'not create_tap'.
   create_tap is true by default. So a bridge is used and tap will be created by
   default. [Cedric de Saint Martin]
 * Add delay for slapformat. [Cedric Le Ninivin]
 * If no software_type is given, use default one (i.e fix "error 500" when
   requesting new instance). [Cedric de Saint Martin]
 * slapgrid: promise based software release, new api to fetch full computer
   information from server. [Yingjie Xu]
 * slapproxy: new api to mock full computer information [Yingjie Xu]
 * slapgrid: minor fix randomise delay feature. [Yingjie Xu]
 * slapgrid: optimise slapgrid-cp, run buildout only if there is an update
   on server side. [Yingjie Xu]
 * libslap: Allow accessing ServerError. [Vincent Pelletier]

0.25 (2012-05-16)
-----------------

 * Fix support for no_bridge option in configuration files for some values:
   no_bridge = false was stated as true. [Cedric de Saint Martin]
 * Delay a randomized period of time before calling slapgrid. [Yingjie Xu]
 * slapformat: Don't require tunctl if no_bridge is set [Leonardo Rochael]
 * slapformat: remove monkey patching when creating address so that it doesn't
   return false positive. [Cedric de Saint Martin]
 * Various: clearer error messages.

0.24 (2012-03-29)
-----------------

 * Handles different errors in a user friendly way [Cedric de Saint Martin]
 * slapgrid: Supports software destruction. [Łukasz Nowak]
 * slap: added support to Supply.supply state parameter (available, destroyed)
   [Łukasz Nowak]

0.23 (2012-02-29)
-----------------

 * slapgrid : Don't create tarball of sofwtare release when shacache is not
   configured. [Yingjie Xu]

0.22 (2012-02-09)
-----------------

 * slapformat : Add no-bridge feature. [Cedric de Saint Martin]
 * slapgrid : Add binary cache support. [Yingjie Xu]

0.21 (2011-12-23)
-----------------

 * slap: Add renaming API. [Antoine Catton]

0.20 (2011-11-24)
-----------------

 * slapgrid: Support service-less parttions. [Antoine Catton]
 * slapgrid: Avoid gid collision while dropping privileges. [Antoine Catton]
 * slapgrid: Drop down network usage during usage reporting. [Łukasz Nowak]
 * general: Add sphinx documentation. [Romain Courteaud]

0.19 (2011-11-07)
-----------------

 * bang: Executable to be called by being banged computer. [Łukasz Nowak]

0.18 (2011-10-18)
-----------------

 * Fix 0.17 release: missing change for slap library. [Łukasz Nowak]

0.17 (2011-10-18)
-----------------

 * slap: Avoid request under the hood. [Łukasz Nowak]
 * slap: ComputerPartition.bang provided. It allows to update all instances
   in tree. [Łukasz Nowak]
 * slap: Computer.bang provided. It allows to bang all instances on computer.
   [Łukasz Nowak]

0.16 (2011-10-03)
-----------------

 * slapgrid: Bugfix for slapgrid introduced in 0.15. [Łukasz Nowak]

0.15 (2011-09-27)
-----------------

 * slapgrid: Sanitize environment variables as early as possible. [Arnaud
   Fontaine]
 * slap: Docstring bugfix. [Sebastien Robin]
 * slap: Make request asynchronous call. [Łukasz Nowak]

0.14 (2011-08-31)
-----------------

 * slapgrid: Implement SSL based authentication to shadir and shacache.
   [Łukasz Nowak]
 * slapgrid, slap: Fix usage report packing list generation. [Nicolas Godbert]

0.13 (2011-08-25)
-----------------

 * slapgrid: Implement software signing and shacache upload. [Lucas Carvalho]
 * slap: Support slave instances [Gabriel Monnerat]
 * slapformat: Generate always address for computer [Łukasz Nowak]
 * slapgrid: Support promises scripts [Antoine Catton]
 * general: slapos.core gets tests. [many contributors]

0.12 (2011-07-15)
-----------------

 * Include modifications that should have been included in 0.11.

0.11 (2011-07-15)
-----------------

 * Bug fix : slapconsole : shorthand methods request and supply now correctly
   return an object. [Cedric de Saint Martin]

0.10 (2011-07-13)
-----------------

 * Fix a bug in slapconsole where request and supply shorthand methods
   don't accept all needed parameters. [Cedric de Saint Martin]

0.9 (2011-07-11)
----------------

 * slapconsole: Simplify usage and use configuration file. You can now
   just run slapconsole and type things like "request(kvm, 'mykvm')".
   [Cedric de Saint Martin]
 * slapformat: Fix issue of bridge not connected with real interface on
   Linux >= 2.6.39 [Arnaud Fontaine]
 * slapformat: Allow to have IPv6 only interface, with bridge still supporting
   local IPv4 stack. [Łukasz Nowak]

0.8 (2011-06-27)
----------------

 * slapgrid: Bugfix for temporary extends cache permissions. [Łukasz Nowak]

0.7 (2011-06-27)
----------------

 * slapgrid: Fallback to buildout in own search path. [Łukasz Nowak]

0.6 (2011-06-27)
----------------

 * slap: Fix bug: state shall be XML encapsulated. [Łukasz Nowak]

0.5 (2011-06-24)
----------------

 * slapgrid: Use temporary extends-cache directory in order to make faster
   remote profile refresh. [Łukasz Nowak]

0.4 (2011-06-24)
----------------

 * general: Polish requirement versions. [Arnaud Fontaine]
 * general: Remove libnetworkcache. [Lucas Carvalho]
 * slap: Remove not needed method from interface. [Romain Courteaud]
 * slap: state parameter is accepted and transmitted to SlapOS master [Łukasz
   Nowak]
 * slapformat: Implement dry run. [Vincent Pelletier]
 * slapgrid: Allow to select any buildout binary used to bootstrap environment.
   [Łukasz Nowak]


0.3 (2011-06-14)
----------------

 * slap: Implement SLA by filter_kw in OpenOrder.request. [Łukasz Nowak]
 * slap: Timeout network operations. [Łukasz Nowak]
 * slapformat: Make slapsoft and slapuser* system users. [Kazuhiko Shiozaki]
 * slapgrid: Add more tolerance with supervisord. [Łukasz Nowak]

0.2 (2011-06-01)
----------------

 * Include required files in distribution [Łukasz Nowak]

0.1 (2011-05-27)
----------------

 * Merged slapos.slap, slapos.tool.console, slapos.tool.format,
   slapos.tool.grid, slapos.tool.libnetworkcache and slapos.tool.proxy into one
   package: slapos.core
