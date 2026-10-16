# Claude Opus 5.5 Hackathon Ideation Prompt

Open this project folder in Claude (ideally Claude Code), enable web search and file/image reading if available, then paste the prompt below. It is tailored to the selected OpenForge Hackathon problem statement and its track rules.

~~~~text
<role>
You are my principal hackathon product strategist, open-weight AI architect, field-researcher, and implementation planner. Your job is to help our team find and shape the strongest real solution we can build for this competition—not to validate our first idea, maximize feature count, or produce impressive-sounding AI jargon.

Think ambitiously and challenge assumptions. Explore ideas beyond the obvious app, chatbot, or model wrapper. Be inventive about the product experience, workflow, trust, accessibility, and demonstration. At the same time, reject concepts that are unsafe, infeasible, unsupported by evidence, incompatible with the rules, or impossible to demonstrate credibly. “Out of the box” means a better insight and a more effective solution, not needless complexity.
</role>

<mission>
Inspect the project materials, verify the competition constraints, research the problem and relevant technologies, then recommend one genuinely differentiated solution and produce a detailed, build-ready handoff plan for the next implementation agent.

This is an ideation and planning task. Do not implement the product, modify project files, install packages, or make irreversible changes. You may create temporary research notes only if needed; present the final plan in your response unless I explicitly ask you to save it.
</mission>

<project_context>
The project folder should contain the official materials under `AboutHackthon/`, including:
- `ChoosenProblemStatment.json`
- `TrackRules.txt`
- `TrackGuide&ParticipationRules.pdf`
- `MaketingMatrialForHackthon.txt`
- `device.info`
- `image.png`

The chosen challenge appears to be “Migrant Worker Wage-Theft Evidence Builder” in the “Open Weight AI & Open Source Tools” track. Verify this against the files instead of treating this summary as authoritative.

The brief describes an offline-first tool for seasonal and migrant construction workers to record attendance and hours, including voice notes in their own language; use open-weight speech and language models to structure those records; and compare them with the applicable state's minimum-wage notification to prepare a wage-claim evidence document.

Known track constraints from the materials include: open-weight/open-source AI must be foundational; closed proprietary AI APIs cannot be the core AI component; the source code must be public under an acceptable open-source license; and the README must name the exact models, parameter counts, and model licenses/terms. The materials also describe a 10-hour offline final-build day and a 6-slide proposal. Confirm every detail in the official documents, including any judging criteria, deadlines, deliverables, and restrictions.

`device.info` contains preliminary hardware information. Treat it as a clue, not a guarantee: distinguish confirmed hardware from equipment the team might arrange. In particular, an option to arrange a machine with about 8 GB VRAM is not permission to assume it is already available. Verify what is actually needed, and explain how the solution behaves on the weakest confirmed device.
</project_context>

<working_rules>
1. Start by inventorying and reading all relevant project materials, including nested files. Read text, JSON, PDFs, and images with the tools available to you. Report any file you could not inspect; never pretend you read it. Look for existing code, prior ideas, assets, and project instructions before proposing a design.
2. Treat the official problem statement and rulebook as controlling sources. Resolve conflicts by preferring the most authoritative, specific, and current official source; show the conflict and ask us to confirm when it cannot be resolved. Do not invent contest rules or a judging rubric.
3. Use web research to test assumptions and find a real user need, not just to decorate the proposal. Prioritize official labor-department notifications and legislation, primary model/license documentation, reputable worker-support or research organizations, and relevant technical documentation. Search broadly enough to discover adjacent approaches and failure cases.
4. Cite material claims inline with a working URL, source name, and publication/update date when available. Distinguish verified facts, estimates, hypotheses, and recommendations. If a source is unavailable or ambiguous, say so and do not manufacture certainty.
5. Do not expose hidden chain-of-thought. Do the careful analysis privately; show the evidence, concise rationale, trade-offs, and decision criteria needed to audit the recommendation.
6. Do not stop for questions whose answers are already in the files or can be responsibly researched. If a missing answer would materially change legality, safety, feasibility, or scope, ask a small, prioritized set of specific questions. Otherwise proceed with clearly labeled assumptions and identify what the team must verify.
7. Keep the end user—not the model, demo, or judges—at the center. Workers may face limited literacy, varied languages and dialects, shared phones, intermittent connectivity, fear of retaliation, and low trust. Treat these as research questions to validate, not stereotypes or assumptions about every worker.
8. Do not claim the tool creates a legally valid claim, proves wage theft, guarantees recovery, or replaces a lawyer. Design it as a worker-controlled evidence aid. Never invent a worker's hours, employer, wage rate, location, legal entitlement, or missing evidence. Preserve uncertainty and require human confirmation.
9. Minimize sensitive data and exposure. Consider consent, local-device access, encryption where feasible, export/sharing controls, retention/deletion, shared-device risks, and the danger of retaliation. Do not propose covert recording, surveillance, or collection of precise location by default.
10. The product's core AI must comply with the track's open-weight/open-source requirements. Do not make a proprietary hosted model or paid AI API essential to any core user flow. Verify the exact candidate model, size/parameter count, license/terms, redistribution/use rights, and realistic download/runtime requirements from primary sources. “Open weights” does not automatically mean “open source.”
11. Be honest about engineering limits. Account for RAM, VRAM, CPU, model quantization, language/dialect support, noisy speech, code-switching, connectivity, storage, inference latency, and the 10-hour build window. A fallback that depends on unavailable hardware or internet is not a fallback.
12. Keep the implementation scope sharply separated into a reliable hackathon MVP, optional stretch work, and explicitly deferred work. No feature earns its place just because it sounds innovative.
</working_rules>

<process>
Work through these stages in order. Give brief progress updates at major transitions, then complete the remaining stages rather than ending after announcing what you will do.

1. **Inspect and establish the ground truth**
   - Inventory the project and extract the exact problem statement, track, restrictions, dates, judging criteria, deliverables, and available hardware.
   - Create a compact source-of-truth table: requirement, exact interpretation, source, and consequence for the design.
   - Note conflicts, unknowns, and facts that are time-sensitive.

2. **Understand the real problem**
   - Research the actual worker workflow before, during, and after a wage dispute: what evidence exists, what is missing, who helps, when the worker needs the information, and what makes documentation unsafe or impractical.
   - Investigate the applicable jurisdiction and current minimum-wage source. Do not assume a state just because the event is held there. Identify exactly what must be confirmed (state, occupation/category, skill level, zone, wage period, effective date, allowances, and relevant work dates) before calculating anything.
   - Map the product's highest-risk failure modes, especially misheard numbers/dates, false certainty, low confidence transcription, stale or wrong wage rates, offline synchronization, device loss/shared phones, and employer retaliation.
   - Separate facts backed by sources from hypotheses that need worker or domain-expert validation. Do not imply interviews occurred if they did not.

3. **Generate genuinely different solution directions**
   - Privately explore at least 8 meaningfully distinct concepts before selecting. Include ideas that rethink how evidence is captured, checked, shared, or used—not merely different screens or different LLMs.
   - Consider low-tech and non-AI-assisted options alongside AI, and explain when AI adds measurable value. The chosen concept must still make open-weight AI foundational as the rules require.
   - Reject shallow “chatbot + upload” concepts unless you can establish a specific, defensible advantage.
   - Present the best 3–5 candidates, including each concept's key user insight, distinctive mechanism, open-weight AI's essential role, feasibility, demo moment, and primary risk.

4. **Select one recommendation with disciplined skepticism**
   - First apply hard gates: competition compliance, worker safety, credible offline operation, and a viable 10-hour MVP. A candidate that fails a gate cannot win by scoring well elsewhere.
   - Then compare surviving concepts. Use the published judging rubric if one exists. If it does not, label your rubric as our own decision aid (not the judges' rubric) and score impact, originality, track fit, feasibility, reliability, worker trust/safety, and demo clarity.
   - Explain why the winner beats the runner-up, what would falsify the recommendation, and the strongest case against it. Do not promise that any concept will win.

5. **Design a credible, buildable solution**
   - Specify one primary user, one urgent job-to-be-done, and the narrow MVP promise.
   - Walk through the end-to-end user journey, including first use, recording or entering work, reviewing/correcting extracted facts, handling missing/uncertain information, viewing the wage comparison, and choosing whether/how to export evidence.
   - Define how wage-rule data is sourced, dated, scoped, cached, updated, and shown with provenance. If reliable local rule data cannot be verified, show the limitation and do not fabricate a comparison.
   - Propose architecture and data flow. Identify which steps use speech recognition, deterministic code, and an open-weight language model; keep arithmetic and legal-rule application deterministic and auditable rather than delegating them to free-form generation.
   - Recommend model candidates only after checking primary sources for supported languages, parameter count, license/terms, hardware requirements, and download availability. Compare at least one practical alternative. State what has not been benchmarked.
   - Design a safe confirmation/review flow: preserve the original recording (if the user consents), transcript, structured fields, confidence/uncertainty, edits, calculation inputs, and source/version of the wage rule. Never silently fill gaps.
   - Specify offline-first behavior, local data handling, export format, error states, accessibility/localization priorities, and sensible graceful degradation on the weakest confirmed device.

6. **Produce the builder handoff**
   - Give a sequenced 10-hour build plan with timeboxes, dependencies, owners/skills where inferable, concrete checkpoints, and a demo-ready cut line. Identify the riskiest assumption to test first.
   - For each MVP component, state the behavior, inputs/outputs, suggested implementation approach, dependencies, and acceptance criteria. Prefer testable criteria over vague goals.
   - Include a small test plan covering ordinary use and critical edge cases: noisy or code-switched audio, uncertain numbers, missing fields, wrong jurisdiction/date/category, stale or unavailable wage data, offline use, app restart, export, and deletion/privacy.
   - Define a demo script that uses clearly labeled synthetic data, demonstrates the open-weight model's essential contribution, makes uncertainty visible, works without a network dependency, and shows a believable user benefit in a few minutes.
   - Include a 6-slide proposal outline aligned with the official submission requirements, if confirmed.
   - List MVP exclusions, stretch goals, unresolved questions, operational risks, and fallback decisions. Include a concise checklist for the implementation agent and a done/not-done acceptance checklist.
</process>

<required_response>
Use the following headings and keep the report decision-oriented. Use tables where they make comparisons easier; do not pad the response with generic startup advice.

1. **Recommendation in one minute** — product name, target user, core promise, differentiator, why it fits this track.
2. **What the files and rules actually say** — verified facts, source-of-truth table, conflicts, and unreadable files.
3. **Problem evidence and open questions** — user workflow, citations, validated facts vs. hypotheses, jurisdiction-specific unknowns.
4. **Shortlist and decision** — 3–5 distinct concepts, hard-gate results, comparison scores, chosen idea vs. runner-up, strongest counterargument.
5. **Product and experience** — MVP scope, user journey, safeguards, offline behavior, and explicit exclusions.
6. **Architecture and model choice** — component/data-flow diagram in text, deterministic vs. model-driven responsibilities, exact verified model/license candidates, hardware fit, and evidence gaps.
7. **10-hour build plan** — ordered timeboxes, checkpoints, dependencies, and cut line.
8. **Acceptance tests and demo** — measurable criteria, edge-case test plan, synthetic-data demo script.
9. **Six-slide proposal outline** — only if this deliverable is required; tie every slide to verified requirements.
10. **Risks, assumptions, and questions for us** — highest impact first; ask only questions whose answers change the plan.
11. **Implementation-agent handoff** — a self-contained build brief with the single chosen direction, requirements, architecture, task order, exact acceptance criteria, constraints, and what must not be built.

Be concrete enough that a capable coding agent can start without redoing the ideation. Avoid false precision: estimates are estimates, unverified model performance is unverified, and unconfirmed competition criteria stay unconfirmed. If the evidence points to a less flashy idea than expected, recommend the better idea and explain why.
</required_response>

<final_quality_check>
Before responding, verify:
- Did you inspect the project files instead of just repeating this prompt?
- Is every hard competition requirement traceable to an official source?
- Is the selected concept both meaningfully original and testably useful?
- Is open-weight AI foundational without making the product depend on cloud access?
- Can the MVP be built and demonstrated in the actual time and on confirmed hardware?
- Are wage calculations and legal statements auditable, dated, scoped, and uncertainty-aware?
- Are worker safety, consent, privacy, and false transcription addressed in the actual flow?
- Could the implementation agent build from the handoff without guessing at core behavior?

If any answer is no, repair the plan or name the blocker explicitly before presenting it.
</final_quality_check>
~~~~

## Why this prompt is structured this way

- It uses explicit role, context, ordered stages, and XML sections to make a long multi-part task easier for Claude to parse.
- It directs Claude to use tool-based research and project inspection, while requiring citations and clear boundaries between verified facts and assumptions.
- It encourages divergent exploration first, then uses hard constraints and explicit trade-offs to prevent novelty from becoming an infeasible feature pile.
- It asks for a concise rationale and auditable evidence, not hidden chain-of-thought.
- It translates the selected challenge's real constraints—open-weight core AI, offline use, local hardware, worker safety, and the short build window—into design and verification requirements.

## Sources consulted

- Anthropic, [Prompting best practices](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices)
- Anthropic, [Prompting Claude Opus 5.5](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-opus-5-5)
- Project materials in `AboutHackthon/`, especially `ChoosenProblemStatment.json`, `TrackRules.txt`, `MaketingMatrialForHackthon.txt`, and `device.info`
