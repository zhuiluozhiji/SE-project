from datetime import datetime


def overlaps(new_start: datetime, new_end: datetime, old_start: datetime, old_end: datetime) -> bool:
    return new_start < old_end and new_end > old_start
