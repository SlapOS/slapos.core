--version:17
CREATE TABLE config%(version)s (
  name TEXT PRIMARY KEY,
  value TEXT
) WITHOUT ROWID;

CREATE TABLE software%(version)s (
  url VARCHAR(255),
  computer_reference VARCHAR(255) DEFAULT '%(computer)s',
  requested_state VARCHAR(255) DEFAULT 'available',
  PRIMARY KEY (url, computer_reference)
);

CREATE TABLE computer%(version)s (
  reference VARCHAR(255) DEFAULT '%(computer)s',
  address VARCHAR(255),
  netmask VARCHAR(255),
  PRIMARY KEY (reference)
);

CREATE TABLE partition%(version)s (
  reference VARCHAR(255),
  computer_reference VARCHAR(255) DEFAULT '%(computer)s',
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
  PRIMARY KEY (reference, computer_reference)
);

CREATE TABLE slave%(version)s (
  reference VARCHAR(255), -- unique slave reference
  computer_reference VARCHAR(255) DEFAULT '%(computer)s',
  connection_xml TEXT,
  hosted_by VARCHAR(255),
  asked_by VARCHAR(255) -- only used for debugging,
                        -- slapproxy does not support proper scope
);

CREATE TABLE partition_network%(version)s (
  partition_reference VARCHAR(255),
  computer_reference VARCHAR(255) DEFAULT '%(computer)s',
  reference VARCHAR(255),
  address VARCHAR(255),
  netmask VARCHAR(255)
);

CREATE TABLE forwarded_partition_request%(version)s (
  partition_reference VARCHAR(255), -- a.k.a source_instance_id
  master_url VARCHAR(255),
  PRIMARY KEY (partition_reference, master_url)
);
