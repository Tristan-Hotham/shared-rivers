// QA: open index.html at 1280 px and 390 px, collect console errors, take screenshots, try a few interactions.
// Usage: node code/qa.js http://localhost:PORT/ (serve the study folder first)
const { chromium } = require("playwright");
const path = require("path");
const url = process.argv[2] || "http://localhost:8765/";
const out = path.join(__dirname, "..", "qa");
(async () => {
  const browser = await chromium.launch();
  for (const [name, w, h] of [["desktop", 1280, 900], ["phone", 390, 844]]) {
    const page = await browser.newPage({ viewport: { width: w, height: h }, deviceScaleFactor: 1 });
    const errs = [];
    page.on("console", m => { if (m.type() === "error" && !m.text().includes("ERR_FAILED")) errs.push(m.text()); });   // ERR_FAILED: tiles and fonts blocked in the container
    page.on("pageerror", e => errs.push("pageerror: " + e.message));
    await page.route(/arcgisonline|googleapis|gstatic/, r => r.abort());   // no outside network in the container
    const LL = "/tmp/claude-0/-home-claude/9791f396-0812-550b-8fd1-2ad33918f115/scratchpad/npm/node_modules/leaflet/dist/";
    await page.route(/cdnjs.*leaflet\.min\.js/, r => r.fulfill({ path: LL + "leaflet.js", contentType: "application/javascript" }));
    await page.route(/cdnjs.*leaflet\.min\.css/, r => r.fulfill({ path: LL + "leaflet.css", contentType: "text/css" }));
    await page.goto(url, { waitUntil: "load" });
    await page.waitForTimeout(4000);
    await page.screenshot({ path: `${out}/${name}_top.png` });
    const atlas = await page.$("#atlas");
    await atlas.scrollIntoViewIfNeeded();
    await page.waitForTimeout(800);
    await atlas.screenshot({ path: `${out}/${name}_map.png` });
    // zoom to the Danube and open its panel
    await page.click("#focusRow >> text=Danube");
    await page.waitForTimeout(1500);
    await atlas.screenshot({ path: `${out}/${name}_danube.png` });
    // search for a river
    await page.fill("#q", "Mekong");
    await page.waitForTimeout(300);
    const sug = await page.$$eval("#sug li", ls => ls.map(l => l.textContent));
    await page.press("#q", "Enter");
    await page.waitForTimeout(1500);
    await atlas.screenshot({ path: `${out}/${name}_mekong.png` });
    // dependency view
    await page.click("#viewTabs >> text=Water from abroad");
    await page.waitForTimeout(800);
    await page.click("#focusRow >> text=World");
    await page.waitForTimeout(1200);
    await atlas.screenshot({ path: `${out}/${name}_dep.png` });
    // layers panel
    await page.click(".lyrBtn");
    await page.waitForTimeout(300);
    await atlas.screenshot({ path: `${out}/${name}_layers.png` });
    await page.click(".lyrBtn");
    // full screen button present?
    const fs = await page.$$eval(".mfs-btn", b => b.length);
    // charts
    for (const id of ["shareChart", "lenChart", "scaleChart", "depChart"]) {
      const e = await page.$("#" + id); await e.scrollIntoViewIfNeeded(); await page.waitForTimeout(200);
      await e.screenshot({ path: `${out}/${name}_${id}.png` });
    }
    await page.screenshot({ path: `${out}/${name}_full.png`, fullPage: true });
    const sw = await page.evaluate(() => [document.documentElement.scrollWidth, innerWidth]);
    console.log(name, "errors:", JSON.stringify(errs), "suggest:", JSON.stringify(sug.slice(0, 4)), "fullscreen buttons:", fs, "scrollWidth/innerWidth:", sw);
    await page.close();
  }
  await browser.close();
})();
