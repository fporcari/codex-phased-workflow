# Contributing

Keep changes small and protocol-aware. A modification to `.phased/` layout,
markers, note fields, plan parsing, or commit semantics requires a compatibility
test using both Claude-originated and Codex-originated fixtures.

Run `./tests/run_tests.sh` before opening a pull request. Do not include AI or
tool attribution in commits or GitHub content.
