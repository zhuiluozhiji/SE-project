ALTER TABLE schedule_event
  ADD COLUMN marker_label VARCHAR(8) NULL AFTER color_type;

ALTER TABLE schedule_event
  MODIFY color_type VARCHAR(32) NOT NULL DEFAULT 'green';
