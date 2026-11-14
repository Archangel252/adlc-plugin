// Runs a capture spec in headless Chromium. Called by capture.py: node capture.mjs <spec json> <base url> <out dir>
// Prints the path of every file it writes, one per line.
import { createRequire } from "node:module";
import { mkdirSync, renameSync } from "node:fs";
import path from "node:path";

const require = createRequire(path.join(process.env.NODE_PATH, "noop.js"));
const { chromium } = require("playwright");

const [specJson, baseUrl, outDir] = process.argv.slice(2);
const spec = JSON.parse(specJson);
mkdirSync(outDir, { recursive: true });

const browser = await chromium.launch();
const viewport = spec.viewport ?? { width: 1280, height: 800 };
const context = await browser.newContext({
  baseURL: baseUrl,
  viewport,
  ...(spec.video ? { recordVideo: { dir: outDir, size: viewport } } : {}),
});
const page = await context.newPage();
const consoleErrors = [];
page.on("console", (msg) => msg.type() === "error" && consoleErrors.push(msg.text()));

let failed = null;
try {
  for (const [i, step] of spec.steps.entries()) {
    const timeout = step.timeout ?? 15000;
    try {
      if (step.goto !== undefined) await page.goto(step.goto, { timeout, waitUntil: "networkidle" });
      else if (step.click) await page.locator(step.click).first().click({ timeout });
      else if (step.fill) await page.locator(step.fill[0]).first().fill(step.fill[1], { timeout });
      else if (step.press) {
        if (Array.isArray(step.press)) await page.locator(step.press[0]).first().press(step.press[1], { timeout });
        else await page.keyboard.press(step.press);
      } else if (step.hover) await page.locator(step.hover).first().hover({ timeout });
      else if (step.wait_for) await page.locator(step.wait_for).first().waitFor({ timeout });
      else if (step.wait) await page.waitForTimeout(step.wait);
      else if (step.screenshot) {
        const file = path.join(outDir, `${step.screenshot}.png`);
        if (step.selector) await page.locator(step.selector).first().screenshot({ path: file, timeout });
        else await page.screenshot({ path: file, fullPage: !!step.full_page });
        console.log(file);
      } else throw new Error(`unknown step ${JSON.stringify(step)}`);
    } catch (err) {
      failed = `step ${i + 1} ${JSON.stringify(step)}: ${err.message.split("\n")[0]}`;
      const file = path.join(outDir, `failed-step-${i + 1}.png`);
      await page.screenshot({ path: file }).catch(() => {});
      console.log(file);
      break;
    }
  }
} finally {
  const video = page.video();
  await context.close();
  if (video) {
    const file = path.join(outDir, "recording.webm");
    renameSync(await video.path(), file);
    console.log(file);
  }
  await browser.close();
}

if (consoleErrors.length) console.error(`Browser console errors:\n${consoleErrors.slice(0, 10).join("\n")}`);
if (failed) {
  console.error(`Capture failed at ${failed}`);
  process.exit(1);
}
