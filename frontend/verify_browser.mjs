import puppeteer from 'puppeteer';
import fs from 'fs';
import path from 'path';

async function runBrowserVerification() {
  console.log('Starting Puppeteer browser verification using system Chrome...');
  const chromePath = 'C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe';

  const browser = await puppeteer.launch({
    executablePath: chromePath,
    headless: 'new',
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage', '--disable-gpu'],
  });

  try {
    const page = await browser.newPage();
    await page.setViewport({ width: 1280, height: 900 });

    const logs = [];
    page.on('console', (msg) => logs.push(`[Console ${msg.type()}]: ${msg.text()}`));
    page.on('pageerror', (err) => logs.push(`[Page Error]: ${err.message}`));

    console.log('Navigating to http://127.0.0.1:5173/auth ...');
    await page.goto('http://127.0.0.1:5173/auth', { waitUntil: 'networkidle0', timeout: 15000 });

    // Ensure we start logged out
    const existingSignOut = await page.$('#signout-button');
    if (existingSignOut) {
      console.log('Clearing existing session...');
      await existingSignOut.click();
      await new Promise((r) => setTimeout(r, 1000));
    }

    console.log('Switching to Register tab...');
    // Click register tab (tab index 1)
    const tabs = await page.$$('button[role="tab"]');
    if (tabs.length > 1) {
      await tabs[1].click();
      await new Promise((r) => setTimeout(r, 800));
    }

    const testTimestamp = Date.now();
    const testEmail = `verified_user_${testTimestamp}@example.com`;
    const testPassword = 'Password123!';
    const testFullName = `Verified User ${testTimestamp}`;

    console.log(`Filling registration form for ${testEmail}...`);
    await page.waitForSelector('#register-fullname', { timeout: 5000 });
    await page.type('#register-fullname', testFullName);
    await page.type('#register-email', testEmail);
    await page.type('#register-password', testPassword);

    console.log('Submitting registration form...');
    await page.click('#register-submit-button');

    // Wait for the UI to update to authenticated card
    console.log('Waiting for authenticated view...');
    await page.waitForSelector('#signout-button', { timeout: 10000 });
    await new Promise((r) => setTimeout(r, 1500));

    // Verify GET /api/auth/me result in UI
    const regPageText = await page.evaluate(() => document.body.innerText);
    console.log('Checking page text for user details after registration...');
    const hasEmailAfterReg = regPageText.includes(testEmail);
    const hasFullNameAfterReg = regPageText.includes(testFullName);
    const hasVerifiedGetMeAfterReg = regPageText.includes('GET /api/auth/me');

    console.log(`Registration & Auth Me verification:
      - Has Email (${testEmail}): ${hasEmailAfterReg}
      - Has Full Name: ${hasFullNameAfterReg}
      - Displays GET /api/auth/me verified: ${hasVerifiedGetMeAfterReg}
    `);

    // Take screenshot of authenticated state
    const artifactDir = 'C:\\Users\\kamal\\.gemini\\antigravity\\brain\\63d0c85f-46ca-4212-8e6b-bd3b8bca9032';
    const screenshotPath = path.join(artifactDir, 'auth_verification_screenshot.png');
    await page.screenshot({ path: screenshotPath, fullPage: true });
    console.log(`Screenshot saved to: ${screenshotPath}`);

    // Now test Log out
    console.log('Testing Sign Out button...');
    await page.click('#signout-button');
    await page.waitForSelector('#login-email', { timeout: 8000 });
    await new Promise((r) => setTimeout(r, 800));

    // Now test Log in
    console.log('Testing Login with registered credentials...');
    await page.type('#login-email', testEmail);
    await page.type('#login-password', testPassword);
    await page.click('#login-submit-button');

    await page.waitForSelector('#signout-button', { timeout: 10000 });
    await new Promise((r) => setTimeout(r, 1500));

    const postLoginText = await page.evaluate(() => document.body.innerText);
    const loginSuccess = postLoginText.includes(testEmail);
    const hasVerifiedGetMeAfterLogin = postLoginText.includes('GET /api/auth/me');

    console.log(`Login verification:
      - Has Email after login: ${loginSuccess}
      - GET /api/auth/me re-verified: ${hasVerifiedGetMeAfterLogin}
    `);

    const result = {
      timestamp: new Date().toISOString(),
      testEmail,
      testFullName,
      registrationSuccess: hasEmailAfterReg && hasVerifiedGetMeAfterReg,
      loginSuccess: loginSuccess && hasVerifiedGetMeAfterLogin,
      screenshotPath,
      consoleLogs: logs,
    };

    const resultPath = path.join(artifactDir, 'auth_browser_verification_result.json');
    fs.writeFileSync(resultPath, JSON.stringify(result, null, 2));
    console.log(`Verification result saved to: ${resultPath}`);

  } catch (error) {
    console.error('Browser verification failed:', error);
    process.exit(1);
  } finally {
    await browser.close();
    console.log('Browser closed.');
  }
}

runBrowserVerification();
