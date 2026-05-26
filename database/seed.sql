SET NAMES utf8mb4;

USE se_project;

INSERT INTO user (id, username, password_hash, role, major, college)
VALUES
  (
    1,
    'student001',
    '$2b$12$wVQaGVST72ESc4mkGSpgFeFgDec400alA.LhqR6DC56pm4e.bFx.S',
    'student',
    '计算机科学与技术',
    '计算机科学与技术学院'
  ),
  (
    2,
    'admin001',
    '$2b$12$wVQaGVST72ESc4mkGSpgFeFgDec400alA.LhqR6DC56pm4e.bFx.S',
    'admin',
    NULL,
    '信息技术中心'
  )
ON DUPLICATE KEY UPDATE
  username = VALUES(username),
  password_hash = VALUES(password_hash),
  role = VALUES(role),
  major = VALUES(major),
  college = VALUES(college);

INSERT INTO activity (
  id, title, description, speaker, organizer, college, category, campus, location,
  start_time, end_time, source_url, source_type, hot_score, status
)
VALUES
  (
    101,
    '人工智能前沿讲座',
    '围绕大模型、智能体和可信 AI 的前沿进展进行分享。',
    '张三教授',
    '计算机科学与技术学院',
    '计算机科学与技术学院',
    '讲座',
    '紫金港',
    '紫金港校区西区报告厅',
    '2026-05-10 14:00:00',
    '2026-05-10 16:00:00',
    'https://example.com/activity/101',
    'manual',
    87,
    'open'
  ),
  (
    102,
    '数据库系统学术沙龙',
    '介绍数据库内核、查询优化和云原生数据库方向的最新研究。',
    '李四研究员',
    '软件学院',
    '软件学院',
    '沙龙',
    '玉泉',
    '玉泉校区曹光彪楼会议室',
    '2026-05-12 18:30:00',
    '2026-05-12 20:00:00',
    'https://example.com/activity/102',
    'manual',
    64,
    'open'
  )
ON DUPLICATE KEY UPDATE
  title = VALUES(title),
  description = VALUES(description),
  speaker = VALUES(speaker),
  organizer = VALUES(organizer),
  college = VALUES(college),
  category = VALUES(category),
  campus = VALUES(campus),
  location = VALUES(location),
  start_time = VALUES(start_time),
  end_time = VALUES(end_time),
  source_url = VALUES(source_url),
  source_type = VALUES(source_type),
  hot_score = VALUES(hot_score),
  status = VALUES(status);

DELETE FROM activity_tag WHERE activity_id IN (101, 102);

INSERT INTO activity_tag (activity_id, tag_name)
VALUES
  (101, '人工智能'),
  (101, '计算机'),
  (101, '机器学习'),
  (102, '数据库'),
  (102, '系统')
ON DUPLICATE KEY UPDATE tag_name = VALUES(tag_name);

DELETE FROM user_interest WHERE user_id IN (1, 2);

INSERT INTO user_interest (user_id, tag_name)
VALUES
  (1, '人工智能'),
  (1, '数据库')
ON DUPLICATE KEY UPDATE tag_name = VALUES(tag_name);

DELETE FROM course_schedule
WHERE user_id = 1
  AND weekday = 1
  AND start_section = 3
  AND end_section = 4;

INSERT INTO course_schedule (
  user_id, course_name, teacher, weekday, start_section, end_section, weeks, location
)
VALUES
  (1, '机器学习', '李老师', 1, 3, 4, '1-16', '紫金港东1A-101');

DELETE FROM schedule_event
WHERE user_id = 1
  AND type = 'course'
  AND start_time = '2026-05-10 13:00:00'
  AND end_time = '2026-05-10 15:00:00';

INSERT INTO schedule_event (
  user_id, title, type, activity_id, start_time, end_time, location, color_type
)
VALUES
  (1, '机器学习课程', 'course', NULL, '2026-05-10 13:00:00', '2026-05-10 15:00:00', '紫金港东1A-101', 'blue');
