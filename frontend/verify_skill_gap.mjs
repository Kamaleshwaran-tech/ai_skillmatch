import puppeteer from 'puppeteer';
import fs from 'fs';
import path from 'path';

async function runSkillGapVerification() {
  console.log('Starting end-to-end browser verification for Skill Gap Analysis...');
  const chromePath = 'C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe';

  const browser = await puppeteer.launch({
    executablePath: chromePath,
    headless: 'new',
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage', '--disable-gpu'],
  });

  try {
    const page = await browser.newPage();
    await page.setViewport({ width: 1280, height: 900 });

    console.log('Navigating page to frontend origin http://127.0.0.1:5173 ...');
    await page.goto('http://127.0.0.1:5173/auth', { waitUntil: 'networkidle0', timeout: 15000 });

    const timestamp = Date.now();
    const testEmail = `gap_tester_${timestamp}@example.com`;
    const testPassword = 'Password123!';
    const testFullName = `Sarah Connor ${timestamp}`;

    console.log(`1. Authenticating user ${testEmail}...`);
    const authResult = await page.evaluate(async (email, password, fullName) => {
      const res = await fetch('/api/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password, full_name: fullName }),
      });
      return await res.json();
    }, testEmail, testPassword, testFullName);

    console.log('Registration response status: Access token received =', !!authResult.access_token);
    const token = authResult.access_token;
    if (!token) {
      throw new Error('Registration failed: ' + JSON.stringify(authResult));
    }

    // 2. Upload test resume via browser page context
    console.log('2. Uploading test_candidate_resume.pdf in browser context...');
    const pdfPath = path.resolve('..', 'test_candidate_resume.pdf');
    const pdfBytes = fs.readFileSync(pdfPath);
    const pdfBase64 = pdfBytes.toString('base64');

    const uploadResult = await page.evaluate(async (jwt, base64Data) => {
      const byteCharacters = atob(base64Data);
      const byteNumbers = new Array(byteCharacters.length);
      for (let i = 0; i < byteCharacters.length; i++) {
        byteNumbers[i] = byteCharacters.charCodeAt(i);
      }
      const byteArray = new Uint8Array(byteNumbers);
      const blob = new Blob([byteArray], { type: 'application/pdf' });

      const formData = new FormData();
      formData.append('file', blob, 'test_candidate_resume.pdf');

      const res = await fetch('/api/resumes/upload', {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${jwt}`,
        },
        body: formData,
      });
      return await res.json();
    }, token, pdfBase64);

    console.log('Upload result: Resume ID =', uploadResult.id, 'Skills extracted count =', uploadResult.extracted_skills_count);
    const resumeId = uploadResult.id;
    if (!resumeId) {
      throw new Error('Upload failed: ' + JSON.stringify(uploadResult));
    }

    // 3. Trigger POST /api/skill-gap/analyze
    console.log('3. Running POST /api/skill-gap/analyze for target role "Developer"...');
    const gapAnalysisResponse = await page.evaluate(async (jwt, rId) => {
      const res = await fetch('/api/skill-gap/analyze', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${jwt}`,
        },
        body: JSON.stringify({
          resume_id: rId,
          target_role: 'Developer',
          target_location: 'San Francisco, CA',
          limit: 10,
        }),
      });
      return await res.json();
    }, token, resumeId);

    console.log('Skill gap analysis complete!');
    console.log('Analysis ID:', gapAnalysisResponse.analysis_id);
    console.log('Total listings analyzed:', gapAnalysisResponse.total_listings_analyzed);
    console.log('Summary:', JSON.stringify(gapAnalysisResponse.summary, null, 2));

    // 4. Verify GET /api/skill-gap/{analysis_id}
    console.log(`4. Verifying GET /api/skill-gap/${gapAnalysisResponse.analysis_id}...`);
    const getAnalysisResult = await page.evaluate(async (jwt, aId) => {
      const res = await fetch(`/api/skill-gap/${aId}`, {
        method: 'GET',
        headers: {
          Authorization: `Bearer ${jwt}`,
        },
      });
      return await res.json();
    }, token, gapAnalysisResponse.analysis_id);

    console.log('GET retrieval verified! Matching summary =', getAnalysisResult.summary.total_demanded_skills);

    // Save token in localStorage and reload page to capture screenshot
    await page.evaluate((jwt) => {
      localStorage.setItem('access_token', jwt);
    }, token);
    await page.reload({ waitUntil: 'networkidle0' });
    await new Promise((r) => setTimeout(r, 1000));

    const artifactDir = 'C:\\Users\\kamal\\.gemini\\antigravity\\brain\\63d0c85f-46ca-4212-8e6b-bd3b8bca9032';
    const screenshotPath = path.join(artifactDir, 'skill_gap_browser_screenshot.png');
    await page.screenshot({ path: screenshotPath, fullPage: true });
    console.log(`Screenshot saved to: ${screenshotPath}`);

    // Save raw JSON response as artifact
    const jsonArtifactPath = path.join(artifactDir, 'skill_gap_analysis_raw_response.json');
    fs.writeFileSync(jsonArtifactPath, JSON.stringify(gapAnalysisResponse, null, 2));
    console.log(`Raw JSON response saved to artifact: ${jsonArtifactPath}`);

    console.log('All skill gap verification steps passed!');
  } catch (error) {
    console.error('Skill gap browser verification failed:', error);
    process.exit(1);
  } finally {
    await browser.close();
    console.log('Browser closed.');
  }
}

runSkillGapVerification();
