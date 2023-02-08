PRAGMA foreign_keys=OFF;
BEGIN TRANSACTION;
CREATE TABLE local_software_release_root17 (
  path VARCHAR(255)
);
INSERT INTO "local_software_release_root17" VALUES('/');
INSERT INTO "local_software_release_root17" VALUES('/');
INSERT INTO "local_software_release_root17" VALUES('/');
CREATE TABLE software17 (
  url VARCHAR(255),
  computer_reference VARCHAR(255) DEFAULT 'slaprunner',
  requested_state VARCHAR(255) DEFAULT 'available',
  CONSTRAINT uniq PRIMARY KEY (url, computer_reference)
);
INSERT INTO "software17" VALUES('/srv/slapgrid/slappart8/srv/runner/project/slapos/software/seleniumrunner/software.cfg','slaprunner','available');
INSERT INTO "software17" VALUES('/srv/slapgrid/slappart8/srv/runner/project/slapos/software/evil/software.cfg','slaprunner','available');
INSERT INTO "software17" VALUES('/srv/slapgrid/slappart8/srv/runner/project/slapos/software/erp5/software.cfg','slaprunner','available');
CREATE TABLE computer17 (
  reference VARCHAR(255) DEFAULT 'slaprunner',
  address VARCHAR(255),
  netmask VARCHAR(255),
  CONSTRAINT uniq PRIMARY KEY (reference)
);
INSERT INTO "computer17" VALUES('slaprunner','10.0.30.235','255.255.255.255');
CREATE TABLE partition17 (
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
  root_partition VARCHAR(255), -- root partition of the instance tree
  requested_state VARCHAR(255) NOT NULL DEFAULT 'started',
  timestamp REAL,
  CONSTRAINT uniq PRIMARY KEY (reference, computer_reference)
);
CREATE TABLE slave17 (
  reference VARCHAR(255), -- unique slave reference
  computer_reference VARCHAR(255) DEFAULT 'slaprunner',
  connection_xml TEXT,
  hosted_by VARCHAR(255),
  asked_by VARCHAR(255) -- only used for debugging,
                        -- slapproxy does not support proper scope
);
CREATE TABLE partition_network17 (
  partition_reference VARCHAR(255),
  computer_reference VARCHAR(255) DEFAULT 'slaprunner',
  reference VARCHAR(255),
  address VARCHAR(255),
  netmask VARCHAR(255)
);
INSERT INTO "partition_network17" VALUES('slappart0','slaprunner','slappart0','10.0.30.235','255.255.255.255');
INSERT INTO "partition_network17" VALUES('slappart0','slaprunner','slappart0','::1','ffff:ffff:ffff::');
INSERT INTO "partition_network17" VALUES('slappart1','slaprunner','slappart1','10.0.30.235','255.255.255.255');
INSERT INTO "partition_network17" VALUES('slappart1','slaprunner','slappart1','::1','ffff:ffff:ffff::');
INSERT INTO "partition_network17" VALUES('slappart2','slaprunner','slappart2','10.0.30.235','255.255.255.255');
INSERT INTO "partition_network17" VALUES('slappart2','slaprunner','slappart2','::1','ffff:ffff:ffff::');
INSERT INTO "partition_network17" VALUES('slappart3','slaprunner','slappart3','10.0.30.235','255.255.255.255');
INSERT INTO "partition_network17" VALUES('slappart3','slaprunner','slappart3','::1','ffff:ffff:ffff::');
INSERT INTO "partition_network17" VALUES('slappart4','slaprunner','slappart4','10.0.30.235','255.255.255.255');
INSERT INTO "partition_network17" VALUES('slappart4','slaprunner','slappart4','::1','ffff:ffff:ffff::');
INSERT INTO "partition_network17" VALUES('slappart5','slaprunner','slappart5','10.0.30.235','255.255.255.255');
INSERT INTO "partition_network17" VALUES('slappart5','slaprunner','slappart5','::1','ffff:ffff:ffff::');
INSERT INTO "partition_network17" VALUES('slappart6','slaprunner','slappart6','10.0.30.235','255.255.255.255');
INSERT INTO "partition_network17" VALUES('slappart6','slaprunner','slappart6','::1','ffff:ffff:ffff::');
INSERT INTO "partition_network17" VALUES('slappart7','slaprunner','slappart7','10.0.30.235','255.255.255.255');
INSERT INTO "partition_network17" VALUES('slappart7','slaprunner','slappart7','::1','ffff:ffff:ffff::');
INSERT INTO "partition_network17" VALUES('slappart8','slaprunner','slappart8','10.0.30.235','255.255.255.255');
INSERT INTO "partition_network17" VALUES('slappart8','slaprunner','slappart8','::1','ffff:ffff:ffff::');
INSERT INTO "partition_network17" VALUES('slappart9','slaprunner','slappart9','10.0.30.235','255.255.255.255');
INSERT INTO "partition_network17" VALUES('slappart9','slaprunner','slappart9','::1','ffff:ffff:ffff::');
INSERT INTO "partition_network17" VALUES('slappart10','slaprunner','slappart10','10.0.30.235','255.255.255.255');
INSERT INTO "partition_network17" VALUES('slappart10','slaprunner','slappart10','::1','ffff:ffff:ffff::');
INSERT INTO "partition_network17" VALUES('slappart11','slaprunner','slappart11','10.0.30.235','255.255.255.255');
INSERT INTO "partition_network17" VALUES('slappart11','slaprunner','slappart11','::1','ffff:ffff:ffff::');
INSERT INTO "partition_network17" VALUES('slappart12','slaprunner','slappart12','10.0.30.235','255.255.255.255');
INSERT INTO "partition_network17" VALUES('slappart12','slaprunner','slappart12','::1','ffff:ffff:ffff::');
INSERT INTO "partition_network17" VALUES('slappart13','slaprunner','slappart13','10.0.30.235','255.255.255.255');
INSERT INTO "partition_network17" VALUES('slappart13','slaprunner','slappart13','::1','ffff:ffff:ffff::');
INSERT INTO "partition_network17" VALUES('slappart14','slaprunner','slappart14','10.0.30.235','255.255.255.255');
INSERT INTO "partition_network17" VALUES('slappart14','slaprunner','slappart14','::1','ffff:ffff:ffff::');
INSERT INTO "partition_network17" VALUES('slappart15','slaprunner','slappart15','10.0.30.235','255.255.255.255');
INSERT INTO "partition_network17" VALUES('slappart15','slaprunner','slappart15','::1','ffff:ffff:ffff::');
INSERT INTO "partition_network17" VALUES('slappart16','slaprunner','slappart16','10.0.30.235','255.255.255.255');
INSERT INTO "partition_network17" VALUES('slappart16','slaprunner','slappart16','::1','ffff:ffff:ffff::');
INSERT INTO "partition_network17" VALUES('slappart17','slaprunner','slappart17','10.0.30.235','255.255.255.255');
INSERT INTO "partition_network17" VALUES('slappart17','slaprunner','slappart17','::1','ffff:ffff:ffff::');
INSERT INTO "partition_network17" VALUES('slappart18','slaprunner','slappart18','10.0.30.235','255.255.255.255');
INSERT INTO "partition_network17" VALUES('slappart18','slaprunner','slappart18','::1','ffff:ffff:ffff::');
INSERT INTO "partition_network17" VALUES('slappart19','slaprunner','slappart19','10.0.30.235','255.255.255.255');
INSERT INTO "partition_network17" VALUES('slappart19','slaprunner','slappart19','::1','ffff:ffff:ffff::');
CREATE TABLE forwarded_partition_request17 (
  partition_reference VARCHAR(255), -- a.k.a source_instance_id
  master_url VARCHAR(255),
  CONSTRAINT uniq PRIMARY KEY (partition_reference, master_url)
);
COMMIT;
