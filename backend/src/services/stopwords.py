"""POS-based function-word filter for the tokenizer.

Instead of a static word list, we filter by Universal POS tags assigned by
spaCy.  This approach is context-aware: 'well' as a NOUN (water well) is
clickable, while 'well' as an ADV ('well done') is filtered.
"""

# Universal POS tags that indicate function words - never clickable.
FUNCTION_POS: frozenset[str] = frozenset(
    {
        "ADP",  # adpositions: in, on, at, by, for, with, to, from...
        "AUX",  # auxiliaries: is, are, was, have, has, do, can, will...
        "CCONJ",  # coordinating conjunctions: and, but, or, nor
        "DET",  # determiners: the, a, an, this, that, some, any...
        "NUM",  # cardinal numbers: one, two, 100...
        "PART",  # particles: not, n't, to (infinitive), 's (possessive)
        "PRON",  # pronouns: I, me, you, he, she, it, we, they...
        "SCONJ",  # subordinating conjunctions: because, if, while, that...
    }
)
