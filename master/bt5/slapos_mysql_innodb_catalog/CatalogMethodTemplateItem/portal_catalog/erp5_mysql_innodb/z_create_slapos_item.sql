CREATE TABLE `slapos_item` (
  `uid` BIGINT UNSIGNED NOT NULL,
  `slap_state` varchar(255),
  `slap_date` datetime,
  PRIMARY KEY (`uid`, `slap_state`)
) ENGINE=InnoDB;
