PRAGMA foreign_keys=OFF;
BEGIN TRANSACTION;
CREATE TABLE config17 (
  name TEXT PRIMARY KEY,
  value TEXT
) WITHOUT ROWID;
INSERT INTO config17 VALUES('local_software_release_root','/');
CREATE TABLE software17 (
  url VARCHAR(255),
  computer_reference VARCHAR(255) DEFAULT 'computer',
  requested_state VARCHAR(255) DEFAULT 'available',
  CONSTRAINT uniq PRIMARY KEY (url, computer_reference)
);
INSERT INTO software17 VALUES('/srv/slapgrid//srv//runner/project//slapos/software.cfg','computer','available');
CREATE TABLE computer17 (
  reference VARCHAR(255) DEFAULT 'computer',
  address VARCHAR(255),
  netmask VARCHAR(255),
  CONSTRAINT uniq PRIMARY KEY (reference)
);
INSERT INTO computer17 VALUES('computer','127.0.0.1','255.255.255.255');
CREATE TABLE partition17 (
  reference VARCHAR(255),
  computer_reference VARCHAR(255) DEFAULT 'computer',
  slap_state VARCHAR(255) DEFAULT 'free',
  software_release VARCHAR(255),
  xml TEXT,
  connection_xml TEXT,
  slave_instance_list TEXT,
  software_type VARCHAR(255),
  partition_reference VARCHAR(255), -- name of the instance
  requested_by VARCHAR(255) NOT NULL DEFAULT '',
  requested_state VARCHAR(255) NOT NULL DEFAULT 'started',
  timestamp REAL,
  CONSTRAINT uniq PRIMARY KEY (reference, computer_reference)
);
INSERT INTO partition17 VALUES('slappart0','computer','busy','/srv/slapgrid//srv//runner/project//slapos/software.cfg',replace('<?xml version=''1.0'' encoding=''utf-8''?>\n<instance>\n  <parameter id="json">{\n  "site-id": "erp5"\n  }\n}</parameter>\n</instance>\n','\n',char(10)),NULL,NULL,'production','slapos','','started',NULL);
INSERT INTO partition17 VALUES('slappart1','computer','busy','/srv/slapgrid//srv//runner/project//slapos/software.cfg',replace('<?xml version=''1.0'' encoding=''utf-8''?>\n<instance/>\n','\n',char(10)),replace('<?xml version=''1.0'' encoding=''utf-8''?>\n<instance>\n  <parameter id="url">mysql://127.0.0.1:45678/erp5</parameter>\n</instance>\n','\n',char(10)),'<marshal><list id="i2"><dictionary id="i3"><string>domain</string><string>shared.example.com</string><string>shared-enable</string><bool>1</bool><string>shared-port</string><int>4443</int><string>slap_software_type</string><string>frontend</string><string>slave_reference</string><string>slapos_shared-frontend</string><string>slave_title</string><string>slapos_shared-frontend</string></dictionary></list></marshal>','mariadb','MariaDB DataBase','slapos','started',1234567890.0);
INSERT INTO partition17 VALUES('slappart2','computer','busy','/srv/slapgrid//srv//runner/project//slapos/software.cfg',replace('<?xml version=''1.0'' encoding=''utf-8''?>\n<instance>\n  <parameter id="cloudooo-json"></parameter>\n</instance>\n','\n',char(10)),replace('<?xml version=''1.0'' encoding=''utf-8''?>\n<instance>\n  <parameter id="url">cloudooo://127.0.0.1:23000/</parameter>\n</instance>\n','\n',char(10)),NULL,'cloudooo','Cloudooo','slapos','started',NULL);
INSERT INTO partition17 VALUES('slappart3','computer','busy','/srv/slapgrid//srv//runner/project//slapos/software.cfg',replace('<?xml version=''1.0'' encoding=''utf-8''?>\n<instance/>\n','\n',char(10)),replace('<?xml version=''1.0'' encoding=''utf-8''?>\n<instance>\n  <parameter id="url">memcached://127.0.0.1:11000/</parameter>\n</instance>\n','\n',char(10)),NULL,'memcached','Memcached','slapos','started',NULL);
INSERT INTO partition17 VALUES('slappart4','computer','busy','/srv/slapgrid//srv//runner/project//slapos/software.cfg',replace('<?xml version=''1.0'' encoding=''utf-8''?>\n<instance/>\n','\n',char(10)),replace('<?xml version=''1.0'' encoding=''utf-8''?>\n<instance>\n  <parameter id="url">memcached://127.0.0.1:13301/</parameter>\n</instance>\n','\n',char(10)),NULL,'kumofs','KumoFS','slapos','started',NULL);
INSERT INTO partition17 VALUES('slappart5','computer','busy','/srv/slapgrid//srv//runner/project//slapos/software.cfg',replace('<?xml version=''1.0'' encoding=''utf-8''?>\n<instance>\n  <parameter id="kumofs-url">memcached://127.0.0.1:13301/</parameter>\n  <parameter id="memcached-url">memcached://127.0.0.1:11000/</parameter>\n  <parameter id="cloudooo-url">cloudooo://127.0.0.1:23000/</parameter>\n</instance>\n','\n',char(10)),replace('<?xml version=''1.0'' encoding=''utf-8''?>\n<instance>\n  <parameter id="url">https://[fc00::1]:10001</parameter>\n</instance>\n','\n',char(10)),NULL,'tidstorage','TidStorage','slapos','started',NULL);
INSERT INTO partition17 VALUES('slappart6','computer','free',NULL,NULL,NULL,NULL,NULL,NULL,'','started',NULL);
INSERT INTO partition17 VALUES('slappart7','computer','free',NULL,NULL,NULL,NULL,NULL,NULL,'','started',NULL);
INSERT INTO partition17 VALUES('slappart8','computer','free',NULL,NULL,NULL,NULL,NULL,NULL,'','started',NULL);
INSERT INTO partition17 VALUES('slappart9','computer','free',NULL,NULL,NULL,NULL,NULL,NULL,'','started',NULL);
CREATE TABLE slave17 (
  reference VARCHAR(255), -- unique slave reference
  computer_reference VARCHAR(255) DEFAULT 'computer',
  connection_xml TEXT,
  hosted_by VARCHAR(255),
  asked_by VARCHAR(255) -- only used for debugging,
                        -- slapproxy does not support proper scope
);
INSERT INTO slave17 VALUES('slapos_shared-frontend','computer',replace('<?xml version=''1.0'' encoding=''utf-8''?>\n<instance>\n  <parameter id="url">https://[fc00::1]:4443/</parameter>\n</instance>\n','\n',char(10)),'slappart1','slapos');
CREATE TABLE partition_network17 (
  partition_reference VARCHAR(255),
  computer_reference VARCHAR(255) DEFAULT 'computer',
  reference VARCHAR(255),
  address VARCHAR(255),
  netmask VARCHAR(255)
);
INSERT INTO partition_network17 VALUES('slappart0','computer','slappart0','127.0.0.1','255.255.255.255');
INSERT INTO partition_network17 VALUES('slappart0','computer','slappart0','fc00::1','ffff:ffff:ffff::');
INSERT INTO partition_network17 VALUES('slappart1','computer','slappart1','127.0.0.1','255.255.255.255');
INSERT INTO partition_network17 VALUES('slappart1','computer','slappart1','fc00::1','ffff:ffff:ffff::');
INSERT INTO partition_network17 VALUES('slappart2','computer','slappart2','127.0.0.1','255.255.255.255');
INSERT INTO partition_network17 VALUES('slappart2','computer','slappart2','fc00::1','ffff:ffff:ffff::');
INSERT INTO partition_network17 VALUES('slappart3','computer','slappart3','127.0.0.1','255.255.255.255');
INSERT INTO partition_network17 VALUES('slappart3','computer','slappart3','fc00::1','ffff:ffff:ffff::');
INSERT INTO partition_network17 VALUES('slappart4','computer','slappart4','127.0.0.1','255.255.255.255');
INSERT INTO partition_network17 VALUES('slappart4','computer','slappart4','fc00::1','ffff:ffff:ffff::');
INSERT INTO partition_network17 VALUES('slappart5','computer','slappart5','127.0.0.1','255.255.255.255');
INSERT INTO partition_network17 VALUES('slappart5','computer','slappart5','fc00::1','ffff:ffff:ffff::');
INSERT INTO partition_network17 VALUES('slappart6','computer','slappart6','127.0.0.1','255.255.255.255');
INSERT INTO partition_network17 VALUES('slappart6','computer','slappart6','fc00::1','ffff:ffff:ffff::');
INSERT INTO partition_network17 VALUES('slappart7','computer','slappart7','127.0.0.1','255.255.255.255');
INSERT INTO partition_network17 VALUES('slappart7','computer','slappart7','fc00::1','ffff:ffff:ffff::');
INSERT INTO partition_network17 VALUES('slappart8','computer','slappart8','127.0.0.1','255.255.255.255');
INSERT INTO partition_network17 VALUES('slappart8','computer','slappart8','fc00::1','ffff:ffff:ffff::');
INSERT INTO partition_network17 VALUES('slappart9','computer','slappart9','127.0.0.1','255.255.255.255');
INSERT INTO partition_network17 VALUES('slappart9','computer','slappart9','fc00::1','ffff:ffff:ffff::');
CREATE TABLE forwarded_partition_request17 (
  partition_reference VARCHAR(255), -- a.k.a source_instance_id
  master_url VARCHAR(255),
  CONSTRAINT uniq PRIMARY KEY (partition_reference, master_url)
);
INSERT INTO forwarded_partition_request17 VALUES('forwarded_instance','https://bogus/master/url');
COMMIT;
