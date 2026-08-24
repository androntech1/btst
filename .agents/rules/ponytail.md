# Ponytail Development Rules

You follow the Ponytail philosophy:
1. **Does this need to exist at all?** (YAGNI) -> If not, skip it.
2. **Already in this codebase?** -> Reuse it, don't rewrite.
3. **Stdlib does it?** -> Use it.
4. **Native platform feature covers it?** -> Use it (e.g. native HTML5 `<input type="date">`, standard CSS, vanilla JS over heavy frameworks).
5. **Already-installed dependency solves it?** -> Use it. Never add new ones for simple tasks.
6. **Can it be one line?** -> Write one line.
7. **Only then: minimum code that works.**

Be lazy about the solution, never careless about security, validation, and error handling.
Do not over-engineer or add unnecessary abstractions.
