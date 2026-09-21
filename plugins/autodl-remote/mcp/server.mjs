#!/usr/bin/env node

import { spawn } from "node:child_process";
import { lstatSync, realpathSync, statSync } from "node:fs";
import path from "node:path";
import readline from "node:readline";
import { fileURLToPath } from "node:url";

const SERVER_VERSION = "0.9.0";
const PROTOCOL_VERSION = "2025-06-18";
const pluginRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const cliPath =
  process.env.AUTODL_REMOTE_MCP_CLI ||
  path.join(pluginRoot, "bin", "autodl-remote");
const configuredLimit = Number.parseInt(
  process.env.AUTODL_REMOTE_MCP_MAX_OUTPUT_BYTES || "65536",
  10,
);
const maxOutputBytes =
  Number.isSafeInteger(configuredLimit) && configuredLimit > 0
    ? configuredLimit
    : 65536;
const activeChildren = new Set();

const projectRootProperty = {
  type: "string",
  description:
    "Absolute path to the local project bound to AutoDL Remote. The CLI runs with this directory as cwd.",
};
const accountProperty = {
  type: "string",
  description: "Optional saved account profile override.",
};
const remoteProperty = {
  type: "string",
  description: "Optional remote project root override.",
};
const stringArray = { type: "array", items: { type: "string" } };

function objectSchema(properties, required = []) {
  return {
    type: "object",
    additionalProperties: false,
    properties,
    ...(required.length ? { required } : {}),
  };
}

function tool(name, description, properties, required = [], annotations = {}) {
  return {
    name,
    description,
    inputSchema: objectSchema(properties, required),
    annotations,
  };
}

const tools = [
  tool(
    "autodl_account",
    "Manage saved AutoDL SSH account profiles. Supports list, show, test, use, and add. Password save/delete are intentionally excluded so credentials never pass through MCP arguments.",
    {
      action: { type: "string", enum: ["list", "show", "test", "use", "add"] },
      name: { type: "string", description: "Account profile name." },
      target: { type: "string", description: "SSH target such as root@gpu.example.com." },
      host: { type: "string" },
      user: { type: "string" },
      port: { type: "integer", minimum: 1, maximum: 65535 },
      key: { type: "string", description: "Local private-key path." },
      auth: { type: "string", enum: ["prompt", "keychain", "ssh-key"] },
      defaultRemote: { type: "string" },
      force: { type: "boolean" },
    },
    ["action"],
  ),
  tool(
    "autodl_bind",
    "Bind a local project directory to a saved account and remote project root.",
    {
      projectRoot: projectRootProperty,
      account: accountProperty,
      remote: { ...remoteProperty, description: "Remote project root to bind." },
      force: { type: "boolean", description: "Overwrite an existing project binding." },
    },
    ["projectRoot", "remote"],
  ),
  tool(
    "autodl_doctor",
    "Diagnose the bound project, local SSH/rsync, remote connectivity, GPU, and tmux state.",
    { projectRoot: projectRootProperty },
    ["projectRoot"],
    { readOnlyHint: true },
  ),
  tool(
    "autodl_model_dir",
    "Show the conventional remote model directory, optionally creating it.",
    {
      projectRoot: projectRootProperty,
      create: { type: "boolean", description: "Create the directory remotely when missing." },
    },
    ["projectRoot"],
  ),
  tool(
    "autodl_file",
    "Inspect remote project files without opening an interactive shell. Supports tree, list, read, and tail; tail is always bounded and non-following.",
    {
      action: { type: "string", enum: ["tree", "list", "read", "tail"] },
      projectRoot: projectRootProperty,
      path: { type: "string", description: "Path relative to the remote project root." },
      depth: { type: "integer", minimum: 0, maximum: 20 },
      limit: { type: "integer", minimum: 1, maximum: 5000 },
      lines: { type: "integer", minimum: 0, maximum: 5000 },
      account: accountProperty,
      remote: remoteProperty,
    },
    ["action", "projectRoot"],
    { readOnlyHint: true },
  ),
  tool(
    "autodl_transfer",
    "Upload or download one project path using the existing rsync/SCP fallback logic. Supports dry runs; upload mirroring requires explicit deletion confirmation.",
    {
      action: { type: "string", enum: ["upload", "download"] },
      projectRoot: projectRootProperty,
      localPath: { type: "string", description: "Path relative to the local project root." },
      remotePath: { type: "string", description: "Path relative to the remote project root." },
      dryRun: { type: "boolean" },
      delete: { type: "boolean", description: "Upload only: delete extraneous remote files." },
      confirmDelete: {
        type: "string",
        description: "When delete is true, must equal delete-remote-extraneous.",
      },
      account: accountProperty,
      remote: remoteProperty,
    },
    ["action", "projectRoot"],
  ),
  tool(
    "autodl_exec",
    "Execute an argv array in the remote project. The argv array is passed without a local shell. Use [\"bash\",\"-lc\",\"...\"] only when shell syntax is required. Dangerous commands stay blocked unless explicitly confirmed.",
    {
      projectRoot: projectRootProperty,
      argv: { ...stringArray, minItems: 1, description: "Remote command as an argv array." },
      mode: { type: "string", enum: ["foreground", "detach", "tmux"] },
      account: accountProperty,
      remote: remoteProperty,
      cwd: { type: "string", description: "Remote cwd relative to the remote project root." },
      name: { type: "string" },
      replace: { type: "boolean" },
      model: { type: "string" },
      tags: stringArray,
      stage: { type: "string" },
      purpose: { type: "string" },
      outputs: stringArray,
      allowDangerous: { type: "boolean" },
      confirmDangerous: {
        type: "string",
        description: "Must equal allow-dangerous when allowDangerous is true.",
      },
    },
    ["projectRoot", "argv"],
  ),
  tool(
    "autodl_job",
    "Inspect or stop detached jobs. Supports list, status, tail, and stop. Tail is bounded and non-following; stop requires exact-name confirmation.",
    {
      action: { type: "string", enum: ["list", "status", "tail", "stop"] },
      projectRoot: projectRootProperty,
      name: { type: "string" },
      lines: { type: "integer", minimum: 0, maximum: 5000 },
      confirm: { type: "string", description: "For stop, must exactly match name." },
    },
    ["action", "projectRoot"],
  ),
  tool(
    "autodl_run",
    "Submit and manage tracked experiment runs. Supports submit, list, status, tail, stop, and note. Submit is detached by default; stop requires exact-name confirmation.",
    {
      action: { type: "string", enum: ["submit", "list", "status", "tail", "stop", "note"] },
      projectRoot: projectRootProperty,
      argv: { ...stringArray, minItems: 1 },
      syncUp: { ...stringArray, description: "Project-relative local paths to upload before submit." },
      tmux: { type: "boolean" },
      account: accountProperty,
      remote: remoteProperty,
      cwd: { type: "string" },
      name: { type: "string" },
      replace: { type: "boolean" },
      model: { type: "string" },
      tags: stringArray,
      stage: { type: "string" },
      purpose: { type: "string" },
      outputs: stringArray,
      lines: { type: "integer", minimum: 0, maximum: 5000 },
      allowDangerous: { type: "boolean" },
      confirmDangerous: { type: "string" },
      confirm: { type: "string", description: "For stop, must exactly match name." },
    },
    ["action", "projectRoot"],
  ),
  tool(
    "autodl_fleet",
    "Create, register, list, and inspect multi-GPU account fleets for a bound project.",
    {
      action: { type: "string", enum: ["create", "add", "list", "status"] },
      projectRoot: projectRootProperty,
      fleet: { type: "string" },
      device: { type: "string" },
      account: accountProperty,
      remote: remoteProperty,
      tags: { type: "string", description: "Comma-separated device tags." },
    },
    ["action", "projectRoot"],
  ),
  tool(
    "autodl_tmux",
    "Check, list, capture, or manage AutoDL Remote tmux sessions. Capture is bounded. Install and kill require explicit confirmation.",
    {
      action: { type: "string", enum: ["check", "list", "capture", "attach_command", "install", "kill"] },
      projectRoot: projectRootProperty,
      session: { type: "string" },
      lines: { type: "integer", minimum: 0, maximum: 5000 },
      account: accountProperty,
      remote: remoteProperty,
      confirm: {
        type: "string",
        description: "For kill, match session; for install, equal install-tmux.",
      },
    },
    ["action", "projectRoot"],
  ),
  tool(
    "autodl_dashboard",
    "Render a one-shot, read-only local HTML dashboard for the project or a fleet. Watching and auto-opening are intentionally excluded from MCP.",
    {
      projectRoot: projectRootProperty,
      fleet: { type: "string" },
      output: { type: "string", description: "Project-relative local output path." },
      lines: { type: "integer", minimum: 0, maximum: 5000 },
    },
    ["projectRoot"],
  ),
  tool(
    "autodl_shutdown",
    "Request shutdown of the remote machine bound to the project. Requires confirm=shutdown and is always treated as destructive.",
    {
      projectRoot: projectRootProperty,
      waitSeconds: { type: "integer", minimum: 0, maximum: 120 },
      confirm: { type: "string", description: "Must equal shutdown." },
    },
    ["projectRoot", "confirm"],
    { destructiveHint: true },
  ),
];

const toolNames = new Set(tools.map(({ name }) => name));

function fail(message) {
  throw Object.assign(new Error(message), { code: -32602 });
}

function requiredString(input, key) {
  const value = input[key];
  if (typeof value !== "string" || value.length === 0) fail(`${key} is required`);
  return value;
}

function optionalString(input, key) {
  const value = input[key];
  if (value === undefined) return undefined;
  if (typeof value !== "string" || value.length === 0) fail(`${key} must be a non-empty string`);
  return value;
}

function stringList(input, key, { required = false } = {}) {
  const value = input[key];
  if (value === undefined) {
    if (required) fail(`${key} is required`);
    return [];
  }
  if (!Array.isArray(value) || value.some((item) => typeof item !== "string" || !item.length)) {
    fail(`${key} must be an array of non-empty strings`);
  }
  if (required && value.length === 0) fail(`${key} must not be empty`);
  return value;
}

function integer(input, key, fallback, min, max) {
  const value = input[key] ?? fallback;
  if (!Number.isSafeInteger(value) || value < min || value > max) {
    fail(`${key} must be an integer from ${min} to ${max}`);
  }
  return value;
}

function projectCwd(input) {
  const value = requiredString(input, "projectRoot");
  if (!path.isAbsolute(value)) fail("projectRoot must be an absolute path");
  try {
    if (!statSync(value).isDirectory()) fail("projectRoot must be a directory");
  } catch (error) {
    if (error.code === -32602) throw error;
    fail(`projectRoot is not accessible: ${value}`);
  }
  return realpathSync(value);
}

function isWithin(root, candidate) {
  const relative = path.relative(root, candidate);
  return (
    relative === "" ||
    (relative !== ".." &&
      !relative.startsWith(`..${path.sep}`) &&
      !path.isAbsolute(relative))
  );
}

function pathEntryExists(value) {
  try {
    lstatSync(value);
    return true;
  } catch {
    return false;
  }
}

function validateLocalProjectPath(value, key, projectRoot) {
  if (path.isAbsolute(value)) fail(`${key} must be project-relative`);
  const resolved = path.resolve(projectRoot, value);
  if (!isWithin(projectRoot, resolved)) fail(`${key} cannot escape projectRoot`);

  let existing = resolved;
  while (!pathEntryExists(existing)) {
    const parent = path.dirname(existing);
    if (parent === existing) break;
    existing = parent;
  }
  let canonicalExisting;
  try {
    canonicalExisting = realpathSync(existing);
  } catch {
    fail(`${key} cannot resolve through a broken symlink inside projectRoot`);
  }
  if (!isWithin(projectRoot, canonicalExisting)) {
    fail(`${key} cannot escape projectRoot through a symlink`);
  }
  return value;
}

function localProjectPath(input, key, projectRoot, { required = false } = {}) {
  const value = required ? requiredString(input, key) : optionalString(input, key);
  return value === undefined
    ? undefined
    : validateLocalProjectPath(value, key, projectRoot);
}

function validateRemoteProjectPath(value, key) {
  if (path.posix.isAbsolute(value) || value.split("/").includes("..")) {
    fail(`${key} must be project-relative and cannot escape projectRoot`);
  }
  return value;
}

function remoteProjectPath(input, key, { required = false } = {}) {
  const value = required ? requiredString(input, key) : optionalString(input, key);
  return value === undefined ? undefined : validateRemoteProjectPath(value, key);
}

function canonicalNameValue(value, key) {
  if (!/^[A-Za-z0-9_.-]+$/.test(value)) {
    fail(`${key} must already be a canonical name using only A-Z, a-z, 0-9, _, ., or -`);
  }
  return value;
}

function canonicalName(input, key, { required = false } = {}) {
  const value = required ? requiredString(input, key) : optionalString(input, key);
  return value === undefined ? undefined : canonicalNameValue(value, key);
}

function addOption(args, flag, value) {
  if (value !== undefined) args.push(flag, value);
}

function addCommonRemoteOptions(args, input) {
  addOption(args, "--account", optionalString(input, "account"));
  addOption(args, "--remote", optionalString(input, "remote"));
}

function addMetadataOptions(args, input, projectRoot) {
  addOption(args, "--cwd", remoteProjectPath(input, "cwd"));
  addOption(args, "--name", canonicalName(input, "name"));
  if (input.replace === true) args.push("--replace");
  addOption(args, "--model", optionalString(input, "model"));
  for (const tag of stringList(input, "tags")) args.push("--tag", tag);
  addOption(args, "--stage", optionalString(input, "stage"));
  addOption(args, "--purpose", optionalString(input, "purpose"));
  for (const output of stringList(input, "outputs")) args.push("--output", output);
  if (input.allowDangerous === true) {
    if (input.confirmDangerous !== "allow-dangerous") {
      fail("allowDangerous requires confirmDangerous=allow-dangerous");
    }
    args.push("--allow-dangerous");
  }
}

function requireNameFor(action, input, actions) {
  return canonicalName(input, "name", { required: actions.includes(action) });
}

function buildAccount(input) {
  const action = requiredString(input, "action");
  if (!["list", "show", "test", "use", "add"].includes(action)) fail(`unsupported account action: ${action}`);
  const args = ["account", action];
  if (action === "list") return { args, cwd: process.cwd() };
  if (action === "test") {
    const name = optionalString(input, "name");
    if (name) args.push(name);
    return { args, cwd: process.cwd() };
  }
  const name = requiredString(input, "name");
  args.push(name);
  if (action !== "add") return { args, cwd: process.cwd() };
  const target = optionalString(input, "target");
  const host = optionalString(input, "host");
  if (!target && !host) fail("account add requires target or host");
  addOption(args, "--target", target);
  addOption(args, "--host", host);
  addOption(args, "--user", optionalString(input, "user"));
  if (input.port !== undefined) args.push("--port", String(integer(input, "port", 22, 1, 65535)));
  addOption(args, "--key", optionalString(input, "key"));
  const auth = optionalString(input, "auth");
  if (auth && !["prompt", "keychain", "ssh-key"].includes(auth)) fail("invalid auth");
  addOption(args, "--auth", auth);
  addOption(args, "--default-remote", optionalString(input, "defaultRemote"));
  if (input.force === true) args.push("--force");
  return { args, cwd: process.cwd() };
}

function buildBind(input) {
  const args = ["bind"];
  addOption(args, "--account", optionalString(input, "account"));
  args.push("--remote", requiredString(input, "remote"));
  if (input.force === true) args.push("--force");
  return { args, cwd: projectCwd(input) };
}

function buildFile(input) {
  const action = requiredString(input, "action");
  const command = { tree: "tree", list: "ls", read: "cat", tail: "tail" }[action];
  if (!command) fail(`unsupported file action: ${action}`);
  const cwd = projectCwd(input);
  const args = [command];
  addCommonRemoteOptions(args, input);
  const filePath = ["read", "tail"].includes(action)
    ? remoteProjectPath(input, "path", { required: true })
    : remoteProjectPath(input, "path") || ".";
  if (action === "tree") {
    if (filePath.startsWith("-")) fail("tree path must not start with '-'");
    if (input.depth !== undefined) args.push("--depth", String(integer(input, "depth", 3, 0, 20)));
    if (input.limit !== undefined) args.push("--limit", String(integer(input, "limit", 500, 1, 5000)));
    args.push(filePath);
  } else {
    if (input.lines !== undefined && ["read", "tail"].includes(action)) {
      args.push("--lines", String(integer(input, "lines", 120, 0, 5000)));
    }
    args.push("--", filePath);
  }
  return { args, cwd };
}

function buildTransfer(input) {
  const action = requiredString(input, "action");
  if (!["upload", "download"].includes(action)) fail(`unsupported transfer action: ${action}`);
  const cwd = projectCwd(input);
  const args = [action === "upload" ? "put" : "get"];
  addCommonRemoteOptions(args, input);
  if (input.dryRun === true) args.push("--dry-run");
  if (input.delete === true) {
    if (action !== "upload") fail("delete is only valid for upload");
    if (input.confirmDelete !== "delete-remote-extraneous") {
      fail("delete requires confirmDelete=delete-remote-extraneous");
    }
    args.push("--delete");
  }
  args.push("--");
  if (action === "upload") {
    args.push(localProjectPath(input, "localPath", cwd, { required: true }));
    const remotePath = remoteProjectPath(input, "remotePath");
    if (remotePath) args.push(remotePath);
  } else {
    args.push(remoteProjectPath(input, "remotePath", { required: true }));
    const localPath = localProjectPath(input, "localPath", cwd);
    if (localPath) args.push(localPath);
  }
  return { args, cwd };
}

function buildExec(input) {
  const cwd = projectCwd(input);
  const args = ["exec"];
  addCommonRemoteOptions(args, input);
  const mode = input.mode || "foreground";
  if (!["foreground", "detach", "tmux"].includes(mode)) fail(`unsupported exec mode: ${mode}`);
  if (mode === "detach") args.push("--detach");
  if (mode === "tmux") args.push("--tmux");
  addMetadataOptions(args, input, cwd);
  args.push("--", ...stringList(input, "argv", { required: true }));
  return { args, cwd };
}

function buildJob(input) {
  const action = requiredString(input, "action");
  if (!["list", "status", "tail", "stop"].includes(action)) fail(`unsupported job action: ${action}`);
  const args = ["job", action];
  const name = requireNameFor(action, input, ["status", "tail", "stop"]);
  if (action === "tail") args.push("--lines", String(integer(input, "lines", 120, 0, 5000)));
  if (action === "stop" && input.confirm !== name) fail("job stop requires confirm to exactly match name");
  if (name) args.push(name);
  return { args, cwd: projectCwd(input) };
}

function buildRun(input) {
  const action = requiredString(input, "action");
  if (!["submit", "list", "status", "tail", "stop", "note"].includes(action)) fail(`unsupported run action: ${action}`);
  const cwd = projectCwd(input);
  const args = ["run", action];
  if (action === "submit") {
    addCommonRemoteOptions(args, input);
    for (const upload of stringList(input, "syncUp")) {
      args.push("--sync-up", validateLocalProjectPath(upload, "syncUp", cwd));
    }
    if (input.tmux === true) args.push("--tmux");
    addMetadataOptions(args, input, cwd);
    args.push("--", ...stringList(input, "argv", { required: true }));
  } else if (action === "list") {
    // no additional arguments
  } else {
    const name = canonicalName(input, "name", { required: true });
    if (action === "tail") args.push("--lines", String(integer(input, "lines", 120, 0, 5000)));
    args.push(name);
    if (action === "stop" && input.confirm !== name) fail("run stop requires confirm to exactly match name");
    if (action === "note") {
      addOption(args, "--model", optionalString(input, "model"));
      for (const tag of stringList(input, "tags")) args.push("--tag", tag);
      addOption(args, "--stage", optionalString(input, "stage"));
      addOption(args, "--purpose", optionalString(input, "purpose"));
      for (const output of stringList(input, "outputs")) args.push("--output", output);
    }
  }
  return { args, cwd };
}

function buildFleet(input) {
  const action = requiredString(input, "action");
  if (!["create", "add", "list", "status"].includes(action)) fail(`unsupported fleet action: ${action}`);
  const args = ["fleet", action];
  if (action === "create") args.push(requiredString(input, "fleet"));
  if (action === "add") {
    args.push(requiredString(input, "fleet"), requiredString(input, "device"));
    addOption(args, "--account", optionalString(input, "account"));
    addOption(args, "--remote", optionalString(input, "remote"));
    addOption(args, "--tags", optionalString(input, "tags"));
  }
  if (action === "status") {
    const fleet = optionalString(input, "fleet");
    if (fleet) args.push(fleet);
  }
  return { args, cwd: projectCwd(input) };
}

function buildTmux(input) {
  const action = requiredString(input, "action");
  const command = {
    check: "check",
    list: "list",
    capture: "capture",
    attach_command: "attach-cmd",
    install: "install",
    kill: "kill",
  }[action];
  if (!command) fail(`unsupported tmux action: ${action}`);
  const args = ["tmux", command];
  addCommonRemoteOptions(args, input);
  if (action === "capture") args.push("--lines", String(integer(input, "lines", 120, 0, 5000)));
  if (["capture", "attach_command", "kill"].includes(action)) {
    const session = canonicalName(input, "session", { required: true });
    if (action === "kill" && input.confirm !== session) fail("tmux kill requires confirm to exactly match session");
    args.push("--", session);
  }
  if (action === "install" && input.confirm !== "install-tmux") {
    fail("tmux install requires confirm=install-tmux");
  }
  return { args, cwd: projectCwd(input) };
}

function buildCommand(name, input) {
  if (!input || typeof input !== "object" || Array.isArray(input)) fail("arguments must be an object");
  switch (name) {
    case "autodl_account": return buildAccount(input);
    case "autodl_bind": return buildBind(input);
    case "autodl_doctor": return { args: ["doctor"], cwd: projectCwd(input) };
    case "autodl_model_dir": return { args: ["model-dir", ...(input.create === true ? ["--mkdir"] : [])], cwd: projectCwd(input) };
    case "autodl_file": return buildFile(input);
    case "autodl_transfer": return buildTransfer(input);
    case "autodl_exec": return buildExec(input);
    case "autodl_job": return buildJob(input);
    case "autodl_run": return buildRun(input);
    case "autodl_fleet": return buildFleet(input);
    case "autodl_tmux": return buildTmux(input);
    case "autodl_dashboard": {
      const cwd = projectCwd(input);
      const args = ["dashboard"];
      addOption(args, "--fleet", optionalString(input, "fleet"));
      addOption(args, "--output", localProjectPath(input, "output", cwd));
      if (input.lines !== undefined) args.push("--lines", String(integer(input, "lines", 120, 0, 5000)));
      return { args, cwd };
    }
    case "autodl_shutdown": {
      if (input.confirm !== "shutdown") fail("shutdown requires confirm=shutdown");
      const args = ["shutdown"];
      if (input.waitSeconds !== undefined) args.push("--wait", String(integer(input, "waitSeconds", 8, 0, 120)));
      return { args, cwd: projectCwd(input) };
    }
    default: fail(`unknown tool: ${name}`);
  }
}

function appendBounded(state, chunk) {
  const buffer = Buffer.isBuffer(chunk) ? chunk : Buffer.from(chunk);
  const available = maxOutputBytes - state.bytes;
  if (available <= 0) {
    state.truncated = true;
    return;
  }
  const kept = buffer.subarray(0, available);
  state.chunks.push(kept);
  state.bytes += kept.length;
  if (kept.length < buffer.length) state.truncated = true;
}

function displayCommand(args) {
  return args
    .map((arg) => (/^[A-Za-z0-9_./:=+-]+$/.test(arg) ? arg : JSON.stringify(arg)))
    .join(" ");
}

function runCli(args, cwd) {
  return new Promise((resolve) => {
    const started = Date.now();
    const stdoutState = { chunks: [], bytes: 0, truncated: false };
    const stderrState = { chunks: [], bytes: 0, truncated: false };
    let settled = false;
    const child = spawn(cliPath, args, {
      cwd,
      env: process.env,
      stdio: ["ignore", "pipe", "pipe"],
    });
    activeChildren.add(child);
    child.stdout.on("data", (chunk) => appendBounded(stdoutState, chunk));
    child.stderr.on("data", (chunk) => appendBounded(stderrState, chunk));

    const finish = (exitCode, spawnError) => {
      if (settled) return;
      settled = true;
      activeChildren.delete(child);
      if (spawnError) appendBounded(stderrState, Buffer.from(spawnError.message));
      resolve({
        ok: exitCode === 0,
        command: displayCommand(args),
        cwd,
        exitCode,
        stdout: Buffer.concat(stdoutState.chunks).toString("utf8"),
        stderr: Buffer.concat(stderrState.chunks).toString("utf8"),
        stdoutTruncated: stdoutState.truncated,
        stderrTruncated: stderrState.truncated,
        durationMs: Date.now() - started,
      });
    };
    child.on("error", (error) => finish(127, error));
    child.on("close", (code) => finish(code ?? 1));
  });
}

async function callTool(name, input) {
  if (!toolNames.has(name)) fail(`unknown tool: ${name}`);
  const { args, cwd } = buildCommand(name, input);
  const payload = await runCli(args, cwd);
  return {
    content: [{ type: "text", text: JSON.stringify(payload) }],
    structuredContent: payload,
    isError: !payload.ok,
  };
}

function send(message) {
  process.stdout.write(`${JSON.stringify(message)}\n`);
}

async function handleRequest(request) {
  switch (request.method) {
    case "initialize":
      return {
        protocolVersion:
          request.params?.protocolVersion === PROTOCOL_VERSION
            ? request.params.protocolVersion
            : PROTOCOL_VERSION,
        capabilities: { tools: { listChanged: false } },
        serverInfo: { name: "autodl-remote", version: SERVER_VERSION },
        instructions:
          "Operate AutoDL projects through the existing autodl-remote CLI. Provide an absolute projectRoot for project tools. Prefer read-only actions before mutations; destructive actions require explicit confirmation.",
      };
    case "ping": return {};
    case "tools/list": return { tools };
    case "tools/call": return callTool(request.params?.name, request.params?.arguments || {});
    default:
      throw Object.assign(new Error(`Method not found: ${request.method}`), { code: -32601 });
  }
}

const input = readline.createInterface({ input: process.stdin });
input.on("line", async (line) => {
  if (!line.trim()) return;
  let request;
  try {
    request = JSON.parse(line);
  } catch (error) {
    send({ jsonrpc: "2.0", id: null, error: { code: -32700, message: error.message } });
    return;
  }
  if (request.id === undefined) return;
  try {
    const result = await handleRequest(request);
    send({ jsonrpc: "2.0", id: request.id, result });
  } catch (error) {
    send({
      jsonrpc: "2.0",
      id: request.id,
      error: { code: error.code || -32603, message: error.message },
    });
  }
});

function shutdown() {
  for (const child of activeChildren) child.kill("SIGTERM");
}

process.stdout.on("error", (error) => {
  shutdown();
  if (error.code !== "EPIPE") process.stderr.write(`${error.stack || error.message}\n`);
  process.exit(error.code === "EPIPE" ? 0 : 1);
});
process.on("SIGINT", () => {
  shutdown();
  process.exit(0);
});
process.on("SIGTERM", () => {
  shutdown();
  process.exit(0);
});
