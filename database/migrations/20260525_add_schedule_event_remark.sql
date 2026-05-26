ALTER TABLE schedule_event
  ADD COLUMN remark VARCHAR(500) NULL AFTER marker_label;
