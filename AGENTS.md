# Repository instructions

- Conversation with Francesco is in Italian. All repository artifacts are in English.
- Preserve the `.phased/` protocol exactly unless a coordinated compatibility version is planned for both Claude and Codex.
- Never add AI or tool attribution to commits, issues, pull requests, or comments.
- Use `gpt-5.6-sol` for decided implementation and routine review. Choose `gpt-6-astra` upfront for architecture, coupled diagnosis, difficult implementation or material replanning, including a single-engineer task. Repair and specialist review may use Astra when justified by the uncertainty. Do not introduce a lower-quality implementation model.
- After each edit, run the narrowest relevant test or validator.
