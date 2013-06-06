CREATE TABLE `commits` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `hash` varchar(100) NOT NULL,
  `author` varchar(200) NOT NULL,
  `date` int(11) NOT NULL,
  `message` text NOT NULL,
  `approver` varchar(200) NOT NULL,
  `approverdate` int(11) NOT NULL,
  `status` varchar(50) NOT NULL,
  `repository` varchar(200) NOT NULL,
  `branch` varchar(200) NOT NULL,
  PRIMARY KEY (`id`)
)
