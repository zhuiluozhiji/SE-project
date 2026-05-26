USE se_project;

CREATE TABLE IF NOT EXISTS activity_interaction (
  id INT PRIMARY KEY AUTO_INCREMENT,
  user_id INT NOT NULL,
  activity_id INT NOT NULL,
  action_type VARCHAR(32) NOT NULL,
  source VARCHAR(64),
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_activity_interaction_user_time (user_id, created_at),
  INDEX idx_activity_interaction_user_activity (user_id, activity_id),
  INDEX idx_activity_interaction_activity_action (activity_id, action_type),
  CONSTRAINT fk_activity_interaction_user
    FOREIGN KEY (user_id) REFERENCES user(id)
    ON DELETE CASCADE,
  CONSTRAINT fk_activity_interaction_activity
    FOREIGN KEY (activity_id) REFERENCES activity(id)
    ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
