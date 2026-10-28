import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

const html = readFileSync(new URL("../apps/local-controller/waiting-display.html", import.meta.url), "utf8");
const script = readFileSync(new URL("../apps/local-controller/waiting-display.js", import.meta.url), "utf8");

assert.match(html, /id="currentNumber"/);
assert.doesNotMatch(html, /姓名|健保|病歷|電話/);
assert.match(script, /BroadcastChannel\("ye-neuro-queue"\)/);
assert.match(script, /state\.items\.find/);

console.log("Waiting display privacy and synchronization checks passed.");
