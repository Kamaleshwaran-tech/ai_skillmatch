import puppeteer from 'puppeteer';
import fs from 'fs';
import path from 'path';

async function runGapsVerification() {
  console.log('Running analysis on candidate with realistic skill gaps...');
  const chromePath = 'C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe';

  const browser = await puppeteer.launch({
    executablePath: chromePath,
    headless: 'new',
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage', '--disable-gpu'],
  });

  try {
    const page = await browser.newPage();
    await page.setViewport({ width: 1280, height: 900 });

    await page.goto('http://127.0.0.1:5173/auth', { waitUntil: 'networkidle0' });

    const timestamp = Date.now();
    const testEmail = `gaps_tester_${timestamp}@example.com`;
    const testPassword = 'Password123!';
    const testFullName = `Gaps Candidate ${timestamp}`;

    const authResult = await page.evaluate(async (email, password, fullName) => {
      const res = await fetch('/api/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password, full_name: fullName }),
      });
      return await res.json();
    }, testEmail, testPassword, testFullName);

    const token = authResult.access_token;

    // Upload gaps resume
    const pdfPath = path.resolve('..', 'test_candidate_gaps_resume.pdf');
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
      formData.append('file', blob, 'test_candidate_gaps_resume.pdf');

      const res = await fetch('/api/resumes/upload', {
        method: 'POST',
        headers: { Authorization: `Bearer ${jwt}` },
        body: formData,
      });
      return await res.json();
    }, token, pdfBase64);

    const resumeId = uploadResult.id;

    // Trigger analysis across all available sample jobs (role="")
    const gapAnalysisResponse = await page.evaluate(async (jwt, rId) => {
      const res = await fetch('/api/skill-gap/analyze', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${jwt}`,
        },
        body: JSON.stringify({
          resume_id: rId,
          target_role: "", // analyzes entire job market
          target_location: "",
          limit: 20,
        }),
      });
      return await res.json();
    }, token, resumeId);

    console.log('Skill Gap Analysis Result for Gaps Candidate:');
    console.log('Total listings analyzed:', gapAnalysisResponse.total_listings_analyzed);
    console.log('Matched skills count:', gapAnalysisResponse.matched_skills.length);
    console.log('Missing skills count:', gapAnalysisResponse.missing_skills.length);
    console.log('Needs review count:', gapAnalysisResponse.needs_review_skills.length);
    console.log('Summary:', JSON.stringify(gapAnalysisResponse.summary, null, 2));

    const artifactDir = 'C:\\Users\\kamal\\.gemini\\antigravity\\brain\\63d0c85f-46ca-4212-8e6b-bd3b8bca9032';
    const jsonArtifactPath = path.join(artifactDir, 'skill_gap_analysis_raw_response.json');
    fs.writeFileSync(jsonArtifactPath, JSON.stringify(gapAnalysisResponse, null, 2));
    console.log(`Updated raw JSON response artifact: ${jsonArtifactPath}`);

  } finally {
    await browser.close();
  }
}

runGapsVerification();
