import re


def strip_markdown_fences(text: str | None) -> str | None:
    """Remove cercas ```json ... ``` comuns em respostas Gemini/Claude."""
    if text is None:
        return None
    stripped = text.strip()
    # padrão ```json\n{...}\n``` ou ```\n{...}\n```
    match = re.match(r"^```(?:json)?\s*\n?(.*?)\n?\s*```$", stripped, re.DOTALL)
    if match:
        return match.group(1).strip()
    return stripped
