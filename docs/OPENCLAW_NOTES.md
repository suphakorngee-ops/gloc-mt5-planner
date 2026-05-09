# OpenClaw Notes For Gloc

OpenClaw is optional.

## Simple Explanation

OpenClaw is like giving AI eyes and hands:

- eyes = read the screen
- hands = click mouse and type keyboard
- brain = still comes from an LLM
- notebook = project `.md` files

Gloc does not need OpenClaw for the current safe workflow because the project already has direct files and commands:

```text
MT5 exporter -> CSV -> Python planner -> journal -> report/dashboard/Discord
```

Direct files are safer than screen clicking.

## When OpenClaw Helps

Use it later if the task requires UI control:

- click MT5 buttons
- inspect a browser page visually
- operate an app with no API/file export
- do repetitive UI tasks

## Why Install Takes Long

It may download or build:

- Node packages
- Python packages
- browser binaries such as Chromium
- Playwright/browser drivers
- native dependencies
- cached model/tool runtimes

This can take a long time on Windows, slow internet, antivirus scanning, or first install.

## Current Decision

Do not make OpenClaw part of the trading path yet.

Use local agent runtime first:

```text
queue -> worker -> report/log/Discord
```

Vloc Executor remains OFF.
