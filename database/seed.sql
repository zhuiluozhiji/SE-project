USE se_project;

INSERT INTO user (id, username, password_hash, role, major, college)
VALUES
  (1, 'student001', 'dev-password-hash', 'student', '计算机科学与技术', '计算机科学与技术学院'),
  (2, 'admin001', 'dev-password-hash', 'admin', NULL, '信息技术中心')
ON DUPLICATE KEY UPDATE username = VALUES(username);

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
  )
ON DUPLICATE KEY UPDATE title = VALUES(title);

INSERT INTO activity_tag (activity_id, tag_name)
VALUES
  (101, '人工智能'),
  (101, '计算机'),
  (101, '机器学习')
ON DUPLICATE KEY UPDATE tag_name = VALUES(tag_name);

INSERT INTO user_interest (user_id, tag_name)
VALUES
  (1, '人工智能'),
  (1, '数据库')
ON DUPLICATE KEY UPDATE tag_name = VALUES(tag_name);

INSERT INTO course_schedule (
  user_id, course_name, teacher, weekday, start_section, end_section, weeks, location
)
VALUES
  (1, '机器学习', '李老师', 1, 3, 4, '1-16', '紫金港东1A-101');

INSERT INTO schedule_event (
  user_id, title, type, activity_id, start_time, end_time, location, color_type
)
VALUES
  (1, '机器学习课程', 'course', NULL, '2026-05-10 13:00:00', '2026-05-10 15:00:00', '紫金港东1A-101', 'course');
