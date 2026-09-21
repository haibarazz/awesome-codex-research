---
name: autodl-remote-tmux
description: Use when AutoDL Remote should run or monitor long remote jobs through tmux panes.
---

# AutoDL Remote tmux

Use this skill together with `autodl-remote:autodl-remote` when remote jobs need persistent terminal panes.

## When To Use tmux

- Use tmux for long training, prediction, evaluation, or data-processing jobs where live terminal output is useful.
- Use tmux when several experiments run in parallel on one host or across a fleet.
- Use tmux when the user wants dashboard visibility into the actual remote pane, not only a log file.
- Do not use tmux for short one-shot commands, file transfer, `tree`, `cat`, `ls`, `doctor`, or shutdown.

## Required Behavior

- When MCP tools are available, prefer `autodl_tmux` for check/list/capture and `autodl_exec` with `mode=tmux` for launches. Use the absolute local project path as `projectRoot`.
- `autodl_tmux` installation requires `confirm=install-tmux`; killing a session requires `confirm` to exactly match the session name.
- First check availability with `autodl-remote tmux check`.
- If the remote machine does not have tmux and tmux is useful for the task, install it with `autodl-remote tmux install` unless the user has explicitly forbidden remote package installation.
- Do not hand-write raw SSH/tmux commands unless `autodl-remote` is unavailable or the user explicitly asks to bypass it.
- Always use `--name` for tmux runs so the session can be captured, listed, shown in the dashboard, or killed later.
- Keep reusable code and config local-first; tmux is only the remote runner/pane backend.

## Commands

```bash
autodl-remote tmux check
autodl-remote tmux install
autodl-remote tmux list

autodl-remote exec --tmux --name train-exp1 --model baseline --stage training -- \
  PYTHONUNBUFFERED=1 python -u train.py

autodl-remote tmux capture train-exp1 --lines 200
autodl-remote tmux attach-cmd train-exp1
autodl-remote tmux kill train-exp1
```

For fleet devices, pass the same context overrides used by other commands:

```bash
autodl-remote exec --account autodl-nmb1 --remote /root/autodl-tmp/project \
  --tmux --name model-a --model model-a --stage training -- \
  PYTHONUNBUFFERED=1 python -u train.py

autodl-remote tmux capture --account autodl-nmb1 --remote /root/autodl-tmp/project \
  --lines 200 model-a
```

## Monitoring

- Prefer `autodl-remote tmux capture <name>` for a quick current terminal snapshot.
- Prefer `autodl-remote dashboard --watch <seconds> --lines <n>` when the user wants a visual read-only view.
- The dashboard can show tmux pane output for tmux-backed jobs and fall back to log files if the pane is unavailable.
