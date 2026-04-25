CREATE DATABASE IF NOT EXISTS se_project
  DEFAULT CHARACTER SET utf8mb4
  DEFAULT COLLATE utf8mb4_unicode_ci;

USE se_project;

CREATE TABLE IF NOT EXISTS user (
  id INT PRIMARY KEY AUTO_INCREMENT,
  username VARCHAR(64) NOT NULL UNIQUE,
  password_hash VARCHAR(255) NOT NULL,
  role VARCHAR(32) NOT NULL DEFAULT 'student',
  major VARCHAR(128),
  college VARCHAR(128),
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS activity (
  id INT PRIMARY KEY AUTO_INCREMENT,
  title VARCHAR(255) NOT NULL,
  description TEXT,
  speaker VARCHAR(128),
  organizer VARCHAR(128),
  college VARCHAR(128),
  category VARCHAR(64),
  campus VARCHAR(64),
  location VARCHAR(255),
  start_time DATETIME,
  end_time DATETIME,
  source_url VARCHAR(512),
  source_type VARCHAR(32) NOT NULL DEFAULT 'manual',
  hot_score INT NOT NULL DEFAULT 0,
  status VARCHAR(32) NOT NULL DEFAULT 'open',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_activity_time (start_time, end_time),
  INDEX idx_activity_status (status),
  INDEX idx_activity_campus (campus)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS activity_tag (
  id INT PRIMARY KEY AUTO_INCREMENT,
  activity_id INT NOT NULL,
  tag_name VARCHAR(64) NOT NULL,
  UNIQUE KEY uk_activity_tag (activity_id, tag_name),
  CONSTRAINT fk_activity_tag_activity
    FOREIGN KEY (activity_id) REFERENCES activity(id)
    ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS user_interest (
  id INT PRIMARY KEY AUTO_INCREMENT,
  user_id INT NOT NULL,
  tag_name VARCHAR(64) NOT NULL,
  UNIQUE KEY uk_user_interest (user_id, tag_name),
  CONSTRAINT fk_user_interest_user
    FOREIGN KEY (user_id) REFERENCES user(id)
    ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS course_schedule (
  id INT PRIMARY KEY AUTO_INCREMENT,
  user_id INT NOT NULL,
  course_name VARCHAR(128) NOT NULL,
  teacher VARCHAR(128),
  weekday INT NOT NULL,
  start_section INT NOT NULL,
  end_section INT NOT NULL,
  weeks VARCHAR(64),
  location VARCHAR(255),
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_course_user
    FOREIGN KEY (user_id) REFERENCES user(id)
    ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS schedule_event (
  id INT PRIMARY KEY AUTO_INCREMENT,
  user_id INT NOT NULL,
  title VARCHAR(255) NOT NULL,
  type VARCHAR(32) NOT NULL,
  activity_id INT,
  start_time DATETIME NOT NULL,
  end_time DATETIME NOT NULL,
  location VARCHAR(255),
  color_type VARCHAR(32) NOT NULL DEFAULT 'activity',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_schedule_user_time (user_id, start_time, end_time),
  CONSTRAINT fk_schedule_user
    FOREIGN KEY (user_id) REFERENCES user(id)
    ON DELETE CASCADE,
  CONSTRAINT fk_schedule_activity
    FOREIGN KEY (activity_id) REFERENCES activity(id)
    ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS registration (
  id INT PRIMARY KEY AUTO_INCREMENT,
  user_id INT NOT NULL,
  activity_id INT NOT NULL,
  status VARCHAR(32) NOT NULL DEFAULT 'joined',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uk_registration_user_activity (user_id, activity_id),
  CONSTRAINT fk_registration_user
    FOREIGN KEY (user_id) REFERENCES user(id)
    ON DELETE CASCADE,
  CONSTRAINT fk_registration_activity
    FOREIGN KEY (activity_id) REFERENCES activity(id)
    ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS crawl_record (
  id INT PRIMARY KEY AUTO_INCREMENT,
  source VARCHAR(64) NOT NULL,
  status VARCHAR(32) NOT NULL,
  fetched_count INT NOT NULL DEFAULT 0,
  success_count INT NOT NULL DEFAULT 0,
  error_msg TEXT,
  run_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS admin_log (
  id INT PRIMARY KEY AUTO_INCREMENT,
  admin_id INT NOT NULL,
  action VARCHAR(64) NOT NULL,
  target_type VARCHAR(64) NOT NULL,
  target_id INT NOT NULL,
  reason VARCHAR(255),
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_admin_log_user
    FOREIGN KEY (admin_id) REFERENCES user(id)
    ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
