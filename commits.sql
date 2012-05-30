CREATE TABLE `commits` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `commit` varchar(100) NOT NULL,
  `commiter` varchar(200) NOT NULL,
  `commitdate` int(11) NOT NULL,
  `message` varchar(500) NOT NULL,
  `approver` int(11) NOT NULL,
  `approvedate` int(11) NOT NULL,
  `status` int(11) NOT NULL,
  `project` varchar(200) NOT NULL,
  PRIMARY KEY (`id`)
)