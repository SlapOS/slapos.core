PRAGMA foreign_keys=OFF;
BEGIN TRANSACTION;
CREATE TABLE computer18 (
  reference VARCHAR(255) DEFAULT 'slaprunner',
  address VARCHAR(255),
  netmask VARCHAR(255),
  PRIMARY KEY (reference)
);
INSERT INTO "computer18" VALUES('slaprunner','10.0.30.235','255.255.255.255');
CREATE TABLE config18 (
  name TEXT PRIMARY KEY,
  value TEXT
) WITHOUT ROWID;
INSERT INTO "config18" VALUES('last_instance_id','0');
INSERT INTO "config18" VALUES('local_software_release_root','/');
CREATE TABLE forwarded_partition_request18 (
  partition_reference VARCHAR(255), -- a.k.a source_instance_id
  master_url VARCHAR(255),
  PRIMARY KEY (partition_reference, master_url)
);
CREATE TABLE instance18 (
  instance_guid VARCHAR(255) PRIMARY KEY,
                              -- opaque, immutable. Minted 'SOFTINST-N' for new
                              -- instances; for instances migrated from v17 it is
                              -- the guid the proxy had already published for them
                              -- (frozen verbatim). NEVER derived, NEVER parsed.
  title VARCHAR(255) NOT NULL,                          -- mutable, NOT identity
  shared INTEGER NOT NULL DEFAULT 0,
  root_instance_guid VARCHAR(255) NOT NULL DEFAULT '',
                              -- instance_guid of the tree root; '' = IS a root
  requested_by_instance_guid VARCHAR(255) NOT NULL DEFAULT '',
                              -- instance_guid of the DIRECT requester;
                              -- '' = requested directly by the user
  software_release VARCHAR(255),
  software_type VARCHAR(255),
  requested_state VARCHAR(255) NOT NULL DEFAULT 'started',
                              -- real state for shared instances too
  xml TEXT,                   -- requested parameters
  connection_xml TEXT,
  sla_xml TEXT,               -- stored verbatim at request time; allocation
                              -- stays synchronous -- never read by the
                              -- allocator, kept for master-model fidelity
  slave_reference VARCHAR(255),
                              -- shared rows only: the frozen legacy wire
                              -- reference ('<asked_by>_<title>') used by the
                              -- slave_instance_list projection; NULL for
                              -- non-shared rows
  allocated_computer VARCHAR(255),
  allocated_partition VARCHAR(255),
                              -- together: nullable FK -> partition. For shared
                              -- rows this is the HOSTING partition.
  timestamp REAL              -- processing timestamp (wire processing_timestamp)
);
INSERT INTO "instance18" VALUES('slaprunner-slappart0','slaprunner-dev-local-frontend-2',0,'','','/srv/slapgrid/slappart8/srv/runner/project/slapos/software/erp5/software.cfg','default','started','<?xml version=''1.0'' encoding=''utf-8''?>
<instance>
  <parameter id="_">{
  "mariadb": {
    "innodb-buffer-pool-size": 1073741824, 
    "innodb-log-file-size": 134217728
  }, 
  "site-id": "erp5", 
  "timezone": "Asia/Tokyo", 
  "zodb": [
    {
      "cache-size": 50000, 
      "mount-point": "/", 
      "name": "root", 
      "server": {
        "family": "1"
      }, 
      "storage-dict": {
        "cache-size": "20MB"
      }, 
      "type": "zeo"
    }
  ], 
  "zope-partition-dict": {
    "activities": {
      "family": "activities", 
      "instance-count": 4, 
      "thread-amount": 2, 
      "timerserver-interval": 1
    }, 
    "backend": {
      "family": "login", 
      "instance-count": 2, 
      "longrequest-logger": {
        "interval": 1, 
        "timeout": 2
      }, 
      "thread-amount": 10, 
      "timerserver-interval": 1
    }
  }
}</parameter>
</instance>
','<?xml version=''1.0'' encoding=''utf-8''?>
<instance>
  <parameter id="_">{"hosts-dict": {"erp5-cloudooo": "cloudooo.erp5.net", "erp5-smtp": "127.0.0.2", "erp5-catalog-0": "10.0.30.235", "erp5-memcached-volatile": "10.0.30.235", "erp5-memcached-persistent": "10.0.30.235"}, "login-test-runner-url-list": ["https://10.0.30.235:2157/unit_test_0/", "https://10.0.30.235:2157/unit_test_1/", "https://10.0.30.235:2157/unit_test_2/"], "monitor-setup-url": "https://monitor.app.officejs.com/#page=settings_configurator&amp;url=/public/feeds&amp;username=admin&amp;password=password", "family-login-v6": "https://[::1]:2159", "deadlock-debugger-password": "password", "family-login": "https://10.0.30.235:2159", "inituser-login": "zope", "inituser-password": "password", "family-activities": "https://10.0.30.235:2155", "monitor-base-url": "", "site-id": "erp5", "mariadb-test-database-list": ["mysql://testuser_0:testpassword0@10.0.30.235:2099/erp5_test_0", "mysql://testuser_1:testpassword1@10.0.30.235:2099/erp5_test_1", "mysql://testuser_2:testpassword2@10.0.30.235:2099/erp5_test_2", "mysql://testuser_3:testpassword3@10.0.30.235:2099/erp5_test_3", "mysql://testuser_4:testpassword4@10.0.30.235:2099/erp5_test_4", "mysql://testuser_5:testpassword5@10.0.30.235:2099/erp5_test_5", "mysql://testuser_6:testpassword6@10.0.30.235:2099/erp5_test_6", "mysql://testuser_7:testpassword7@10.0.30.235:2099/erp5_test_7", "mysql://testuser_8:testpassword8@10.0.30.235:2099/erp5_test_8", "mysql://testuser_9:testpassword9@10.0.30.235:2099/erp5_test_9", "mysql://testuser_10:testpassword10@10.0.30.235:2099/erp5_test_10", "mysql://testuser_11:testpassword11@10.0.30.235:2099/erp5_test_11"], "mariadb-database-list": ["mysql://user:insecure@10.0.30.235:2099/erp5"], "memcached-volatile-url": "memcached://10.0.30.235:2013/", "memcached-persistent-url": "memcached://10.0.30.235:2003/", "caucase-http-url": "http://[::1]:8890", "activities-test-runner-url-list": ["https://10.0.30.235:2153/unit_test_0/", "https://10.0.30.235:2153/unit_test_1/", "https://10.0.30.235:2153/unit_test_2/"], "family-activities-v6": "https://[::1]:2155"}</parameter>
</instance>
',NULL,NULL,'slaprunner','slappart0',NULL);
INSERT INTO "instance18" VALUES('slaprunner-slappart1','caucase',0,'slaprunner-slappart0','slaprunner-slappart0','/srv/slapgrid/slappart8/srv/runner/project/slapos/software/erp5/software.cfg','caucase','started','<?xml version=''1.0'' encoding=''utf-8''?>
<instance>
  <parameter id="_">{"use-ipv6": false, "auto-sign-csr-amount": 2, "server-port": 8890, "name": "caucase", "server-https-port": 8891}</parameter>
</instance>
','<?xml version=''1.0'' encoding=''utf-8''?>
<instance>
  <parameter id="_">{"http-url": "http://[::1]:8890", "https-url": "https://[::1]:8891", "init-user": "admin"}</parameter>
</instance>
',NULL,NULL,'slaprunner','slappart1',NULL);
INSERT INTO "instance18" VALUES('slaprunner-slappart2','memcached-persistent',0,'slaprunner-slappart0','slaprunner-slappart0','/srv/slapgrid/slappart8/srv/runner/project/slapos/software/erp5/software.cfg','kumofs','started','<?xml version=''1.0'' encoding=''utf-8''?>
<instance>
  <parameter id="_">{"use-ipv6": false, "monitor-passwd": "password", "tcpv4-port": 2000, "name": "memcached-persistent"}</parameter>
</instance>
','<?xml version=''1.0'' encoding=''utf-8''?>
<instance>
  <parameter id="_">{"url": "memcached://10.0.30.235:2003/", "monitor-base-url": ""}</parameter>
</instance>
',NULL,NULL,'slaprunner','slappart2',NULL);
INSERT INTO "instance18" VALUES('slaprunner-slappart3','memcached-volatile',0,'slaprunner-slappart0','slaprunner-slappart0','/srv/slapgrid/slappart8/srv/runner/project/slapos/software/erp5/software.cfg','kumofs','started','<?xml version=''1.0'' encoding=''utf-8''?>
<instance>
  <parameter id="_">{"use-ipv6": false, "monitor-passwd": "password", "tcpv4-port": 2010, "name": "memcached-volatile", "ram-storage-size": 64}</parameter>
</instance>
','<?xml version=''1.0'' encoding=''utf-8''?>
<instance>
  <parameter id="_">{"url": "memcached://10.0.30.235:2013/", "monitor-base-url": ""}</parameter>
</instance>
',NULL,NULL,'slaprunner','slappart3',NULL);
INSERT INTO "instance18" VALUES('slaprunner-slappart4','mariadb',0,'slaprunner-slappart0','slaprunner-slappart0','/srv/slapgrid/slappart8/srv/runner/project/slapos/software/erp5/software.cfg','mariadb','started','<?xml version=''1.0'' encoding=''utf-8''?>
<instance>
  <parameter id="_">{"monitor-passwd": "password", "name": "mariadb", "use-ipv6": false, "tcpv4-port": 2099, "test-database-amount": 12, "innodb-log-file-size": 134217728, "slowest-query-threshold": "", "innodb-buffer-pool-size": 1073741824, "max-slowqueries-threshold": 1000}</parameter>
</instance>
','<?xml version=''1.0'' encoding=''utf-8''?>
<instance>
  <parameter id="_">{"monitor-base-url": "", "server-id": 3739295806, "database-list": ["mysql://user:insecure@10.0.30.235:2099/erp5"], "test-database-list": ["mysql://testuser_0:testpassword0@10.0.30.235:2099/erp5_test_0", "mysql://testuser_1:testpassword1@10.0.30.235:2099/erp5_test_1", "mysql://testuser_2:testpassword2@10.0.30.235:2099/erp5_test_2", "mysql://testuser_3:testpassword3@10.0.30.235:2099/erp5_test_3", "mysql://testuser_4:testpassword4@10.0.30.235:2099/erp5_test_4", "mysql://testuser_5:testpassword5@10.0.30.235:2099/erp5_test_5", "mysql://testuser_6:testpassword6@10.0.30.235:2099/erp5_test_6", "mysql://testuser_7:testpassword7@10.0.30.235:2099/erp5_test_7", "mysql://testuser_8:testpassword8@10.0.30.235:2099/erp5_test_8", "mysql://testuser_9:testpassword9@10.0.30.235:2099/erp5_test_9", "mysql://testuser_10:testpassword10@10.0.30.235:2099/erp5_test_10", "mysql://testuser_11:testpassword11@10.0.30.235:2099/erp5_test_11"]}</parameter>
</instance>
',NULL,NULL,'slaprunner','slappart4',NULL);
INSERT INTO "instance18" VALUES('slaprunner-slappart5','zodb',0,'slaprunner-slappart0','slaprunner-slappart0','/srv/slapgrid/slappart8/srv/runner/project/slapos/software/erp5/software.cfg','zodb-zeo','started','<?xml version=''1.0'' encoding=''utf-8''?>
<instance>
  <parameter id="_">{"use-ipv6": false, "monitor-passwd": "password", "tcpv4-port": 2100, "name": "zodb", "zodb-dict": {"root": {"family": "1"}}}</parameter>
</instance>
','<?xml version=''1.0'' encoding=''utf-8''?>
<instance>
  <parameter id="_">{"storage-dict": {"root": {"storage": "root", "server": "10.0.30.235:2100"}}, "tidstorage-ip": "", "monitor-base-url": "", "tidstorage-port": ""}</parameter>
</instance>
',NULL,NULL,'slaprunner','slappart5',NULL);
INSERT INTO "instance18" VALUES('slaprunner-slappart6','zope-activities',0,'slaprunner-slappart0','slaprunner-slappart0','/srv/slapgrid/slappart8/srv/runner/project/slapos/software/erp5/software.cfg','zope','started','<?xml version=''1.0'' encoding=''utf-8''?>
<instance>
  <parameter id="_">{"zodb-dict": {"root": {"storage-dict": {"cache-size": "20MB"}, "mount-point": "/", "type": "zeo", "cache-size": 50000}}, "site-id": "erp5", "webdav": false, "saucelabs-dict": {}, "tidstorage-port": "", "hosts-dict": {}, "hostalias-dict": {}, "large-file-threshold": "10MB", "bt5-repository-url": "/srv/slapgrid/slappart8/srv/runner/software/287375f0cba269902ba1bc50242839d7/parts/erp5/bt5 /srv/slapgrid/slappart8/srv/runner/software/287375f0cba269902ba1bc50242839d7/parts/erp5/product/ERP5/bootstrap", "test-runner-apache-url-list": ["https://10.0.30.235:2153/unit_test_0/", "https://10.0.30.235:2153/unit_test_1/", "https://10.0.30.235:2153/unit_test_2/"], "timezone": "Asia/Tokyo", "cloudooo-url": "https://cloudooo.erp5.net/", "mysql-test-url-list": ["mysql://testuser_0:testpassword0@10.0.30.235:2099/erp5_test_0", "mysql://testuser_1:testpassword1@10.0.30.235:2099/erp5_test_1", "mysql://testuser_2:testpassword2@10.0.30.235:2099/erp5_test_2", "mysql://testuser_3:testpassword3@10.0.30.235:2099/erp5_test_3", "mysql://testuser_4:testpassword4@10.0.30.235:2099/erp5_test_4", "mysql://testuser_5:testpassword5@10.0.30.235:2099/erp5_test_5", "mysql://testuser_6:testpassword6@10.0.30.235:2099/erp5_test_6", "mysql://testuser_7:testpassword7@10.0.30.235:2099/erp5_test_7", "mysql://testuser_8:testpassword8@10.0.30.235:2099/erp5_test_8", "mysql://testuser_9:testpassword9@10.0.30.235:2099/erp5_test_9", "mysql://testuser_10:testpassword10@10.0.30.235:2099/erp5_test_10", "mysql://testuser_11:testpassword11@10.0.30.235:2099/erp5_test_11"], "inituser-password": "password", "deadlock-debugger-password": "password", "port-base": 2200, "longrequest-logger-interval": -1, "memcached-url": "memcached://10.0.30.235:2013/", "smtp-url": "smtp://127.0.0.2:0/", "test-runner-enabled": true, "kumofs-url": "memcached://10.0.30.235:2003/", "inituser-login": "zope", "thread-amount": 2, "zodb-zeo": {"root": {"storage": "root", "server": "10.0.30.235:2100"}}, "id-store-interval": null, "caucase-url": "http://[::1]:8890", "test-runner-node-count": 3, "cloudooo-retry-count": "2", "mysql-url-list": ["mysql://user:insecure@10.0.30.235:2099/erp5"], "wendelin-core-zblk-fmt": "", "timerserver-interval": 1, "monitor-passwd": "password", "name": "activities", "tidstorage-ip": "", "bt5": "erp5_full_text_myisam_catalog erp5_configurator_standard erp5_configurator_maxma_demo erp5_configurator_run_my_doc", "private-dev-shm": "", "developer-list": ["zope"], "use-ipv6": false, "instance-count": 4, "longrequest-logger-timeout": 1}</parameter>
</instance>
','<?xml version=''1.0'' encoding=''utf-8''?>
<instance>
  <parameter id="_">{"hosts-dict": {"erp5-cloudooo": "cloudooo.erp5.net", "erp5-smtp": "127.0.0.2", "erp5-catalog-0": "10.0.30.235", "erp5-memcached-volatile": "10.0.30.235", "erp5-memcached-persistent": "10.0.30.235"}, "test-runner-address-list": [["10.0.30.235", 2200], ["10.0.30.235", 2201], ["10.0.30.235", 2202]], "monitor-base-url": "", "zope-address-list": [["10.0.30.235:2203", 2, false], ["10.0.30.235:2204", 2, false], ["10.0.30.235:2205", 2, false], ["10.0.30.235:2206", 2, false]]}</parameter>
</instance>
',NULL,NULL,'slaprunner','slappart6',NULL);
INSERT INTO "instance18" VALUES('slaprunner-slappart7','zope-backend',0,'slaprunner-slappart0','slaprunner-slappart0','/srv/slapgrid/slappart8/srv/runner/project/slapos/software/erp5/software.cfg','zope','started','<?xml version=''1.0'' encoding=''utf-8''?>
<instance>
  <parameter id="_">{"zodb-dict": {"root": {"storage-dict": {"cache-size": "20MB"}, "mount-point": "/", "type": "zeo", "cache-size": 50000}}, "site-id": "erp5", "webdav": false, "saucelabs-dict": {}, "tidstorage-port": "", "hosts-dict": {}, "hostalias-dict": {}, "large-file-threshold": "10MB", "bt5-repository-url": "/srv/slapgrid/slappart8/srv/runner/software/287375f0cba269902ba1bc50242839d7/parts/erp5/bt5 /srv/slapgrid/slappart8/srv/runner/software/287375f0cba269902ba1bc50242839d7/parts/erp5/product/ERP5/bootstrap", "test-runner-apache-url-list": ["https://10.0.30.235:2157/unit_test_0/", "https://10.0.30.235:2157/unit_test_1/", "https://10.0.30.235:2157/unit_test_2/"], "timezone": "Asia/Tokyo", "cloudooo-url": "https://cloudooo.erp5.net/", "mysql-test-url-list": ["mysql://testuser_0:testpassword0@10.0.30.235:2099/erp5_test_0", "mysql://testuser_1:testpassword1@10.0.30.235:2099/erp5_test_1", "mysql://testuser_2:testpassword2@10.0.30.235:2099/erp5_test_2", "mysql://testuser_3:testpassword3@10.0.30.235:2099/erp5_test_3", "mysql://testuser_4:testpassword4@10.0.30.235:2099/erp5_test_4", "mysql://testuser_5:testpassword5@10.0.30.235:2099/erp5_test_5", "mysql://testuser_6:testpassword6@10.0.30.235:2099/erp5_test_6", "mysql://testuser_7:testpassword7@10.0.30.235:2099/erp5_test_7", "mysql://testuser_8:testpassword8@10.0.30.235:2099/erp5_test_8", "mysql://testuser_9:testpassword9@10.0.30.235:2099/erp5_test_9", "mysql://testuser_10:testpassword10@10.0.30.235:2099/erp5_test_10", "mysql://testuser_11:testpassword11@10.0.30.235:2099/erp5_test_11"], "inituser-password": "password", "deadlock-debugger-password": "password", "port-base": 2200, "longrequest-logger-interval": -1, "memcached-url": "memcached://10.0.30.235:2013/", "smtp-url": "smtp://127.0.0.2:0/", "test-runner-enabled": true, "kumofs-url": "memcached://10.0.30.235:2003/", "inituser-login": "zope", "thread-amount": 10, "zodb-zeo": {"root": {"storage": "root", "server": "10.0.30.235:2100"}}, "id-store-interval": null, "caucase-url": "http://[::1]:8890", "test-runner-node-count": 3, "cloudooo-retry-count": "2", "mysql-url-list": ["mysql://user:insecure@10.0.30.235:2099/erp5"], "wendelin-core-zblk-fmt": "", "timerserver-interval": 1, "monitor-passwd": "password", "name": "backend", "tidstorage-ip": "", "bt5": "erp5_full_text_myisam_catalog erp5_configurator_standard erp5_configurator_maxma_demo erp5_configurator_run_my_doc", "private-dev-shm": "", "developer-list": ["zope"], "use-ipv6": false, "instance-count": 2, "longrequest-logger-timeout": 1}</parameter>
</instance>
','<?xml version=''1.0'' encoding=''utf-8''?>
<instance>
  <parameter id="_">{"hosts-dict": {"erp5-cloudooo": "cloudooo.erp5.net", "erp5-smtp": "127.0.0.2", "erp5-catalog-0": "10.0.30.235", "erp5-memcached-volatile": "10.0.30.235", "erp5-memcached-persistent": "10.0.30.235"}, "test-runner-address-list": [["10.0.30.235", 2200], ["10.0.30.235", 2201], ["10.0.30.235", 2202]], "monitor-base-url": "", "zope-address-list": [["10.0.30.235:2203", 10, false], ["10.0.30.235:2204", 10, false]]}</parameter>
</instance>
',NULL,NULL,'slaprunner','slappart7',NULL);
INSERT INTO "instance18" VALUES('slaprunner-slappart8','balancer',0,'slaprunner-slappart0','slaprunner-slappart0','/srv/slapgrid/slappart8/srv/runner/project/slapos/software/erp5/software.cfg','balancer','started','<?xml version=''1.0'' encoding=''utf-8''?>
<instance>
  <parameter id="_">{"haproxy-server-check-path": "/", "apachedex-configuration": "--erp5-base +erp5 .*/VirtualHostRoot/erp5(/|\\?|$) --base +other / --skip-user-agent Zabbix --error-detail --js-embed --quiet", "backend-path-dict": {"activities": "/", "login": "/"}, "name": "balancer", "zope-family-entry-request-zope-activities-test-runner-address-list": [["10.0.30.235", 2200], ["10.0.30.235", 2201], ["10.0.30.235", 2202]], "crl-update-periodicity": "daily", "ssl-authentication-dict": {"activities": false, "login": false}, "zope-family-entry-request-zope-activities": [["10.0.30.235:2203", 2, false], ["10.0.30.235:2204", 2, false], ["10.0.30.235:2205", 2, false], ["10.0.30.235:2206", 2, false]], "zope-family-entry-request-zope-backend": [["10.0.30.235:2203", 10, false], ["10.0.30.235:2204", 10, false]], "zope-family-dict": {"activities": ["zope-family-entry-request-zope-activities"], "login": ["zope-family-entry-request-zope-backend"]}, "zope-family-entry-request-zope-backend-test-runner-address-list": [["10.0.30.235", 2200], ["10.0.30.235", 2201], ["10.0.30.235", 2202]], "ssl": {}, "caucase-url": "http://[::1]:8890", "monitor-passwd": "password", "use-ipv6": false, "apachedex-promise-threshold": 70, "tcpv4-port": 2150}</parameter>
</instance>
','<?xml version=''1.0'' encoding=''utf-8''?>
<instance>
  <parameter id="_">{"activities": "https://10.0.30.235:2155", "login-test-runner-url-list": ["https://10.0.30.235:2157/unit_test_0/", "https://10.0.30.235:2157/unit_test_1/", "https://10.0.30.235:2157/unit_test_2/"], "monitor-base-url": "", "login-v6": "https://[::1]:2159", "activities-v6": "https://[::1]:2155", "login": "https://10.0.30.235:2159", "activities-test-runner-url-list": ["https://10.0.30.235:2153/unit_test_0/", "https://10.0.30.235:2153/unit_test_1/", "https://10.0.30.235:2153/unit_test_2/"]}</parameter>
</instance>
',NULL,NULL,'slaprunner','slappart8',NULL);
INSERT INTO "instance18" VALUES('slaprunner-slappart9','seleniumrunner',0,'','','/srv/slapgrid/slappart8/srv/runner/project/slapos/software/seleniumrunner/software.cfg','RootSoftwareInstance','started','<?xml version=''1.0'' encoding=''utf-8''?>
<instance/>
','<?xml version=''1.0'' encoding=''utf-8''?>
<instance>
  <parameter id="url">http://10.0.30.235:4444/wd/hub</parameter>
  <parameter id="display">:123</parameter>
</instance>
',NULL,NULL,'slaprunner','slappart9',NULL);
INSERT INTO "instance18" VALUES('slaprunner-slappart10','evil-instance-with-_-not-json',0,'','','/srv/slapgrid/slappart8/srv/runner/project/slapos/software/evil/software.cfg','RootSoftwareInstance','started','<?xml version=''1.0'' encoding=''utf-8''?>
<instance/>','<?xml version=''1.0'' encoding=''utf-8''?>
<instance>
  <parameter id="_">Ahah this is not json 😜 </parameter>
</instance>
',NULL,NULL,'slaprunner','slappart10',NULL);
CREATE TABLE partition18 (
  reference VARCHAR(255),
  computer_reference VARCHAR(255) DEFAULT 'slaprunner',
  slap_state VARCHAR(255) DEFAULT 'free',
  PRIMARY KEY (reference, computer_reference)
);
INSERT INTO "partition18" VALUES('slappart0','slaprunner','busy');
INSERT INTO "partition18" VALUES('slappart1','slaprunner','busy');
INSERT INTO "partition18" VALUES('slappart2','slaprunner','busy');
INSERT INTO "partition18" VALUES('slappart3','slaprunner','busy');
INSERT INTO "partition18" VALUES('slappart4','slaprunner','busy');
INSERT INTO "partition18" VALUES('slappart5','slaprunner','busy');
INSERT INTO "partition18" VALUES('slappart6','slaprunner','busy');
INSERT INTO "partition18" VALUES('slappart7','slaprunner','busy');
INSERT INTO "partition18" VALUES('slappart8','slaprunner','busy');
INSERT INTO "partition18" VALUES('slappart9','slaprunner','busy');
INSERT INTO "partition18" VALUES('slappart10','slaprunner','busy');
INSERT INTO "partition18" VALUES('slappart11','slaprunner','free');
INSERT INTO "partition18" VALUES('slappart12','slaprunner','free');
INSERT INTO "partition18" VALUES('slappart13','slaprunner','free');
INSERT INTO "partition18" VALUES('slappart14','slaprunner','free');
INSERT INTO "partition18" VALUES('slappart15','slaprunner','free');
INSERT INTO "partition18" VALUES('slappart16','slaprunner','free');
INSERT INTO "partition18" VALUES('slappart17','slaprunner','free');
INSERT INTO "partition18" VALUES('slappart18','slaprunner','free');
INSERT INTO "partition18" VALUES('slappart19','slaprunner','free');
CREATE TABLE partition_network18 (
  partition_reference VARCHAR(255),
  computer_reference VARCHAR(255) DEFAULT 'slaprunner',
  reference VARCHAR(255),
  address VARCHAR(255),
  netmask VARCHAR(255)
);
INSERT INTO "partition_network18" VALUES('slappart0','slaprunner','slappart0','10.0.30.235','255.255.255.255');
INSERT INTO "partition_network18" VALUES('slappart0','slaprunner','slappart0','::1','ffff:ffff:ffff::');
INSERT INTO "partition_network18" VALUES('slappart1','slaprunner','slappart1','10.0.30.235','255.255.255.255');
INSERT INTO "partition_network18" VALUES('slappart1','slaprunner','slappart1','::1','ffff:ffff:ffff::');
INSERT INTO "partition_network18" VALUES('slappart2','slaprunner','slappart2','10.0.30.235','255.255.255.255');
INSERT INTO "partition_network18" VALUES('slappart2','slaprunner','slappart2','::1','ffff:ffff:ffff::');
INSERT INTO "partition_network18" VALUES('slappart3','slaprunner','slappart3','10.0.30.235','255.255.255.255');
INSERT INTO "partition_network18" VALUES('slappart3','slaprunner','slappart3','::1','ffff:ffff:ffff::');
INSERT INTO "partition_network18" VALUES('slappart4','slaprunner','slappart4','10.0.30.235','255.255.255.255');
INSERT INTO "partition_network18" VALUES('slappart4','slaprunner','slappart4','::1','ffff:ffff:ffff::');
INSERT INTO "partition_network18" VALUES('slappart5','slaprunner','slappart5','10.0.30.235','255.255.255.255');
INSERT INTO "partition_network18" VALUES('slappart5','slaprunner','slappart5','::1','ffff:ffff:ffff::');
INSERT INTO "partition_network18" VALUES('slappart6','slaprunner','slappart6','10.0.30.235','255.255.255.255');
INSERT INTO "partition_network18" VALUES('slappart6','slaprunner','slappart6','::1','ffff:ffff:ffff::');
INSERT INTO "partition_network18" VALUES('slappart7','slaprunner','slappart7','10.0.30.235','255.255.255.255');
INSERT INTO "partition_network18" VALUES('slappart7','slaprunner','slappart7','::1','ffff:ffff:ffff::');
INSERT INTO "partition_network18" VALUES('slappart8','slaprunner','slappart8','10.0.30.235','255.255.255.255');
INSERT INTO "partition_network18" VALUES('slappart8','slaprunner','slappart8','::1','ffff:ffff:ffff::');
INSERT INTO "partition_network18" VALUES('slappart9','slaprunner','slappart9','10.0.30.235','255.255.255.255');
INSERT INTO "partition_network18" VALUES('slappart9','slaprunner','slappart9','::1','ffff:ffff:ffff::');
INSERT INTO "partition_network18" VALUES('slappart10','slaprunner','slappart10','10.0.30.235','255.255.255.255');
INSERT INTO "partition_network18" VALUES('slappart10','slaprunner','slappart10','::1','ffff:ffff:ffff::');
INSERT INTO "partition_network18" VALUES('slappart11','slaprunner','slappart11','10.0.30.235','255.255.255.255');
INSERT INTO "partition_network18" VALUES('slappart11','slaprunner','slappart11','::1','ffff:ffff:ffff::');
INSERT INTO "partition_network18" VALUES('slappart12','slaprunner','slappart12','10.0.30.235','255.255.255.255');
INSERT INTO "partition_network18" VALUES('slappart12','slaprunner','slappart12','::1','ffff:ffff:ffff::');
INSERT INTO "partition_network18" VALUES('slappart13','slaprunner','slappart13','10.0.30.235','255.255.255.255');
INSERT INTO "partition_network18" VALUES('slappart13','slaprunner','slappart13','::1','ffff:ffff:ffff::');
INSERT INTO "partition_network18" VALUES('slappart14','slaprunner','slappart14','10.0.30.235','255.255.255.255');
INSERT INTO "partition_network18" VALUES('slappart14','slaprunner','slappart14','::1','ffff:ffff:ffff::');
INSERT INTO "partition_network18" VALUES('slappart15','slaprunner','slappart15','10.0.30.235','255.255.255.255');
INSERT INTO "partition_network18" VALUES('slappart15','slaprunner','slappart15','::1','ffff:ffff:ffff::');
INSERT INTO "partition_network18" VALUES('slappart16','slaprunner','slappart16','10.0.30.235','255.255.255.255');
INSERT INTO "partition_network18" VALUES('slappart16','slaprunner','slappart16','::1','ffff:ffff:ffff::');
INSERT INTO "partition_network18" VALUES('slappart17','slaprunner','slappart17','10.0.30.235','255.255.255.255');
INSERT INTO "partition_network18" VALUES('slappart17','slaprunner','slappart17','::1','ffff:ffff:ffff::');
INSERT INTO "partition_network18" VALUES('slappart18','slaprunner','slappart18','10.0.30.235','255.255.255.255');
INSERT INTO "partition_network18" VALUES('slappart18','slaprunner','slappart18','::1','ffff:ffff:ffff::');
INSERT INTO "partition_network18" VALUES('slappart19','slaprunner','slappart19','10.0.30.235','255.255.255.255');
INSERT INTO "partition_network18" VALUES('slappart19','slaprunner','slappart19','::1','ffff:ffff:ffff::');
CREATE TABLE software18 (
  url VARCHAR(255),
  computer_reference VARCHAR(255) DEFAULT 'slaprunner',
  requested_state VARCHAR(255) DEFAULT 'available',
  PRIMARY KEY (url, computer_reference)
);
INSERT INTO "software18" VALUES('/srv/slapgrid/slappart8/srv/runner/project/slapos/software/seleniumrunner/software.cfg','slaprunner','available');
INSERT INTO "software18" VALUES('/srv/slapgrid/slappart8/srv/runner/project/slapos/software/evil/software.cfg','slaprunner','available');
INSERT INTO "software18" VALUES('/srv/slapgrid/slappart8/srv/runner/project/slapos/software/erp5/software.cfg','slaprunner','available');
CREATE INDEX instance_tree18
  ON instance18 (root_instance_guid);
CREATE INDEX instance_requested_by18
  ON instance18 (requested_by_instance_guid);
CREATE INDEX instance_request_scope18
  ON instance18 (title, root_instance_guid, shared);
CREATE INDEX instance_allocation18
  ON instance18 (allocated_computer, allocated_partition);
COMMIT;
