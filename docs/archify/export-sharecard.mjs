// Quick share-card export using the Archify viewer
import { chromium } from 'playwright';

const html = 'file:///Users/leandrolima/conductor/workspaces/games/irvine/docs/archify/gamehub-runtime.architecture.html';
const out = '/Users/leandrolima/conductor/workspaces/games/irvine/docs/archify/gamehub-runtime-sharecard.png';

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1200, height: 630 } });
await page.goto(html, { waitUntil: 'networkidle' });
await page.waitForTimeout(500); // let animation settle
await page.screenshot({ path: out, fullPage: false, clip: { x: 0, y: 0, width: 1200, height: 630 } });
await browser.close();
console.log('Share card written to', out);
