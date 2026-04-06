from collections.abc import Sequence


def build_sentence_generation_prompt(
    prompt: str,
    target_words: Sequence[str],
) -> str:
    """Append the internal markdown-marking directive to the user-built prompt.

    The frontend is responsible for assembling the visible prompt (template
    interpolation, scenario/difficulty/length instructions). This function
    only adds the backend-internal instruction that tells the LLM to wrap
    target words in Markdown italics so the tokenizer can identify them.
    """
    final = prompt.strip()

    if not final:
        raise ValueError("A prompt is required to generate a sentence.")

    normalized = [w.strip() for w in target_words if w.strip()]

    if normalized:
        final += (
            " IMPORTANT: You MUST mark the target words in the sentence using Markdown italics, "
            "like *word*. Do not use bold or quotes, only single asterisks."
        )

    return final
