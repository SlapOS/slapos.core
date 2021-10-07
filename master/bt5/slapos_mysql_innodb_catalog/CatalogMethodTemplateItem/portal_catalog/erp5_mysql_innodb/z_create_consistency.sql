CREATE TABLE `consistency` (
  `uid` BIGINT UNSIGNED NOT NULL,
  `consistency_error` BOOL DEFAULT 0,
  PRIMARY KEY (`uid`, `consistency_error`)
) ENGINE=InnoDB;
