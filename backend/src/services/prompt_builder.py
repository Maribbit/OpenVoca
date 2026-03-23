from collections.abc import Sequence


def build_sentence_generation_prompt(words: Sequence[str], prompt_template: str) -> str:
    """
    Construct the final prompt for the LLM.
    Handles target word interpolation and fallback logic when no words are provided.
    """
    normalized_words = [word.strip() for word in words if word.strip()]
    normalized_template = prompt_template.strip()

    if not normalized_template:
        raise ValueError("A prompt template is required to generate a sentence.")

    # Business Logic: Handle empty target words
    if not normalized_words:
        # Inject protective fallback instruction for the LLM
        words_text = (
            "The user did not provide target words. "
            "You may generate any natural English sentence."
        )
    else:
        words_text = ", ".join(normalized_words)

    # Business Logic: Interpolate or Append
    if "{{target_words}}" in normalized_template:
        return normalized_template.replace("{{target_words}}", words_text)

    return f"{normalized_template}\nTarget words: {words_text}."
