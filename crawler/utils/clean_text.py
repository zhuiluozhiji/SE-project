def clean_text(value: str | None) -> str:
    if not value:
        return ""
    return " ".join(value.split())
