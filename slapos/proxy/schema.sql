--version:18
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

-- A Software Instance is a first-class document, mirroring the master: identity
-- is the opaque instance_guid, title is mutable metadata, shared instances are
-- ordinary rows. The table keeps its implicit SQLite rowid (no WITHOUT ROWID):
-- rowid gives a stable insertion order used by the slave_instance_list
-- projection to reproduce the append-order blob.
CREATE TABLE instance%(version)s (
  instance_guid VARCHAR(255) PRIMARY KEY,
                              -- opaque, immutable. Minted 'SOFTINST-N' for new
                              -- instances; for instances migrated from v17 it is
                              -- the guid the proxy already published for them,
                              -- frozen verbatim. NEVER derived, NEVER parsed.
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
                              -- allocator, present for master-model fidelity
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
CREATE INDEX instance_tree%(version)s
  ON instance%(version)s (root_instance_guid);
CREATE INDEX instance_requested_by%(version)s
  ON instance%(version)s (requested_by_instance_guid);
CREATE INDEX instance_request_scope%(version)s
  ON instance%(version)s (title, root_instance_guid, shared);
CREATE INDEX instance_allocation%(version)s
  ON instance%(version)s (allocated_computer, allocated_partition);

-- The partition is a pure RESOURCE row: a slot with an address and an
-- allocation state. Everything instance-shaped lives in instance.
CREATE TABLE partition%(version)s (
  reference VARCHAR(255),
  computer_reference VARCHAR(255) DEFAULT '%(computer)s',
  slap_state VARCHAR(255) DEFAULT 'free',
  PRIMARY KEY (reference, computer_reference)
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
