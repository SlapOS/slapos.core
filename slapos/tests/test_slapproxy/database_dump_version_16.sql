PRAGMA foreign_keys=OFF;
BEGIN TRANSACTION;
CREATE TABLE local_software_release_root16 (
  path VARCHAR(255)
);
INSERT INTO "local_software_release_root16" VALUES('/');
INSERT INTO "local_software_release_root16" VALUES('/');
CREATE TABLE software16 (
  url VARCHAR(255),
  computer_reference VARCHAR(255) DEFAULT 'computer',
  requested_state VARCHAR(255) DEFAULT 'available',
  CONSTRAINT uniq PRIMARY KEY (url, computer_reference)
);
INSERT INTO "software16" VALUES('/srv/slapgrid//srv//runner/project//slapos/software.cfg','computer','available');
CREATE TABLE computer16 (
  reference VARCHAR(255) DEFAULT 'computer',
  address VARCHAR(255),
  netmask VARCHAR(255),
  CONSTRAINT uniq PRIMARY KEY (reference)
);
INSERT INTO "computer16" VALUES('computer','127.0.0.1','255.255.255.255');
CREATE TABLE partition16 (
  reference VARCHAR(255),
  computer_reference VARCHAR(255) DEFAULT 'computer',
  slap_state VARCHAR(255) DEFAULT 'free',
  software_release VARCHAR(255),
  xml TEXT,
  connection_xml TEXT,
  slave_instance_list TEXT,
  software_type VARCHAR(255),
  partition_reference VARCHAR(255), -- name of the instance
  requested_by VARCHAR(255), -- only used for debugging,
                             -- slapproxy does not support proper scope
  requested_state VARCHAR(255) NOT NULL DEFAULT 'started',
  timestamp REAL,
  CONSTRAINT uniq PRIMARY KEY (reference, computer_reference)
);
INSERT INTO "partition16" VALUES('slappart0','computer','busy','/srv/slapgrid//srv//runner/project//slapos/software.cfg','<?xml version=''1.0'' encoding=''utf-8''?>
<instance>
  <parameter id="json">{
  "site-id": "erp5"
  }
}</parameter>
</instance>
',NULL,NULL,'production','slapos',NULL,'started',NULL);
INSERT INTO "partition16" VALUES('slappart1','computer','busy','/srv/slapgrid//srv//runner/project//slapos/software.cfg','<?xml version=''1.0'' encoding=''utf-8''?>
<instance/>
','<?xml version=''1.0'' encoding=''utf-8''?>
<instance>
  <parameter id="url">mysql://127.0.0.1:45678/erp5</parameter>
</instance>
',NULL,'mariadb','MariaDB DataBase','slappart0','started',NULL);
INSERT INTO "partition16" VALUES('slappart2','computer','busy','/srv/slapgrid//srv//runner/project//slapos/software.cfg','<?xml version=''1.0'' encoding=''utf-8''?>
<instance>
  <parameter id="cloudooo-json"></parameter>
</instance>
','<?xml version=''1.0'' encoding=''utf-8''?>
<instance>
  <parameter id="url">cloudooo://127.0.0.1:23000/</parameter>
</instance>
',NULL,'cloudooo','Cloudooo','slappart0','started',NULL);
INSERT INTO "partition16" VALUES('slappart3','computer','busy','/srv/slapgrid//srv//runner/project//slapos/software.cfg','<?xml version=''1.0'' encoding=''utf-8''?>
<instance/>
','<?xml version=''1.0'' encoding=''utf-8''?>
<instance>
  <parameter id="url">memcached://127.0.0.1:11000/</parameter>
</instance>
',NULL,'memcached','Memcached','slappart0','started',NULL);
INSERT INTO "partition16" VALUES('slappart4','computer','busy','/srv/slapgrid//srv//runner/project//slapos/software.cfg','<?xml version=''1.0'' encoding=''utf-8''?>
<instance/>
','<?xml version=''1.0'' encoding=''utf-8''?>
<instance>
  <parameter id="url">memcached://127.0.0.1:13301/</parameter>
</instance>
',NULL,'kumofs','KumoFS','slappart0','started',NULL);
INSERT INTO "partition16" VALUES('slappart5','computer','busy','/srv/slapgrid//srv//runner/project//slapos/software.cfg','<?xml version=''1.0'' encoding=''utf-8''?>
<instance>
  <parameter id="kumofs-url">memcached://127.0.0.1:13301/</parameter>
  <parameter id="memcached-url">memcached://127.0.0.1:11000/</parameter>
  <parameter id="cloudooo-url">cloudooo://127.0.0.1:23000/</parameter>
</instance>
','<?xml version=''1.0'' encoding=''utf-8''?>
<instance>
  <parameter id="url">https://[fc00::1]:10001</parameter>
</instance>
',NULL,'tidstorage','TidStorage','slappart0','started',NULL);
INSERT INTO "partition16" VALUES('slappart6','computer','free',NULL,NULL,NULL,NULL,NULL,NULL,NULL,'started',NULL);
INSERT INTO "partition16" VALUES('slappart7','computer','free',NULL,NULL,NULL,NULL,NULL,NULL,NULL,'started',NULL);
INSERT INTO "partition16" VALUES('slappart8','computer','free',NULL,NULL,NULL,NULL,NULL,NULL,NULL,'started',NULL);
INSERT INTO "partition16" VALUES('slappart9','computer','free',NULL,NULL,NULL,NULL,NULL,NULL,NULL,'started',NULL);
CREATE TABLE slave16 (
  reference VARCHAR(255), -- unique slave reference
  computer_reference VARCHAR(255) DEFAULT 'computer',
  connection_xml TEXT,
  hosted_by VARCHAR(255),
  asked_by VARCHAR(255) -- only used for debugging,
                        -- slapproxy does not support proper scope
);
CREATE TABLE partition_network16 (
  partition_reference VARCHAR(255),
  computer_reference VARCHAR(255) DEFAULT 'computer',
  reference VARCHAR(255),
  address VARCHAR(255),
  netmask VARCHAR(255)
);
INSERT INTO "partition_network16" VALUES('slappart0','computer','slappart0','127.0.0.1','255.255.255.255');
INSERT INTO "partition_network16" VALUES('slappart0','computer','slappart0','fc00::1','ffff:ffff:ffff::');
INSERT INTO "partition_network16" VALUES('slappart1','computer','slappart1','127.0.0.1','255.255.255.255');
INSERT INTO "partition_network16" VALUES('slappart1','computer','slappart1','fc00::1','ffff:ffff:ffff::');
INSERT INTO "partition_network16" VALUES('slappart2','computer','slappart2','127.0.0.1','255.255.255.255');
INSERT INTO "partition_network16" VALUES('slappart2','computer','slappart2','fc00::1','ffff:ffff:ffff::');
INSERT INTO "partition_network16" VALUES('slappart3','computer','slappart3','127.0.0.1','255.255.255.255');
INSERT INTO "partition_network16" VALUES('slappart3','computer','slappart3','fc00::1','ffff:ffff:ffff::');
INSERT INTO "partition_network16" VALUES('slappart4','computer','slappart4','127.0.0.1','255.255.255.255');
INSERT INTO "partition_network16" VALUES('slappart4','computer','slappart4','fc00::1','ffff:ffff:ffff::');
INSERT INTO "partition_network16" VALUES('slappart5','computer','slappart5','127.0.0.1','255.255.255.255');
INSERT INTO "partition_network16" VALUES('slappart5','computer','slappart5','fc00::1','ffff:ffff:ffff::');
INSERT INTO "partition_network16" VALUES('slappart6','computer','slappart6','127.0.0.1','255.255.255.255');
INSERT INTO "partition_network16" VALUES('slappart6','computer','slappart6','fc00::1','ffff:ffff:ffff::');
INSERT INTO "partition_network16" VALUES('slappart7','computer','slappart7','127.0.0.1','255.255.255.255');
INSERT INTO "partition_network16" VALUES('slappart7','computer','slappart7','fc00::1','ffff:ffff:ffff::');
INSERT INTO "partition_network16" VALUES('slappart8','computer','slappart8','127.0.0.1','255.255.255.255');
INSERT INTO "partition_network16" VALUES('slappart8','computer','slappart8','fc00::1','ffff:ffff:ffff::');
INSERT INTO "partition_network16" VALUES('slappart9','computer','slappart9','127.0.0.1','255.255.255.255');
INSERT INTO "partition_network16" VALUES('slappart9','computer','slappart9','fc00::1','ffff:ffff:ffff::');
CREATE TABLE forwarded_partition_request16 (
  partition_reference VARCHAR(255), -- a.k.a source_instance_id
  master_url VARCHAR(255),
  CONSTRAINT uniq PRIMARY KEY (partition_reference, master_url)
);
INSERT INTO "forwarded_partition_request16" VALUES('forwarded_instance','https://bogus/master/url');
COMMIT;
