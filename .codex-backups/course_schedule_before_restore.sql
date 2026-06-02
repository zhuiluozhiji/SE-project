-- MySQL dump 10.13  Distrib 8.0.46, for Linux (x86_64)
--
-- Host: localhost    Database: se_project
-- ------------------------------------------------------
-- Server version	8.0.46

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `course_schedule`
--

DROP TABLE IF EXISTS `course_schedule`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `course_schedule` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `course_name` varchar(128) NOT NULL,
  `teacher` varchar(128) DEFAULT NULL,
  `weekday` int NOT NULL,
  `start_section` int NOT NULL,
  `end_section` int NOT NULL,
  `weeks` varchar(64) DEFAULT NULL,
  `location` varchar(255) DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `fk_course_user` (`user_id`),
  CONSTRAINT `fk_course_user` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=13 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `course_schedule`
--

LOCK TABLES `course_schedule` WRITE;
/*!40000 ALTER TABLE `course_schedule` DISABLE KEYS */;
INSERT INTO `course_schedule` VALUES (1,1,'机器学习','李老师',1,3,4,'1-16','紫金港东1A-101','2026-05-23 11:11:08'),(2,1,'计算机网络','许海涛',3,3,5,'秋冬','玉泉教4-301','2026-06-02 05:50:38'),(3,1,'计算机网络','许海涛',3,11,13,'秋冬','玉泉曹光彪西-304','2026-06-02 05:50:38'),(4,1,'打开艺术之门——钢琴','陈曦',1,6,8,'秋冬','紫金港西3-B109','2026-06-02 05:50:38'),(5,1,'操作系统','季江民/王海帅',2,7,8,'秋冬','玉泉教4-201','2026-06-02 05:50:38'),(6,1,'操作系统','季江民/王海帅',4,7,8,'秋冬','玉泉教4-201','2026-06-02 05:50:38'),(7,1,'操作系统','季江民/王海帅',2,9,10,'秋冬','玉泉曹光彪西-503','2026-06-02 05:50:38'),(8,1,'桨板（初级）','贾浩程',3,6,7,'秋冬','紫金港水上码头','2026-06-02 05:50:38'),(9,1,'计算理论','郑乾',1,3,4,'秋冬','玉泉教4-302','2026-06-02 05:50:38'),(10,1,'日语Ⅰ','任洁',1,9,10,'秋冬','紫金港东1A-205','2026-06-02 05:50:38'),(11,1,'日语Ⅰ','任洁',3,9,10,'秋冬','紫金港东1A-205','2026-06-02 05:50:38'),(12,1,'计算理论导引课程介绍如下','郑乾',1,3,5,'秋冬','玉泉教4-302','2026-06-02 06:23:39');
/*!40000 ALTER TABLE `course_schedule` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `schedule_event`
--

DROP TABLE IF EXISTS `schedule_event`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `schedule_event` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `title` varchar(255) NOT NULL,
  `type` varchar(32) NOT NULL,
  `activity_id` int DEFAULT NULL,
  `start_time` datetime NOT NULL,
  `end_time` datetime NOT NULL,
  `location` varchar(255) DEFAULT NULL,
  `color_type` varchar(32) NOT NULL DEFAULT 'green',
  `marker_label` varchar(8) DEFAULT NULL,
  `remark` varchar(500) DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_schedule_user_time` (`user_id`,`start_time`,`end_time`),
  KEY `fk_schedule_activity` (`activity_id`),
  CONSTRAINT `fk_schedule_activity` FOREIGN KEY (`activity_id`) REFERENCES `activity` (`id`) ON DELETE SET NULL,
  CONSTRAINT `fk_schedule_user` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=15 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `schedule_event`
--

LOCK TABLES `schedule_event` WRITE;
/*!40000 ALTER TABLE `schedule_event` DISABLE KEYS */;
INSERT INTO `schedule_event` VALUES (1,1,'机器学习课程','course',NULL,'2026-05-10 13:00:00','2026-05-10 15:00:00','紫金港东1A-101','course',NULL,NULL,'2026-05-23 11:11:08'),(2,1,'人工智能前沿讲座','activity',101,'2026-05-10 14:00:00','2026-05-10 16:00:00','紫金港校区西区报告厅','green',NULL,NULL,'2026-06-02 05:46:25'),(3,1,'数据库系统学术沙龙','activity',102,'2026-05-12 18:30:00','2026-05-12 20:00:00','玉泉校区曹光彪楼会议室','green',NULL,NULL,'2026-06-02 05:46:37'),(4,1,'计算机网络','course',NULL,'2026-06-03 10:00:00','2026-06-03 12:25:00','玉泉教4-301','blue',NULL,NULL,'2026-06-02 05:50:38'),(5,1,'计算机网络','course',NULL,'2026-06-03 18:50:00','2026-06-03 21:15:00','玉泉曹光彪西-304','blue',NULL,NULL,'2026-06-02 05:50:38'),(6,1,'打开艺术之门——钢琴','course',NULL,'2026-06-01 13:25:00','2026-06-01 15:50:00','紫金港西3-B109','blue',NULL,NULL,'2026-06-02 05:50:38'),(7,1,'操作系统','course',NULL,'2026-06-02 14:15:00','2026-06-02 15:50:00','玉泉教4-201','blue',NULL,NULL,'2026-06-02 05:50:38'),(8,1,'操作系统','course',NULL,'2026-06-04 14:15:00','2026-06-04 15:50:00','玉泉教4-201','blue',NULL,NULL,'2026-06-02 05:50:38'),(9,1,'操作系统','course',NULL,'2026-06-02 16:15:00','2026-06-02 17:50:00','玉泉曹光彪西-503','blue',NULL,NULL,'2026-06-02 05:50:38'),(10,1,'桨板（初级）','course',NULL,'2026-06-03 13:25:00','2026-06-03 15:00:00','紫金港水上码头','blue',NULL,NULL,'2026-06-02 05:50:38'),(11,1,'计算理论','course',NULL,'2026-06-01 10:00:00','2026-06-01 11:35:00','玉泉教4-302','blue',NULL,NULL,'2026-06-02 05:50:38'),(12,1,'日语Ⅰ','course',NULL,'2026-06-01 16:15:00','2026-06-01 17:50:00','紫金港东1A-205','blue',NULL,NULL,'2026-06-02 05:50:38'),(13,1,'日语Ⅰ','course',NULL,'2026-06-03 16:15:00','2026-06-03 17:50:00','紫金港东1A-205','blue',NULL,NULL,'2026-06-02 05:50:38'),(14,1,'计算理论导引课程介绍如下','course',NULL,'2026-06-01 10:00:00','2026-06-01 12:25:00','玉泉教4-302','blue',NULL,NULL,'2026-06-02 06:23:39');
/*!40000 ALTER TABLE `schedule_event` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-06-02  6:29:44
