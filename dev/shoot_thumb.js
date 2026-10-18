const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 144, height: 144 }, deviceScaleFactor: 1 });
  await page.goto('file://' + __dirname + '/mockups/thumbnail.html');
  await page.evaluate(() => document.fonts.ready);
  await page.locator('.t').screenshot({ path: process.argv[2], omitBackground: true });
  await browser.close();
})();
