CREATE TABLE `consistency` (
  `uid` BIGINT UNSIGNED NOT NULL,
  `consistency_error` BOOL DEFAULT 0,
  PRIMARY KEY (`uid`),
  KEY `consistency_error` (`consistency_error`)
) ENGINE=InnoDB;
