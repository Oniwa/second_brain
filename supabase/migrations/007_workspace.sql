-- Add nullable workspace column: which project/repo a thought was captured while working in
-- (capture context, not subject matter — orthogonal to category='project', which means
-- "this thought is about a project"). null = unscoped/global (external knowledge + anything
-- unrecognized) and is always eligible in every workspace-scoped query, preserving
-- cross-pollination. See plans/done/project_scoping_field.md for full design.
ALTER TABLE public.thoughts
  ADD COLUMN IF NOT EXISTS workspace text;

CREATE INDEX IF NOT EXISTS thoughts_workspace_idx ON public.thoughts (workspace);

-- Backfill — exact/tight predicates only, gated on is_external = false, verified against the
-- live DB (2026-07-10). A broad keyword regex is unsafe here: during design it false-matched
-- an external Substack pan's "governance/agent" wording, which must stay null.

-- agile_backlog_builder (19 rows) — every "agile_backlog_builder" source variant
-- (bare, "MIS agile_backlog_builder session ...", "MIS_agile_backlog_builder session ...").
UPDATE public.thoughts
  SET workspace = 'agile_backlog_builder'
  WHERE is_external = false
    AND source ILIKE '%agile_backlog_builder%';

-- abucw (18 rows) — exact IN-list. Sources are heterogeneous free text (RCAs, milestones,
-- /recap threads, CA-15 references, service-name incidents) with no single safe common
-- substring, so each is matched verbatim rather than by pattern.
UPDATE public.thoughts
  SET workspace = 'abucw'
  WHERE is_external = false
    AND source IN (
      'recap: session 2026-06-29 ABU env/deploy + base-image audit',
      'Milestone: 2026-06-29 ABU CW prod env rollout complete',
      'RCA: 2026-05-26 ABU prod outage — Release 29 broken Dockerfile + disk-full + cleanup script + nginx cascade',
      'ABU CW — CA-15 gated to consolidation Phase 1; interim manual mitigation',
      'RCA: 2026-04-28 ABU nginx CD double-failure (syntax error + regex catch-all) — 2 of April''s 3 SEV-1s',
      'ABU Consolidated Website — running incident/outage log',
      'RCA: 2026-06-29 baseinfo-api-dev crash loop (DNS short-name)',
      '/recap end-of-day 2026-06-29 — ABU CW open threads',
      'user-directed next step: 2026-06-29 ABU env prod rollout',
      'RCA: 2026-06-30 rolemgmt "under maintenance" outage (nginx stale upstream IP / CA-15)',
      '/recap 2026-06-30 — ABU CW open threads (post rolemgmt outage)',
      'RCA: 2026-03-23 ABU frontend homepage crash (App Insights key missing from secure file)',
      '/recap 2026-06-30 — ABU outage-count audit (learned)',
      '/recap 2026-06-30 — ABU outage backfill (open thread)',
      'CA-15 proxy_pass conversion done by Katelyn (PR #10846) — verify during consolidation'
    );

-- idea_center_ai_policy (21 rows — extended from the plan's original 6; see
-- plans/done/project_scoping_field.md for reasoning). The plan's 6-row count was verified
-- against the 2026-07-08 DB snapshot, matching only the 4 pre-existing AI-governance sources
-- below. 15 more rows landed 2026-07-10, deliberately tagged with the workspace slug directly
-- in `source` by the user's recap run that day specifically to ease this backfill — matched
-- via ILIKE since the slug is literally present, alongside an exact IN-list for the 4 older
-- rows that don't carry it.
UPDATE public.thoughts
  SET workspace = 'idea_center_ai_policy'
  WHERE is_external = false
    AND (
      source ILIKE '%idea_center_ai_policy%'
      OR source IN (
        'recap: session 2026-06-25 AI governance meeting prep',
        'meeting: AI Governance work-group session 1 (2026-06-26)',
        'synthesis: AI Governance framework v2 (NIST AI RMF + ISO/IEC 42001)',
        'synthesis: AI-Orchestrated SDLC Governance (NIST AI RMF + SSDF + SLSA + OWASP LLM)'
      )
    );
