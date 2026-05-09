---
title: "The Ultimate Codex Plugin Guide"
type: "guide"
label: "Guide"
project: "Codex Plugins Matter Because the Bottleneck Moved"
---

# The Ultimate Codex Plugin Guide

# The Ultimate Codex Plugin Guide

Codex plugins are not magic.

That is the first thing to get clear.

The magic is the part people see: Codex suddenly knows how to do a job, follow a workflow, read a local reference, or use a tool in the right way. But the plugin itself is mostly packaging. It is the layer that turns a workflow into something installable, repeatable, and shareable.

That distinction matters.

If you think a plugin is where all the intelligence lives, you will overbuild it. If you understand that the skill does the job and the plugin ships the job, the whole thing gets much easier.

![plate-01-plugin-package](https://promptkit.natebjones.com/api/assets/20260504_knu_guide_main/files/9c4ae990-1273-49cf-9457-4df822fee643)

## The Mental Model

There are five pieces to keep straight.

1. A skill teaches Codex how to do a specific job.
2. A plugin packages one or more skills.
3. A manifest tells Codex what is inside the package.
4. A marketplace entry tells Codex where the package lives.
5. A test loop tells you whether the package works in the real world.

That is the map.

Do not start with the marketplace. Do not start with app integrations. Do not start with MCP servers. Start with the workflow.

If Codex cannot follow the workflow as a skill, packaging it as a plugin will not fix it. Packaging makes the work portable. It does not make the work good.

Define good first.

![plate-02-skills-recipes](https://promptkit.natebjones.com/api/assets/20260504_knu_guide_main/files/94454bad-694b-4d13-b91d-f22290b2dee7)

## Step 1: Build The Skill First

A skill is just a folder with a `SKILL.md` file.

That sounds too simple, which is why people skip past it. They want the plugin. They want the install button. They want the fancy wrapper.

But the skill is where the operating procedure lives.

The frontmatter matters. The `name` identifies the skill. The `description` tells Codex when to use it. That description is not decoration. It is the trigger surface.

If the description is vague, Codex will have a vague reason to use it. If the description is sharp, Codex has a much better chance of reaching for it at the right time.

A basic skill looks like this:

```md
---
name: codex-plugin-guide
description: Use when creating, reviewing, or teaching Codex plugin workflows.
---

# Codex Plugin Guide

When the user asks how to build a Codex plugin, explain the relationship between skills, plugin manifests, marketplace entries, installation, and testing.

Follow the checklist in order.
```

The body should not be a wall of generic advice. Codex is already smart. The skill should give it the workflow, references, edge cases, and standards it would not otherwise know.

That is the bottleneck.

## Step 2: Package The Skill As A Plugin

Once the skill works, wrap it.

A plugin needs a `.codex-plugin/plugin.json` file. That manifest tells Codex what the plugin is, where its components live, and how it should show up to a human.

The folder usually looks like this:

```text
my-plugin/
  .codex-plugin/
    plugin.json
  skills/
    codex-plugin-guide/
      SKILL.md
  assets/
    icon.png
    screenshot.png
```

The required file is `.codex-plugin/plugin.json`.

Everything else depends on what you are shipping.

If you are only bundling skills, keep it simple. If your plugin needs app integrations, MCP servers, hooks, or assets, add them after the base path works.

Here is the shape of the manifest:

```json
{
  "name": "codex-plugin-guide",
  "version": "0.1.0",
  "description": "A plugin that teaches Codex how to explain and build Codex plugins.",
  "skills": [
    {
      "source": {
        "path": "./skills/codex-plugin-guide"
      }
    }
  ],
  "interface": {
    "displayName": "Codex Plugin Guide",
    "description": "Build and test Codex plugin workflows.",
    "category": "developer-tools"
  }
}
```

The `interface` section is for humans. Display name, description, category, icon, screenshots, default prompts. That is what makes the thing legible when someone installs it.

Legibility matters.

If you want people to reuse your workflow, they need to understand what it does before they run it.

![plate-03-marketplace-shelf](https://promptkit.natebjones.com/api/assets/20260504_knu_guide_main/files/359f6dd1-c69f-43b3-b7ac-3a56e604c5d2)

## Step 3: Add The Marketplace Entry

This is where people usually lose an hour.

Codex needs a catalog. For a repo, that catalog can live at `.agents/plugins/marketplace.json`. For a local personal setup, it can live under your home directory.

The important part is the path.

`source.path` is relative to the marketplace root. If the path points to the wrong place, Codex will not find your plugin.

That is not a deep AI problem.

It is usually a path problem.

A simple marketplace entry looks like this:

```json
{
  "plugins": [
    {
      "name": "codex-plugin-guide",
      "source": {
        "type": "local",
        "path": "./plugins/codex-plugin-guide"
      }
    }
  ]
}
```

Check the path twice. Then check it again after moving files.

This is the boring part that makes the good part work.

## Step 4: Add Advanced Pieces Only After The Base Plugin Works

A plugin can be more than a skill bundle.

It can expose app integrations. It can register MCP servers. It can include hooks. It can ship assets, templates, screenshots, prompt packs, and local reference material.

But do not add all of that up front.

That is how you create a beautiful failure with six possible causes.

![plate-04-integrations-bridge](https://promptkit.natebjones.com/api/assets/20260504_knu_guide_main/files/439ac8ee-8b0f-4bd4-96d1-365aa4aa9668)

Add advanced pieces in this order:

1. Skills first.
2. Plugin manifest second.
3. Marketplace entry third.
4. Assets fourth.
5. App or MCP integrations last.

The reason is simple. You want one new failure mode at a time.

If the skill does not trigger, fix the skill. If the plugin does not show up, fix the manifest. If Codex cannot install it, fix the marketplace path. If the MCP server fails after that, now you know the base plugin is not the problem.

That saves time.

Velocity compounds.

## Step 5: Restart, Install, Test

Once the files are in place, restart Codex so it reloads the plugin directory.

Then install the plugin.

Then test it in a fresh thread.

Fresh thread matters because you want to know whether the plugin triggers from the plugin metadata and the user request, not from context you accidentally gave Codex ten minutes earlier.

![plate-05-testing-loop](https://promptkit.natebjones.com/api/assets/20260504_knu_guide_main/files/bef1b51d-ab3d-457a-bd85-d45e1b1d8053)

Run five tests:

1. Direct invocation. Mention the plugin or skill by name and see if Codex uses it.
2. Natural language. Ask for the workflow in normal words and see if the description catches it.
3. Missing information. Give Codex an incomplete request and see whether it asks the right question or makes a reasonable assumption.
4. File path behavior. Move nothing, rename nothing, and confirm the installed plugin still resolves every local path.
5. Fresh session behavior. Restart Codex and test again.

Most plugin bugs live in one of those five places.

## The Debugging Checklist

If the plugin does not show up, do not start theorizing.

Run the boring checklist:

1. Is `plugin.json` valid JSON?
2. Is it inside `.codex-plugin/`?
3. Does the skill path start with `./`?
4. Does every `SKILL.md` have a `name` and `description`?
5. Is `source.path` relative to the marketplace root?
6. Did you restart Codex?
7. Are you testing in a fresh thread?
8. Did you accidentally move the plugin folder after writing the marketplace entry?
9. Are you trying to reference an app or connector Codex cannot actually expose?

That list will feel too basic until it saves you.

Then you will keep it.

## What This Is Really About

Plugins are infrastructure for your own workflows.

That is the bigger point.

As intelligence gets cheaper, the value moves to specification, context, packaging, and distribution. A skill is specification. A plugin is packaging. A marketplace is distribution. The test loop is how you keep the whole thing honest.

This is why plugins matter.

They let you turn a good one-off workflow into something repeatable. They let you encode the way you work. They let a team share the same operating procedure instead of relying on everyone to remember the same prompt.

That is where this starts to get interesting.

Do not ask, "Can Codex do this?"

Ask a better question: "Have I given Codex the workflow, context, and installable package it needs to do this the same way twice?"

Build that.

Then tighten it every time it misses.
