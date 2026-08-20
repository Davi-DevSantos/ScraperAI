def format_prompt(html: str, prompt: str):
    prompt = f"""
            {prompt}

            ==============

            {html}
              """
    return prompt