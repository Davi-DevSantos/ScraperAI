import re

def strip_markdown_fences(text: str | None) -> str | None:
    if text is None:
        return None
    stripped = text.strip()

    match = re.match(r"^```(?:json)?\s*\n?(.*?)\n?\s*```$", stripped, re.DOTALL)
    if match:
        return match.group(1).strip()
    return stripped
