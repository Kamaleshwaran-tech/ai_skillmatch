import puppeteer from 'puppeteer';
import fs from 'fs';
import path from 'path';

async function runFullFlowVerification() {
  console.log('=== STARTING FULL END-TO-END FLOW VERIFICATION ===');
  console.log('Flow: Register -> Upload Resume -> Run Skill Gap Analysis -> View Dashboard & Market Demand');

  const chromePath = 'C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe';
  const artifactDir = 'C:\\Users\\kamal\\.gemini\\antigravity\\brain\\63d0c85f-46ca-4212-8e6b-bd3b8bca9032';

  const browser = await puppeteer.launch({
    executablePath: chromePath,
    headless: 'new',
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage', '--disable-gpu'],
  });

  const recordedSteps = [];

  try {
    const page = await browser.newPage();
    await page.setViewport({ width: 1400, height: 950 });

    const timestamp = Date.now();
    const testEmail = `journey_user_${timestamp}@example.com`;
    const testPassword = 'Password123!';
    const testFullName = `Full Flow Candidate ${timestamp}`;

    // STEP 1: Registration
    console.log(`[Step 1] Navigating to http://127.0.0.1:5173/auth to register user: ${testEmail}...`);
    await page.goto('http://127.0.0.1:5173/auth', { waitUntil: 'networkidle0' });

    // Switch to Register Tab
    const tabs = await page.$$('button[role="tab"]');
    if (tabs.length > 1) {
      await tabs[1].click();
      await new Promise((r) => setTimeout(r, 600));
    }

    await page.type('#register-fullname', testFullName);
    await page.type('#register-email', testEmail);
    await page.type('#register-password', testPassword);
    await page.click('#register-submit-button');

    await page.waitForSelector('#signout-button', { timeout: 10000 });
    console.log('[Step 1 Complete] Registered and authenticated successfully.');
    const step1Shot = path.join(artifactDir, 'flow_step1_auth.png');
    await page.screenshot({ path: step1Shot });
    recordedSteps.push({ step: 1, action: 'Registration & Authentication', screenshot: 'flow_step1_auth.png' });

    // STEP 2: Navigate to Market Demand Page
    console.log('[Step 2] Navigating to Market Demand Analytics page (/market-demand)...');
    await page.goto('http://127.0.0.1:5173/market-demand', { waitUntil: 'networkidle0' });
    await page.waitForSelector('#sample-data-banner', { timeout: 10000 });
    await new Promise((r) => setTimeout(r, 1500)); // Allow Recharts to render bars

    const demandPageText = await page.evaluate(() => document.body.innerText);
    const hasSampleBanner = demandPageText.includes('SAMPLE DATA — not live');
    const hasDenominator = demandPageText.includes('Unique Listings Analyzed');
    console.log(`[Step 2 Details] Sample Banner visible: ${hasSampleBanner}, Denominator shown: ${hasDenominator}`);

    const step2Shot = path.join(artifactDir, 'flow_step2_market_demand.png');
    await page.screenshot({ path: step2Shot, fullPage: true });
    recordedSteps.push({ step: 2, action: 'Market Demand Page with Sample Banner and Recharts', screenshot: 'flow_step2_market_demand.png' });

    // STEP 3: Navigate to Skill Gap Page and Upload Resume
    console.log('[Step 3] Navigating to Skill Gap Analysis page (/skill-gap)...');
    await page.goto('http://127.0.0.1:5173/skill-gap', { waitUntil: 'networkidle0' });

    console.log('[Step 3] Selecting test_candidate_resume.pdf for upload...');
    const pdfPath = path.resolve('..', 'test_candidate_resume.pdf');
    const fileInput = await page.$('#resume-file-input');
    await fileInput.uploadFile(pdfPath);
    await new Promise((r) => setTimeout(r, 600));

    console.log('[Step 3] Clicking Upload & Parse Resume button...');
    await page.click('#upload-resume-button');
    await page.waitForSelector('#upload-success-alert', { timeout: 12000 });
    console.log('[Step 3 Complete] Resume uploaded and parsed successfully.');

    const step3Shot = path.join(artifactDir, 'flow_step3_resume_uploaded.png');
    await page.screenshot({ path: step3Shot });
    recordedSteps.push({ step: 3, action: 'Resume Upload & Skills Extracted', screenshot: 'flow_step3_resume_uploaded.png' });

    // STEP 4: Run Skill Gap Analysis
    console.log('[Step 4] Running Skill Gap Analysis for target role "Developer"...');
    // Set target role
    await page.$eval('#target-role-input', (el) => (el.value = ''));
    await page.type('#target-role-input', 'Developer');
    await page.click('#run-analysis-button');

    console.log('[Step 4] Waiting for analysis results dashboard to render...');
    await page.waitForSelector('#skill-gap-results-panel', { timeout: 25000 });
    await new Promise((r) => setTimeout(r, 2000));

    const analysisPageText = await page.evaluate(() => document.body.innerText);
    const hasMatchedSkills = analysisPageText.includes('Matched Skills');
    const hasMissingSkills = analysisPageText.includes('Missing Competencies');
    const hasEvidence = analysisPageText.includes('Evidence:');
    const hasPriority = analysisPageText.includes('Priority:');
    console.log(`[Step 4 Details] Matched: ${hasMatchedSkills}, Missing: ${hasMissingSkills}, Evidence: ${hasEvidence}, Priority: ${hasPriority}`);

    const step4Shot = path.join(artifactDir, 'flow_step4_skill_gap_dashboard.png');
    await page.screenshot({ path: step4Shot, fullPage: true });
    recordedSteps.push({ step: 4, action: 'Skill Gap Dashboard with Evidence and Priority Badges', screenshot: 'flow_step4_skill_gap_dashboard.png' });

    // Record flow journey summary
    const journeySummary = {
      timestamp: new Date().toISOString(),
      userEmail: testEmail,
      resumeFile: 'test_candidate_resume.pdf',
      targetRole: 'Developer',
      sampleBannerVerified: hasSampleBanner,
      denominatorVerified: hasDenominator,
      matchedSectionVerified: hasMatchedSkills,
      missingSectionVerified: hasMissingSkills,
      evidenceInlineVerified: hasEvidence,
      priorityLabelsVerified: hasPriority,
      recordedSteps,
    };

    const journeyPath = path.join(artifactDir, 'full_flow_walkthrough_recording.json');
    fs.writeFileSync(journeyPath, JSON.stringify(journeySummary, null, 2));
    console.log('=== FULL END-TO-END FLOW RECORDED SUCCESSFULLY ===');
    console.log('Recording summary saved to:', journeyPath);

  } catch (error) {
    console.error('Full flow walkthrough failed:', error);
    process.exit(1);
  } finally {
    await browser.close();
  }
}

runFullFlowVerification();
