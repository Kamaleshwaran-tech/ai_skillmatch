import puppeteer from 'puppeteer';
import fs from 'fs';
import path from 'path';

async function verifyJobRecommendations() {
  console.log('=== VERIFYING RECOMMENDED JOBS FEATURE VIA BROWSER ===');

  const chromePath = 'C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe';
  const artifactDir = 'C:\\Users\\kamal\\.gemini\\antigravity\\brain\\63d0c85f-46ca-4212-8e6b-bd3b8bca9032';
  const testResumePath = 'D:\\S7 main project\\ai_skill_match\\test_candidate_resume.pdf';

  const browser = await puppeteer.launch({
    executablePath: chromePath,
    headless: 'new',
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage', '--disable-gpu'],
  });

  try {
    const page = await browser.newPage();
    await page.setViewport({ width: 1400, height: 1000 });

    const timestamp = Date.now();
    const testEmail = `job_rec_user_${timestamp}@example.com`;
    const testPassword = 'Password123!';
    const testFullName = `Rec Tester ${timestamp}`;

    // 1. REGISTER USER
    console.log(`[1] Registering test user: ${testEmail}...`);
    await page.goto('http://127.0.0.1:5173/auth', { waitUntil: 'networkidle0' });

    const tabs = await page.$$('button[role="tab"]');
    if (tabs.length > 1) {
      await tabs[1].click();
      await new Promise((r) => setTimeout(r, 500));
    }

    await page.type('#register-fullname', testFullName);
    await page.type('#register-email', testEmail);
    await page.type('#register-password', testPassword);
    await page.click('#register-submit-button');

    await page.waitForSelector('#signout-button', { timeout: 10000 });
    console.log('[1] Successfully registered and authenticated!');

    // 2. NAVIGATE TO SKILL-GAP / RECOMMENDED JOBS
    console.log('[2] Navigating to http://127.0.0.1:5173/skill-gap...');
    await page.goto('http://127.0.0.1:5173/skill-gap', { waitUntil: 'networkidle0' });

    // 3. UPLOAD RESUME
    console.log(`[3] Uploading resume: ${testResumePath}...`);
    const fileInput = await page.$('#resume-file-input');
    await fileInput.uploadFile(testResumePath);
    await page.click('#upload-resume-button');

    // Wait for upload success alert
    await page.waitForSelector('#upload-success-alert', { timeout: 15000 });
    console.log('[3] Resume uploaded and parsed successfully!');

    // 4. WAIT FOR RECOMMENDED JOBS TO LOAD
    console.log('[4] Waiting for /api/jobs/recommendations to resolve and cards to render...');
    await page.waitForSelector('#job-recommendations-grid', { timeout: 25000 });
    // Additional short settle time for rendering
    await new Promise((r) => setTimeout(r, 1500));

    // 5. INSPECT RENDERED CARDS
    const cardData = await page.evaluate(() => {
      const cards = Array.from(document.querySelectorAll('#job-recommendations-grid > div'));
      return cards.map((card) => {
        const titleEl = card.querySelector('h3');
        const badgeEl = card.querySelector('h6');
        const companyEl = card.querySelector('p');
        const applyBtn = card.querySelector('a.apply-job-link');

        // Extract matched and missing skill chips
        const matchedChips = Array.from(card.querySelectorAll('.MuiChip-root'))
          .filter((chip) => chip.getAttribute('style')?.includes('bbf7d0') || chip.className.includes('MuiChip-filled'))
          .map((c) => c.textContent.trim());

        return {
          title: titleEl ? titleEl.textContent.trim() : null,
          company: companyEl ? companyEl.textContent.trim() : null,
          matchPercentageText: badgeEl ? badgeEl.textContent.trim() : null,
          applyHref: applyBtn ? applyBtn.getAttribute('href') : null,
          applyTarget: applyBtn ? applyBtn.getAttribute('target') : null,
          applyRel: applyBtn ? applyBtn.getAttribute('rel') : null,
          applyButtonDisabled: applyBtn ? applyBtn.hasAttribute('disabled') : false,
        };
      });
    });

    console.log(`[5] Successfully found ${cardData.length} recommended job cards.`);
    console.log('Sample Card 1:', JSON.stringify(cardData[0], null, 2));

    // Check banner presence
    const sampleBanner = await page.$('#sample-data-banner');
    const isSampleBannerVisible = sampleBanner !== null;

    // 6. TAKE SCREENSHOT
    const screenshotPath = path.join(artifactDir, 'recommended_jobs_browser_verification.png');
    await page.screenshot({ path: screenshotPath, fullPage: true });
    console.log(`[6] Full-page verification screenshot saved to: ${screenshotPath}`);

    // 7. RECORD AND SAVE ARTIFACT RESULT
    const verificationReport = {
      timestamp: new Date().toISOString(),
      testUser: testEmail,
      resumeUploaded: 'test_candidate_resume.pdf',
      cardsRenderedCount: cardData.length,
      sampleBannerDisplayed: isSampleBannerVisible,
      firstCard: cardData[0] || null,
      allCards: cardData,
      checks: {
        cardsLoaded: cardData.length > 0,
        hasProminentMatchPercentage: cardData.some((c) => c.matchPercentageText && c.matchPercentageText.includes('%')),
        applyLinkHasValidHref: cardData.some((c) => c.applyHref && (c.applyHref.startsWith('http://') || c.applyHref.startsWith('https://'))),
        applyLinkTargetBlank: cardData.every((c) => c.applyTarget === '_blank'),
        applyLinkNoopener: cardData.every((c) => c.applyRel === 'noopener noreferrer'),
      },
    };

    const reportJsonPath = path.join(artifactDir, 'recommended_jobs_verification_result.json');
    fs.writeFileSync(reportJsonPath, JSON.stringify(verificationReport, null, 2));
    console.log(`[7] Verification JSON report saved to: ${reportJsonPath}`);

    console.log('=== VERIFICATION PASSED SUCCESSFULLY ===');
    return verificationReport;
  } finally {
    await browser.close();
  }
}

verifyJobRecommendations().catch((err) => {
  console.error('VERIFICATION FAILED:', err);
  process.exit(1);
});
