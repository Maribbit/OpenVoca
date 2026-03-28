---
applyTo: "**"
---

Use the `vscode_askQuestions` tool in two scenarios:

1. **Mid-task clarification** — When you need answers from the user before you can proceed (e.g., design decisions, ambiguous requirements, approval models). Do NOT write questions as prose; always use the tool so the user gets an interactive prompt.
2. **Post-task follow-up** — After completing any user request, check if additional work is needed before ending your turn.

> **Tool lookup**: The tool may be deferred. Search for it with `askQuestion` pattern before first use.

## Rules
- When you have blocking questions that affect how you proceed, ask BEFORE doing the work
- After task completion, always ask if more work is needed
- Stop asking when the user confirms no further steps or says something like "done", "that's all", or "no"
- Keep questions concise

## Example

**User:** "Write a Python script that analyzes sales data and generates a report."

**Assistant:** 
1. Writes the Python script
2. Uses `vscode_askQuestions` tool:
   - Question: "Would you like me to do anything else with this script? (e.g., add tests, improve error handling, add documentation)"

**User:** "Add unit tests"

**Assistant:**
1. Adds unit tests
2. Uses `vscode_askQuestions` tool again

**User:** "No, that's all"

**Assistant:** Ends the session without asking further questions.

## Important: Always Loop

Even if the user provides a new, unrelated task in their response, you MUST still call `vscode_askQuestions` after completing that task. The loop only ends when the user explicitly indicates they are done.

**Example of task switching:**

**User:** "Explain Java"

**Assistant:**
1. Explains Java
2. Uses `vscode_askQuestions` tool:
   - Question: "Is there anything else you'd like to know?"

**User:** "Now create a hello world program"

**Assistant:**
1. Creates the program
2. Uses `vscode_askQuestions` tool again (loop continues)

**User:** "That's all, thanks"

**Assistant:** Ends without asking further.