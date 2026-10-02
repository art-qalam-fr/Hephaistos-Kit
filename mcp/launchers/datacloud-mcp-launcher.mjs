// Waits for the datacloud extension's named pipe, then execs the MCP proxy.
// Usage: node datacloud-mcp-launcher.mjs <proxy-arg e.g. notebooks-devin>
import { spawn } from "node:child_process";
import { Socket } from "node:net";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import { readdirSync, existsSync } from "node:fs";

const arg = process.argv[2] || "notebooks-devin";
const pipe = `\\\\.\\pipe\\datacloud-mcp-${arg}`;

// Resolve the newest installed datacloud extension dynamically —
// hardcoding the versioned folder breaks on every extension update.
const homedir = process.env.USERPROFILE || process.env.HOME || "";
const roots = [
  join(dirname(fileURLToPath(import.meta.url)), "../extensions"), // .devin
  join(homedir, ".antigravity-ide", "extensions"),
  join(homedir, ".devin", "extensions"),
];
let proxy = "";
for (const extRoot of roots) {
  let versions = [];
  try {
    versions = readdirSync(extRoot)
      .filter((d) => d.startsWith("googlecloudtools.datacloud-"))
      .sort()
      .reverse();
  } catch { /* dossier absent */ }
  for (const v of versions) {
    const p = join(extRoot, v, "mcp_servers/cli/mcp_proxy_bundle.js");
    if (existsSync(p)) { proxy = p; break; }
  }
  if (proxy) break;
}
if (!proxy) {
  console.error("datacloud extension introuvable dans " + roots.join(", "));
  process.exit(1);
}

const waitPipe = () =>
  new Promise((resolve) => {
    const tryOnce = () => {
      const s = new Socket();
      s.on("connect", () => { s.destroy(); resolve(); });
      s.on("error", () => { s.destroy(); setTimeout(tryOnce, 1000); });
      s.connect(pipe);
    };
    tryOnce();
  });

await waitPipe();
const child = spawn(process.execPath, [proxy, arg], { stdio: "inherit" });
child.on("exit", (code) => process.exit(code ?? 0));
