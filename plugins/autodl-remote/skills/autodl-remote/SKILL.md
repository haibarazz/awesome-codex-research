---
name: autodl-remote
description: Use when the host coding agent should control an AutoDL or SSH server from the local machine, run remote commands, and explicitly upload or download selected files.
---

# AutoDL Remote

Use this skill when the user wants the host coding agent to work locally while controlling AutoDL through SSH.

## Operating Model

- The plugin is a thin SSH tool layer.
- When the `autodl_*` MCP tools are available, prefer them for bounded account, project, file, transfer, execution, job/run, fleet, tmux, dashboard, and shutdown operations. Supply the absolute local project path as `projectRoot`.
- Keep MCP file, transfer, sync-up, remote-cwd, and dashboard-output operands project-relative. Use the explicit account/remote context overrides when a different bound remote root is intended.
- Use the CLI when the operation intentionally remains outside MCP: password save/delete, interactive `shell`, `exec --script`, `exec --stdin`, following logs, or a continuously watched/opened dashboard.
- MCP destructive actions require their documented confirmation value. Never invent confirmation on the user's behalf when approval is required.
- For AutoDL or remote SSH work, first verify the tool with `autodl-remote --version`, then use `autodl-remote` as the default gateway for remote commands and file transfer.
- Do not hand-write raw `ssh`, `expect`, `scp`, or `rsync` workflows for AutoDL work unless `autodl-remote` is unavailable, the command fails after a reasonable retry, or the user explicitly asks to bypass the plugin.
- If bypassing `autodl-remote`, state the concrete reason before doing so and avoid printing passwords or embedding credentials in shell history/logs.
- For complex remote checks or multi-line scripts, use `autodl-remote exec --script` or `autodl-remote exec --stdin -- bash`; do not pack nested Python heredocs or long quoted scripts into a raw SSH command.
- Do not decide that local or remote is the source of truth globally.
- Do not use `local-main`, `remote-main`, manifests, sparse-cache modes, or automatic code ownership rules.
- The host coding agent decides the smallest useful action each time: inspect, upload, download, run, or tail logs.
- Reusable project assets must be created or edited locally first, then uploaded with `put`, `sync-up`, or `put-run` before remote execution. This includes source code, notebooks, YAML/JSON/TOML configs, prompts, templates, and files needed to reproduce an experiment. Do not create or modify these durable files directly on the remote machine with heredocs, `cat > file`, editors, or shell redirection, unless the user explicitly asks for a remote-only edit.
- Shell commands and shell launch wrappers are normally runtime control, not durable project assets. They may be generated or executed remotely without local persistence for startup glue, environment checks, quoting-heavy commands, process supervision, and one-off experiment launches. Only save shell scripts locally when the user asks to keep them or they become a named project entrypoint.
- Do not download LLM weights, checkpoints, datasets, or large outputs unless the user explicitly asks.
- Prefer reading remote files/logs in place with `cat`, `tail`, `ls`, and `tree`.
- Use detached job commands for long training runs instead of manually guessing process state.
- For long-running, interactive, multi-run, or multi-device work, consider using the tmux backend with `autodl-remote exec --tmux --name <run> -- <command>`. Use ordinary `exec` or `exec --detach` for short non-interactive commands.
- If tmux is useful but missing on the remote machine, do not bypass the plugin with raw SSH. Run `autodl-remote tmux check`, then install it with `autodl-remote tmux install` unless the user has explicitly forbidden remote package installation.
- For tmux-backed jobs, prefer `autodl-remote tmux capture <name>` or the dashboard to inspect live pane output. The dashboard may show tmux pane output directly instead of only log files.
- Use run metadata (`--model`, `--tag`, `--stage`, `--purpose`) when launching experiments so `run list` and the dashboard explain what is running.
- Use `fleet` for multi-device projects and `dashboard` for display-only visibility. The dashboard must not be treated as an operation surface.
- Do not start or open the dashboard by default. For single-device work, prefer `run status`, `run tail`, `job status`, or `tail` unless the user explicitly asks for a dashboard or live visual monitoring.
- For multi-device work, the dashboard is appropriate only when the user asks for a dashboard, overview, or live monitoring; otherwise keep the workflow in CLI commands.
- When the user wants to watch progress visually, run `autodl-remote dashboard --watch <seconds> --lines <n> --open` instead of copying logs into chat.
- Use `shutdown` when the user asks to stop the remote machine; treat SSH disconnect during shutdown as likely success.
- Before using AutoDL Remote in a project, read `.autodl-remote/CONVENTIONS.md` if it exists. Treat it as the project-specific source for runtime, paths, sync rules, and notes.
- When the user and the host coding agent discuss or decide any project-specific remote configuration, runtime environment, path convention, model/data/output location, sync preference, or safety rule, update `.autodl-remote/CONVENTIONS.md` so future sessions can reuse it.
- Keep `.autodl-remote/CONVENTIONS.md` concise and project-specific; do not turn it into a generic manual.
- When writing remote run scripts, emit clear stdout logs because dashboard content comes from the remote log, not from Codex narration. Prefer markers such as `[START]`, `[ENV]`, `[PROGRESS]`, `[METRIC]`, `[OUTPUT]`, `[DONE]`, and `[ERROR]`. For Python, prefer `PYTHONUNBUFFERED=1 python -u ...`.

## Setup

Use an existing account or create one:

```bash
autodl-remote account list
autodl-remote account add autodl-gpu --target root@host --port 2222 --auth prompt
autodl-remote account use autodl-gpu
```

Bind the current local directory to the concrete remote directory the user wants:

```bash
autodl-remote bind --account autodl-gpu --remote /root/autodl-tmp/my-project
```

The project config should only contain `ACCOUNT` and `REMOTE_ROOT`.

## Core Commands

```bash
autodl-remote doctor
autodl-remote model-dir
autodl-remote tree . --depth 2
autodl-remote ls .
autodl-remote cat -- README.md
autodl-remote tail -- logs/train.log

autodl-remote put ./train.py train.py
autodl-remote put-run ./train.py -- python train.py
autodl-remote get outputs/result.csv ./outputs/result.csv
autodl-remote sync-up ./src src
autodl-remote sync-down logs/train.log ./logs/train.log

autodl-remote exec -- pwd
autodl-remote exec -- python train.py
autodl-remote exec --detach --name train --model baseline --stage training -- python train.py
autodl-remote tmux check
autodl-remote exec --tmux --name train-live --model baseline --stage training -- PYTHONUNBUFFERED=1 python -u train.py
autodl-remote tmux capture train-live --lines 200
autodl-remote exec --script scripts/remote_check.sh
cat scripts/remote_check.sh | autodl-remote exec --stdin -- bash
autodl-remote job list
autodl-remote job status train
autodl-remote job tail train --lines 120
autodl-remote job stop train
autodl-remote run list
autodl-remote run stop train
autodl-remote run note train --stage evaluating
autodl-remote fleet create rag-exp
autodl-remote fleet add rag-exp nmb1 --account autodl-nmb1 --remote /root/autodl-tmp/LLM-RAG --tags a800,rag
autodl-remote fleet status rag-exp
autodl-remote tree --account autodl-nmb1 --remote /root/autodl-tmp/LLM-RAG . --depth 2
autodl-remote dashboard
autodl-remote dashboard --fleet rag-exp --open
autodl-remote dashboard --fleet rag-exp --open --watch 5 --lines 120
autodl-remote shutdown
```

## Behavior Rules

- Before editing remote-existing code, inspect with `tree`, `ls`, `cat`, or `get` only the needed files.
- Before running remote code that depends on local edits, explicitly upload the edited files or directories with `put` or `sync-up`.
- Do not use `exec --stdin`, heredocs, `cat >`, remote editors, or remote shell redirection to create reusable project assets on the remote host. Keep durable code and configuration local-first so git and the user's local workspace remain the record. This restriction does not apply to shell commands or shell wrappers used to start, check, or supervise runs.
- After remote execution, inspect logs remotely first; pull only small result files when useful.
- If both local and remote have similar files, do not assume one should overwrite the other. Compare or inspect first, then choose `put` or `get`.
- Use `exec --detach` for long training jobs and then `tail` the log path.
- Use `exec --tmux --name <run>` when live pane visibility matters, when several experiments run in parallel, or when multiple hosts need clearer terminal-state monitoring.
- Prefer `job status <name>`, `job tail <name>`, and `job stop <name>` for detached jobs created with `--name`. Do not reuse an active name unless `exec --replace` explicitly stops the recorded job first.
- Prefer `tmux capture <name>` for tmux-backed jobs when the user asks what the remote terminal currently shows.
- Prefer `run list`, `run status`, `run tail`, `run stop`, and `run note` when the user is thinking in terms of experiments/models rather than raw jobs.
- For multiple machines, use `fleet add/list/status` by default. Use `dashboard --fleet <name>` only after the user asks for a dashboard, overview, or live monitoring.
- When inspecting a non-default fleet device, pass `--account` and `--remote` to `tree`, `ls`, `cat`, `tail`, `put`, `get`, and `exec` instead of rebinding the project.
- The dashboard is read-only and can be used for one device or many devices. Do not add operational assumptions just because the dashboard exists.
- Dashboard logs are pulled from remote run log files. Add useful stdout logging to scripts instead of expecting Codex to summarize progress in chat.
- Prefer `exec --script` or `exec --stdin` for complex multi-line commands, Python heredocs, env vars, JSON, awk, or sed.
- Use `put-run` when the workflow is "upload these local paths, then immediately run this remote command".
- `model-dir` prints the project model directory convention. The first project command creates `.autodl-remote/CONVENTIONS.md` locally for concise project notes.
- `shutdown` first syncs the remote filesystem, then tries provider-safe shutdown methods, waits, and verifies that SSH disconnects.
- Treat broad destructive commands as dangerous; require explicit user approval before using `--allow-dangerous`.
