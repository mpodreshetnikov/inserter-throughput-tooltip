const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1236, height: 800 }, deviceScaleFactor: 1.5 });
  for (const name of process.argv.slice(2)) {
    await page.goto('file://' + __dirname + '/mockups/' + name + '.html');
    await page.evaluate(() => document.fonts.ready);
    await page.screenshot({ path: __dirname + '/mockups/' + name + '.png', fullPage: true });
  }
  await browser.close();
})();
