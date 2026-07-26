-- Backfill `workspace` for pre-workspace thoughts, so project pages can move to
-- workspace-only scoping (see plans/in_progress/project_page_implementation.md,
-- "RESOLVED 2026-07-26"). Follows the same pattern as migration 007.
--
-- Project pages previously grouped thoughts by anchor topics listed in
-- scripts/project_definitions.json. That mechanism is retired: a project IS a workspace.
-- This migration is therefore the LAST consumer of those anchor-topic lists, and preserves
-- them here as the historical record of how pre-workspace thoughts were scoped.
--
-- Expected: 29 rows total (second_brain 24, boardgame_inventory 3, meal_planner 2).
--
-- Three guards apply to every statement below:
--   1. `workspace is null`    — never overwrite an existing workspace. This is what leaves
--      the one known false positive alone: a thought matching ABUCW's anchor topics that is
--      really `project_tracker` work (project_tracker reads CURRENT.md across active projects
--      to build a priority list — its own project, not part of ABUCW). Also makes this
--      migration idempotent.
--   2. not external          — external content (YouTube, Substack, articles) is deliberately
--      kept global by deriveCaptureWorkspace (mcp/src/server.ts): a /pan run must never be
--      stamped with whatever repo it happened to run from. Four of the 28 second_brain topic
--      matches carry is_external=true and are correctly excluded by this guard.
--   3. topic overlap         — the retired anchor lists, verbatim from project_definitions.json.
--
-- Deliberately NOT backfilled: "Project Forecasting" (1 thought, no repo exists under any
-- spelling, no page exists). It stays unrepresentable under workspace-only scoping.

-- Second Brain — 24 rows (28 exact topic matches minus 4 flagged is_external)
update public.thoughts
   set workspace = 'second_brain'
 where workspace is null
   and coalesce(is_external, false) = false
   and coalesce(source, '') !~* '^(youtube|substack|article|github|synthesis|danshapiro|simonwillison):'
   and topics && array[
     'compile_wiki.py', 'wiki compilation', 'wiki_implementation', 'MCP server',
     'Discord bot', 'audit page', 'process-thought', 'cron automation', 'stale detection'
   ];

-- Board Game Inventory — 3 rows. Slug is the real repo name (github.com/Oniwa/boardgame_inventory),
-- NOT the 'board_game_inventory' a human would guess from the display title.
update public.thoughts
   set workspace = 'boardgame_inventory'
 where workspace is null
   and coalesce(is_external, false) = false
   and coalesce(source, '') !~* '^(youtube|substack|article|github|synthesis|danshapiro|simonwillison):'
   and topics && array['board games', 'board game collection', 'board game inventory'];

-- Meal Planner — 2 rows
update public.thoughts
   set workspace = 'meal_planner'
 where workspace is null
   and coalesce(is_external, false) = false
   and coalesce(source, '') !~* '^(youtube|substack|article|github|synthesis|danshapiro|simonwillison):'
   and topics && array['meal planning', 'Fitbit integration', 'Django', 'nutrition', 'health metrics'];
