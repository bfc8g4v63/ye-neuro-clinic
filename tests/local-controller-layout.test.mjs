import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

const css = readFileSync(new URL("../apps/local-controller/styles.css", import.meta.url), "utf8");

function rule(selector) {
  const match = css.match(new RegExp(`${selector.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}\\s*\\{([\\s\\S]*?)\\}`));
  assert.ok(match, `Missing CSS rule for ${selector}`);
  return match[1];
}

const actions = rule(".action, .secondary, .text-button, .display-button");
assert.match(actions, /display:\s*inline-flex/);
assert.match(actions, /align-items:\s*center/);
assert.match(actions, /justify-content:\s*center/);
assert.match(actions, /text-align:\s*center/);
assert.match(actions, /min-height:\s*58px/);

const mobile = css.match(/@media \(max-width: 480px\)\s*\{([\s\S]*?)\n\}/);
assert.ok(mobile, "Missing mobile breakpoint");
assert.match(mobile[1], /\.control-grid, \.queues \{ grid-template-columns: 1fr;/);

console.log("Local controller CTA alignment regression checks passed.");
