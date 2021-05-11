PRAGMA foreign_keys=OFF;
BEGIN TRANSACTION;
CREATE TABLE software14 (
  url VARCHAR(255),
  computer_reference VARCHAR(255) DEFAULT 'slaprunner',
  requested_state VARCHAR(255) DEFAULT 'available',
  CONSTRAINT uniq PRIMARY KEY (url, computer_reference)
);
INSERT INTO "software14" VALUES('/srv/slapgrid/slappart8/srv/runner/project/slapos/software/seleniumrunner/software.cfg','slaprunner','available');
INSERT INTO "software14" VALUES('/srv/slapgrid/slappart8/srv/runner/project/slapos/software/evil/software.cfg','slaprunner','available');
INSERT INTO "software14" VALUES('/srv/slapgrid/slappart8/srv/runner/project/slapos/software/erp5/software.cfg','slaprunner','available');
CREATE TABLE computer14 (
  reference VARCHAR(255) DEFAULT 'slaprunner',
  address VARCHAR(255),
  netmask VARCHAR(255),
  CONSTRAINT uniq PRIMARY KEY (reference)
);
INSERT INTO "computer14" VALUES('slaprunner','10.0.30.235','255.255.255.255');
CREATE TABLE partition14 (
  reference VARCHAR(255),
  computer_reference VARCHAR(255) DEFAULT 'slaprunner',
  slap_state VARCHAR(255) DEFAULT 'free',
  software_release VARCHAR(255),
  xml TEXT,
  connection_xml TEXT,
  slave_instance_list TEXT,
  software_type VARCHAR(255),
  partition_reference VARCHAR(255), -- name of the instance
  requested_by VARCHAR(255),
  requested_state VARCHAR(255) NOT NULL DEFAULT 'started',
  timestamp REAL,
  CONSTRAINT uniq PRIMARY KEY (reference, computer_reference)
);
INSERT INTO "partition14" VALUES('slappart0','slaprunner','busy','/srv/slapgrid/slappart8/srv/runner/project/slapos/software/erp5/software.cfg','<?xml version=''1.0'' encoding=''utf-8''?>
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
',NULL,'default','slaprunner-dev-local-frontend-2',NULL,'started',NULL);
INSERT INTO "partition14" VALUES('slappart1','slaprunner','busy','/srv/slapgrid/slappart8/srv/runner/project/slapos/software/erp5/software.cfg','<?xml version=''1.0'' encoding=''utf-8''?>
<instance>
  <parameter id="_">{"use-ipv6": false, "auto-sign-csr-amount": 2, "server-port": 8890, "name": "caucase", "server-https-port": 8891}</parameter>
</instance>
','<?xml version=''1.0'' encoding=''utf-8''?>
<instance>
  <parameter id="_">{"http-url": "http://[::1]:8890", "https-url": "https://[::1]:8891", "init-user": "admin"}</parameter>
</instance>
',NULL,'caucase','caucase','slappart0','started',NULL);
INSERT INTO "partition14" VALUES('slappart2','slaprunner','busy','/srv/slapgrid/slappart8/srv/runner/project/slapos/software/erp5/software.cfg','<?xml version=''1.0'' encoding=''utf-8''?>
<instance>
  <parameter id="_">{"use-ipv6": false, "monitor-passwd": "password", "tcpv4-port": 2000, "name": "memcached-persistent"}</parameter>
</instance>
','<?xml version=''1.0'' encoding=''utf-8''?>
<instance>
  <parameter id="_">{"url": "memcached://10.0.30.235:2003/", "monitor-base-url": ""}</parameter>
</instance>
',NULL,'kumofs','memcached-persistent','slappart0','started',NULL);
INSERT INTO "partition14" VALUES('slappart3','slaprunner','busy','/srv/slapgrid/slappart8/srv/runner/project/slapos/software/erp5/software.cfg','<?xml version=''1.0'' encoding=''utf-8''?>
<instance>
  <parameter id="_">{"use-ipv6": false, "monitor-passwd": "password", "tcpv4-port": 2010, "name": "memcached-volatile", "ram-storage-size": 64}</parameter>
</instance>
','<?xml version=''1.0'' encoding=''utf-8''?>
<instance>
  <parameter id="_">{"url": "memcached://10.0.30.235:2013/", "monitor-base-url": ""}</parameter>
</instance>
',NULL,'kumofs','memcached-volatile','slappart0','started',NULL);
INSERT INTO "partition14" VALUES('slappart4','slaprunner','busy','/srv/slapgrid/slappart8/srv/runner/project/slapos/software/erp5/software.cfg','<?xml version=''1.0'' encoding=''utf-8''?>
<instance>
  <parameter id="_">{"monitor-passwd": "password", "name": "mariadb", "use-ipv6": false, "tcpv4-port": 2099, "test-database-amount": 12, "innodb-log-file-size": 134217728, "slowest-query-threshold": "", "innodb-buffer-pool-size": 1073741824, "max-slowqueries-threshold": 1000}</parameter>
</instance>
','<?xml version=''1.0'' encoding=''utf-8''?>
<instance>
  <parameter id="_">{"monitor-base-url": "", "server-id": 3739295806, "database-list": ["mysql://user:insecure@10.0.30.235:2099/erp5"], "test-database-list": ["mysql://testuser_0:testpassword0@10.0.30.235:2099/erp5_test_0", "mysql://testuser_1:testpassword1@10.0.30.235:2099/erp5_test_1", "mysql://testuser_2:testpassword2@10.0.30.235:2099/erp5_test_2", "mysql://testuser_3:testpassword3@10.0.30.235:2099/erp5_test_3", "mysql://testuser_4:testpassword4@10.0.30.235:2099/erp5_test_4", "mysql://testuser_5:testpassword5@10.0.30.235:2099/erp5_test_5", "mysql://testuser_6:testpassword6@10.0.30.235:2099/erp5_test_6", "mysql://testuser_7:testpassword7@10.0.30.235:2099/erp5_test_7", "mysql://testuser_8:testpassword8@10.0.30.235:2099/erp5_test_8", "mysql://testuser_9:testpassword9@10.0.30.235:2099/erp5_test_9", "mysql://testuser_10:testpassword10@10.0.30.235:2099/erp5_test_10", "mysql://testuser_11:testpassword11@10.0.30.235:2099/erp5_test_11"]}</parameter>
</instance>
',NULL,'mariadb','mariadb','slappart0','started',NULL);
INSERT INTO "partition14" VALUES('slappart5','slaprunner','busy','/srv/slapgrid/slappart8/srv/runner/project/slapos/software/erp5/software.cfg','<?xml version=''1.0'' encoding=''utf-8''?>
<instance>
  <parameter id="_">{"use-ipv6": false, "monitor-passwd": "password", "tcpv4-port": 2100, "name": "zodb", "zodb-dict": {"root": {"family": "1"}}}</parameter>
</instance>
','<?xml version=''1.0'' encoding=''utf-8''?>
<instance>
  <parameter id="_">{"storage-dict": {"root": {"storage": "root", "server": "10.0.30.235:2100"}}, "tidstorage-ip": "", "monitor-base-url": "", "tidstorage-port": ""}</parameter>
</instance>
',NULL,'zodb-zeo','zodb','slappart0','started',NULL);
INSERT INTO "partition14" VALUES('slappart6','slaprunner','busy','/srv/slapgrid/slappart8/srv/runner/project/slapos/software/erp5/software.cfg','<?xml version=''1.0'' encoding=''utf-8''?>
<instance>
  <parameter id="_">{"zodb-dict": {"root": {"storage-dict": {"cache-size": "20MB"}, "mount-point": "/", "type": "zeo", "cache-size": 50000}}, "site-id": "erp5", "webdav": false, "saucelabs-dict": {}, "tidstorage-port": "", "hosts-dict": {}, "hostalias-dict": {}, "large-file-threshold": "10MB", "bt5-repository-url": "/srv/slapgrid/slappart8/srv/runner/software/287375f0cba269902ba1bc50242839d7/parts/erp5/bt5 /srv/slapgrid/slappart8/srv/runner/software/287375f0cba269902ba1bc50242839d7/parts/erp5/product/ERP5/bootstrap", "test-runner-apache-url-list": ["https://10.0.30.235:2153/unit_test_0/", "https://10.0.30.235:2153/unit_test_1/", "https://10.0.30.235:2153/unit_test_2/"], "timezone": "Asia/Tokyo", "cloudooo-url": "https://cloudooo.erp5.net/", "mysql-test-url-list": ["mysql://testuser_0:testpassword0@10.0.30.235:2099/erp5_test_0", "mysql://testuser_1:testpassword1@10.0.30.235:2099/erp5_test_1", "mysql://testuser_2:testpassword2@10.0.30.235:2099/erp5_test_2", "mysql://testuser_3:testpassword3@10.0.30.235:2099/erp5_test_3", "mysql://testuser_4:testpassword4@10.0.30.235:2099/erp5_test_4", "mysql://testuser_5:testpassword5@10.0.30.235:2099/erp5_test_5", "mysql://testuser_6:testpassword6@10.0.30.235:2099/erp5_test_6", "mysql://testuser_7:testpassword7@10.0.30.235:2099/erp5_test_7", "mysql://testuser_8:testpassword8@10.0.30.235:2099/erp5_test_8", "mysql://testuser_9:testpassword9@10.0.30.235:2099/erp5_test_9", "mysql://testuser_10:testpassword10@10.0.30.235:2099/erp5_test_10", "mysql://testuser_11:testpassword11@10.0.30.235:2099/erp5_test_11"], "inituser-password": "password", "deadlock-debugger-password": "password", "port-base": 2200, "longrequest-logger-interval": -1, "memcached-url": "memcached://10.0.30.235:2013/", "smtp-url": "smtp://127.0.0.2:0/", "test-runner-enabled": true, "kumofs-url": "memcached://10.0.30.235:2003/", "inituser-login": "zope", "thread-amount": 2, "zodb-zeo": {"root": {"storage": "root", "server": "10.0.30.235:2100"}}, "id-store-interval": null, "caucase-url": "http://[::1]:8890", "test-runner-node-count": 3, "cloudooo-retry-count": "2", "mysql-url-list": ["mysql://user:insecure@10.0.30.235:2099/erp5"], "wendelin-core-zblk-fmt": "", "timerserver-interval": 1, "monitor-passwd": "password", "name": "activities", "tidstorage-ip": "", "bt5": "erp5_full_text_myisam_catalog erp5_configurator_standard erp5_configurator_maxma_demo erp5_configurator_run_my_doc", "private-dev-shm": "", "developer-list": ["zope"], "use-ipv6": false, "instance-count": 4, "longrequest-logger-timeout": 1}</parameter>
</instance>
','<?xml version=''1.0'' encoding=''utf-8''?>
<instance>
  <parameter id="_">{"hosts-dict": {"erp5-cloudooo": "cloudooo.erp5.net", "erp5-smtp": "127.0.0.2", "erp5-catalog-0": "10.0.30.235", "erp5-memcached-volatile": "10.0.30.235", "erp5-memcached-persistent": "10.0.30.235"}, "test-runner-address-list": [["10.0.30.235", 2200], ["10.0.30.235", 2201], ["10.0.30.235", 2202]], "monitor-base-url": "", "zope-address-list": [["10.0.30.235:2203", 2, false], ["10.0.30.235:2204", 2, false], ["10.0.30.235:2205", 2, false], ["10.0.30.235:2206", 2, false]]}</parameter>
</instance>
',NULL,'zope','zope-activities','slappart0','started',NULL);
INSERT INTO "partition14" VALUES('slappart7','slaprunner','busy','/srv/slapgrid/slappart8/srv/runner/project/slapos/software/erp5/software.cfg','<?xml version=''1.0'' encoding=''utf-8''?>
<instance>
  <parameter id="_">{"zodb-dict": {"root": {"storage-dict": {"cache-size": "20MB"}, "mount-point": "/", "type": "zeo", "cache-size": 50000}}, "site-id": "erp5", "webdav": false, "saucelabs-dict": {}, "tidstorage-port": "", "hosts-dict": {}, "hostalias-dict": {}, "large-file-threshold": "10MB", "bt5-repository-url": "/srv/slapgrid/slappart8/srv/runner/software/287375f0cba269902ba1bc50242839d7/parts/erp5/bt5 /srv/slapgrid/slappart8/srv/runner/software/287375f0cba269902ba1bc50242839d7/parts/erp5/product/ERP5/bootstrap", "test-runner-apache-url-list": ["https://10.0.30.235:2157/unit_test_0/", "https://10.0.30.235:2157/unit_test_1/", "https://10.0.30.235:2157/unit_test_2/"], "timezone": "Asia/Tokyo", "cloudooo-url": "https://cloudooo.erp5.net/", "mysql-test-url-list": ["mysql://testuser_0:testpassword0@10.0.30.235:2099/erp5_test_0", "mysql://testuser_1:testpassword1@10.0.30.235:2099/erp5_test_1", "mysql://testuser_2:testpassword2@10.0.30.235:2099/erp5_test_2", "mysql://testuser_3:testpassword3@10.0.30.235:2099/erp5_test_3", "mysql://testuser_4:testpassword4@10.0.30.235:2099/erp5_test_4", "mysql://testuser_5:testpassword5@10.0.30.235:2099/erp5_test_5", "mysql://testuser_6:testpassword6@10.0.30.235:2099/erp5_test_6", "mysql://testuser_7:testpassword7@10.0.30.235:2099/erp5_test_7", "mysql://testuser_8:testpassword8@10.0.30.235:2099/erp5_test_8", "mysql://testuser_9:testpassword9@10.0.30.235:2099/erp5_test_9", "mysql://testuser_10:testpassword10@10.0.30.235:2099/erp5_test_10", "mysql://testuser_11:testpassword11@10.0.30.235:2099/erp5_test_11"], "inituser-password": "password", "deadlock-debugger-password": "password", "port-base": 2200, "longrequest-logger-interval": -1, "memcached-url": "memcached://10.0.30.235:2013/", "smtp-url": "smtp://127.0.0.2:0/", "test-runner-enabled": true, "kumofs-url": "memcached://10.0.30.235:2003/", "inituser-login": "zope", "thread-amount": 10, "zodb-zeo": {"root": {"storage": "root", "server": "10.0.30.235:2100"}}, "id-store-interval": null, "caucase-url": "http://[::1]:8890", "test-runner-node-count": 3, "cloudooo-retry-count": "2", "mysql-url-list": ["mysql://user:insecure@10.0.30.235:2099/erp5"], "wendelin-core-zblk-fmt": "", "timerserver-interval": 1, "monitor-passwd": "password", "name": "backend", "tidstorage-ip": "", "bt5": "erp5_full_text_myisam_catalog erp5_configurator_standard erp5_configurator_maxma_demo erp5_configurator_run_my_doc", "private-dev-shm": "", "developer-list": ["zope"], "use-ipv6": false, "instance-count": 2, "longrequest-logger-timeout": 1}</parameter>
</instance>
','<?xml version=''1.0'' encoding=''utf-8''?>
<instance>
  <parameter id="_">{"hosts-dict": {"erp5-cloudooo": "cloudooo.erp5.net", "erp5-smtp": "127.0.0.2", "erp5-catalog-0": "10.0.30.235", "erp5-memcached-volatile": "10.0.30.235", "erp5-memcached-persistent": "10.0.30.235"}, "test-runner-address-list": [["10.0.30.235", 2200], ["10.0.30.235", 2201], ["10.0.30.235", 2202]], "monitor-base-url": "", "zope-address-list": [["10.0.30.235:2203", 10, false], ["10.0.30.235:2204", 10, false]]}</parameter>
</instance>
',NULL,'zope','zope-backend','slappart0','started',NULL);
INSERT INTO "partition14" VALUES('slappart8','slaprunner','busy','/srv/slapgrid/slappart8/srv/runner/project/slapos/software/erp5/software.cfg','<?xml version=''1.0'' encoding=''utf-8''?>
<instance>
  <parameter id="_">{"haproxy-server-check-path": "/", "apachedex-configuration": "--erp5-base +erp5 .*/VirtualHostRoot/erp5(/|\\?|$) --base +other / --skip-user-agent Zabbix --error-detail --js-embed --quiet", "backend-path-dict": {"activities": "/", "login": "/"}, "name": "balancer", "zope-family-entry-request-zope-activities-test-runner-address-list": [["10.0.30.235", 2200], ["10.0.30.235", 2201], ["10.0.30.235", 2202]], "crl-update-periodicity": "daily", "ssl-authentication-dict": {"activities": false, "login": false}, "zope-family-entry-request-zope-activities": [["10.0.30.235:2203", 2, false], ["10.0.30.235:2204", 2, false], ["10.0.30.235:2205", 2, false], ["10.0.30.235:2206", 2, false]], "zope-family-entry-request-zope-backend": [["10.0.30.235:2203", 10, false], ["10.0.30.235:2204", 10, false]], "zope-family-dict": {"activities": ["zope-family-entry-request-zope-activities"], "login": ["zope-family-entry-request-zope-backend"]}, "zope-family-entry-request-zope-backend-test-runner-address-list": [["10.0.30.235", 2200], ["10.0.30.235", 2201], ["10.0.30.235", 2202]], "ssl": {}, "caucase-url": "http://[::1]:8890", "monitor-passwd": "password", "use-ipv6": false, "apachedex-promise-threshold": 70, "tcpv4-port": 2150}</parameter>
</instance>
','<?xml version=''1.0'' encoding=''utf-8''?>
<instance>
  <parameter id="_">{"activities": "https://10.0.30.235:2155", "login-test-runner-url-list": ["https://10.0.30.235:2157/unit_test_0/", "https://10.0.30.235:2157/unit_test_1/", "https://10.0.30.235:2157/unit_test_2/"], "monitor-base-url": "", "login-v6": "https://[::1]:2159", "activities-v6": "https://[::1]:2155", "login": "https://10.0.30.235:2159", "activities-test-runner-url-list": ["https://10.0.30.235:2153/unit_test_0/", "https://10.0.30.235:2153/unit_test_1/", "https://10.0.30.235:2153/unit_test_2/"]}</parameter>
</instance>
',NULL,'balancer','balancer','slappart0','started',NULL);
INSERT INTO "partition14" VALUES('slappart9','slaprunner','busy','/srv/slapgrid/slappart8/srv/runner/project/slapos/software/seleniumrunner/software.cfg','<?xml version=''1.0'' encoding=''utf-8''?>
<instance/>
','<?xml version=''1.0'' encoding=''utf-8''?>
<instance>
  <parameter id="url">http://10.0.30.235:4444/wd/hub</parameter>
  <parameter id="display">:123</parameter>
</instance>
',NULL,'RootSoftwareInstance','seleniumrunner',NULL,'started',NULL);
INSERT INTO "partition14" VALUES('slappart10','slaprunner','busy','/srv/slapgrid/slappart8/srv/runner/project/slapos/software/evil/software.cfg','<?xml version=''1.0'' encoding=''utf-8''?>
<instance/>','<?xml version=''1.0'' encoding=''utf-8''?>
<instance>
  <parameter id="_">Ahah this is not json 😜 </parameter>
</instance>
',NULL,'RootSoftwareInstance','evil-instance-with-_-not-json',NULL,'started',NULL);
INSERT INTO "partition14" VALUES('slappart11','slaprunner','free',NULL,NULL,NULL,NULL,NULL,NULL,NULL,'started',NULL);
INSERT INTO "partition14" VALUES('slappart12','slaprunner','free',NULL,NULL,NULL,NULL,NULL,NULL,NULL,'started',NULL);
INSERT INTO "partition14" VALUES('slappart13','slaprunner','free',NULL,NULL,NULL,NULL,NULL,NULL,NULL,'started',NULL);
INSERT INTO "partition14" VALUES('slappart14','slaprunner','free',NULL,NULL,NULL,NULL,NULL,NULL,NULL,'started',NULL);
INSERT INTO "partition14" VALUES('slappart15','slaprunner','free',NULL,NULL,NULL,NULL,NULL,NULL,NULL,'started',NULL);
INSERT INTO "partition14" VALUES('slappart16','slaprunner','free',NULL,NULL,NULL,NULL,NULL,NULL,NULL,'started',NULL);
INSERT INTO "partition14" VALUES('slappart17','slaprunner','free',NULL,NULL,NULL,NULL,NULL,NULL,NULL,'started',NULL);
INSERT INTO "partition14" VALUES('slappart18','slaprunner','free',NULL,NULL,NULL,NULL,NULL,NULL,NULL,'started',NULL);
INSERT INTO "partition14" VALUES('slappart19','slaprunner','free',NULL,NULL,NULL,NULL,NULL,NULL,NULL,'started',NULL);
CREATE TABLE slave14 (
  reference VARCHAR(255), -- unique slave reference
  computer_reference VARCHAR(255) DEFAULT 'slaprunner',
  connection_xml TEXT,
  hosted_by VARCHAR(255),
  asked_by VARCHAR(255) -- only used for debugging,
                        -- slapproxy does not support proper scope
);
CREATE TABLE partition_network14 (
  partition_reference VARCHAR(255),
  computer_reference VARCHAR(255) DEFAULT 'slaprunner',
  reference VARCHAR(255),
  address VARCHAR(255),
  netmask VARCHAR(255)
);
INSERT INTO "partition_network14" VALUES('slappart0','slaprunner','slappart0','10.0.30.235','255.255.255.255');
INSERT INTO "partition_network14" VALUES('slappart0','slaprunner','slappart0','::1','ffff:ffff:ffff::');
INSERT INTO "partition_network14" VALUES('slappart1','slaprunner','slappart1','10.0.30.235','255.255.255.255');
INSERT INTO "partition_network14" VALUES('slappart1','slaprunner','slappart1','::1','ffff:ffff:ffff::');
INSERT INTO "partition_network14" VALUES('slappart2','slaprunner','slappart2','10.0.30.235','255.255.255.255');
INSERT INTO "partition_network14" VALUES('slappart2','slaprunner','slappart2','::1','ffff:ffff:ffff::');
INSERT INTO "partition_network14" VALUES('slappart3','slaprunner','slappart3','10.0.30.235','255.255.255.255');
INSERT INTO "partition_network14" VALUES('slappart3','slaprunner','slappart3','::1','ffff:ffff:ffff::');
INSERT INTO "partition_network14" VALUES('slappart4','slaprunner','slappart4','10.0.30.235','255.255.255.255');
INSERT INTO "partition_network14" VALUES('slappart4','slaprunner','slappart4','::1','ffff:ffff:ffff::');
INSERT INTO "partition_network14" VALUES('slappart5','slaprunner','slappart5','10.0.30.235','255.255.255.255');
INSERT INTO "partition_network14" VALUES('slappart5','slaprunner','slappart5','::1','ffff:ffff:ffff::');
INSERT INTO "partition_network14" VALUES('slappart6','slaprunner','slappart6','10.0.30.235','255.255.255.255');
INSERT INTO "partition_network14" VALUES('slappart6','slaprunner','slappart6','::1','ffff:ffff:ffff::');
INSERT INTO "partition_network14" VALUES('slappart7','slaprunner','slappart7','10.0.30.235','255.255.255.255');
INSERT INTO "partition_network14" VALUES('slappart7','slaprunner','slappart7','::1','ffff:ffff:ffff::');
INSERT INTO "partition_network14" VALUES('slappart8','slaprunner','slappart8','10.0.30.235','255.255.255.255');
INSERT INTO "partition_network14" VALUES('slappart8','slaprunner','slappart8','::1','ffff:ffff:ffff::');
INSERT INTO "partition_network14" VALUES('slappart9','slaprunner','slappart9','10.0.30.235','255.255.255.255');
INSERT INTO "partition_network14" VALUES('slappart9','slaprunner','slappart9','::1','ffff:ffff:ffff::');
INSERT INTO "partition_network14" VALUES('slappart10','slaprunner','slappart10','10.0.30.235','255.255.255.255');
INSERT INTO "partition_network14" VALUES('slappart10','slaprunner','slappart10','::1','ffff:ffff:ffff::');
INSERT INTO "partition_network14" VALUES('slappart11','slaprunner','slappart11','10.0.30.235','255.255.255.255');
INSERT INTO "partition_network14" VALUES('slappart11','slaprunner','slappart11','::1','ffff:ffff:ffff::');
INSERT INTO "partition_network14" VALUES('slappart12','slaprunner','slappart12','10.0.30.235','255.255.255.255');
INSERT INTO "partition_network14" VALUES('slappart12','slaprunner','slappart12','::1','ffff:ffff:ffff::');
INSERT INTO "partition_network14" VALUES('slappart13','slaprunner','slappart13','10.0.30.235','255.255.255.255');
INSERT INTO "partition_network14" VALUES('slappart13','slaprunner','slappart13','::1','ffff:ffff:ffff::');
INSERT INTO "partition_network14" VALUES('slappart14','slaprunner','slappart14','10.0.30.235','255.255.255.255');
INSERT INTO "partition_network14" VALUES('slappart14','slaprunner','slappart14','::1','ffff:ffff:ffff::');
INSERT INTO "partition_network14" VALUES('slappart15','slaprunner','slappart15','10.0.30.235','255.255.255.255');
INSERT INTO "partition_network14" VALUES('slappart15','slaprunner','slappart15','::1','ffff:ffff:ffff::');
INSERT INTO "partition_network14" VALUES('slappart16','slaprunner','slappart16','10.0.30.235','255.255.255.255');
INSERT INTO "partition_network14" VALUES('slappart16','slaprunner','slappart16','::1','ffff:ffff:ffff::');
INSERT INTO "partition_network14" VALUES('slappart17','slaprunner','slappart17','10.0.30.235','255.255.255.255');
INSERT INTO "partition_network14" VALUES('slappart17','slaprunner','slappart17','::1','ffff:ffff:ffff::');
INSERT INTO "partition_network14" VALUES('slappart18','slaprunner','slappart18','10.0.30.235','255.255.255.255');
INSERT INTO "partition_network14" VALUES('slappart18','slaprunner','slappart18','::1','ffff:ffff:ffff::');
INSERT INTO "partition_network14" VALUES('slappart19','slaprunner','slappart19','10.0.30.235','255.255.255.255');
INSERT INTO "partition_network14" VALUES('slappart19','slaprunner','slappart19','::1','ffff:ffff:ffff::');
CREATE TABLE forwarded_partition_request14 (
  partition_reference VARCHAR(255), -- a.k.a source_instance_id
  master_url VARCHAR(255)
);
COMMIT;
