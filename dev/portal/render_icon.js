// node render_icon.js <dir> <page> <out.png> <size>
const { chromium } = require('playwright');
(async () => {
  const [dir, page_name, out, size] = process.argv.slice(2);
  const browser = await chromium.launch();
  const scale = Number(size) / 144;
  const page = await browser.newPage({ viewport: { width: 1100, height: 520 }, deviceScaleFactor: page_name === 'preview' ? 1 : scale });
  await page.goto('file://' + dir + '/' + page_name + '.html');
  await page.evaluate(() => document.fonts.ready);
  if (page_name === 'preview') await page.screenshot({ path: out, fullPage: true });
  else await page.locator('svg').first().screenshot({ path: out, omitBackground: true });
  await browser.close();
})();
