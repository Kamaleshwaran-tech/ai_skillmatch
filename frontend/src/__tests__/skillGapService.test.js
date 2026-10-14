import { describe, it, expect, vi, beforeEach } from 'vitest';
import apiClient from '../api/client';
import {
  fetchMarketDemand,
  uploadResumeFile,
  fetchActiveResume,
  fetchUserResumes,
  activateResume,
  fetchResumeSkills,
  deleteResumeFile,
  analyzeSkillGap,
  fetchSkillGapAnalysis,
  fetchJobRecommendations,
  fetchLearningRoadmap,
} from '../services/skillGapService';

vi.mock('../api/client', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    delete: vi.fn(),
  },
}));

describe('skillGapService', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('fetchMarketDemand calls /market-demand with params', async () => {
    const mockResponse = { data: { total_listings_analyzed: 10, skills: [] } };
    apiClient.get.mockResolvedValueOnce(mockResponse);

    const result = await fetchMarketDemand({ role: 'Python Developer' });
    expect(apiClient.get).toHaveBeenCalledWith('/market-demand', {
      params: { role: 'Python Developer' },
    });
    expect(result).toEqual(mockResponse.data);
  });

  it('uploadResumeFile posts multipart/form-data to /resumes/upload', async () => {
    const mockResponse = { data: { resume_id: 42, filename: 'test.pdf' } };
    apiClient.post.mockResolvedValueOnce(mockResponse);

    const file = new File(['content'], 'test.pdf', { type: 'application/pdf' });
    const result = await uploadResumeFile(file);
    expect(apiClient.post).toHaveBeenCalledWith('/resumes/upload', expect.any(FormData), {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    expect(result).toEqual(mockResponse.data);
  });

  it('fetchActiveResume calls GET /resumes/active', async () => {
    const mockResponse = {
      data: {
        has_active_resume: true,
        message: 'Active resume loaded',
        resume: { id: 42, filename: 'resume_a.pdf', is_active: true },
      },
    };
    apiClient.get.mockResolvedValueOnce(mockResponse);

    const result = await fetchActiveResume();
    expect(apiClient.get).toHaveBeenCalledWith('/resumes/active');
    expect(result).toEqual(mockResponse.data);
  });

  it('fetchUserResumes calls GET /resumes', async () => {
    const mockResponse = {
      data: {
        total_count: 2,
        resumes: [
          { id: 43, filename: 'resume_b.pdf', is_active: true },
          { id: 42, filename: 'resume_a.pdf', is_active: false },
        ],
      },
    };
    apiClient.get.mockResolvedValueOnce(mockResponse);

    const result = await fetchUserResumes();
    expect(apiClient.get).toHaveBeenCalledWith('/resumes');
    expect(result).toEqual(mockResponse.data);
  });

  it('activateResume calls POST /resumes/{id}/activate', async () => {
    const mockResponse = {
      data: {
        has_active_resume: true,
        resume: { id: 42, filename: 'resume_a.pdf', is_active: true },
      },
    };
    apiClient.post.mockResolvedValueOnce(mockResponse);

    const result = await activateResume(42);
    expect(apiClient.post).toHaveBeenCalledWith('/resumes/42/activate');
    expect(result).toEqual(mockResponse.data);
  });

  it('fetchResumeSkills calls /resumes/{id}/skills', async () => {
    const mockResponse = { data: { skills: [{ canonical_name: 'Python' }] } };
    apiClient.get.mockResolvedValueOnce(mockResponse);

    const result = await fetchResumeSkills(42);
    expect(apiClient.get).toHaveBeenCalledWith('/resumes/42/skills');
    expect(result).toEqual(mockResponse.data);
  });

  it('deleteResumeFile calls DELETE /resumes/{id}', async () => {
    const mockResponse = { data: { message: 'Resume deleted' } };
    apiClient.delete.mockResolvedValueOnce(mockResponse);

    const result = await deleteResumeFile(42);
    expect(apiClient.delete).toHaveBeenCalledWith('/resumes/42');
    expect(result).toEqual(mockResponse.data);
  });

  it('analyzeSkillGap posts payload to /skill-gap/analyze', async () => {
    const payload = { resume_id: 1, target_role: 'Full Stack Engineer' };
    const mockResponse = { data: { analysis_id: 101, matched_skills: [] } };
    apiClient.post.mockResolvedValueOnce(mockResponse);

    const result = await analyzeSkillGap(payload);
    expect(apiClient.post).toHaveBeenCalledWith('/skill-gap/analyze', payload);
    expect(result).toEqual(mockResponse.data);
  });

  it('fetchSkillGapAnalysis calls /skill-gap/{id}', async () => {
    const mockResponse = { data: { analysis_id: 101, target_role: 'Engineer' } };
    apiClient.get.mockResolvedValueOnce(mockResponse);

    const result = await fetchSkillGapAnalysis(101);
    expect(apiClient.get).toHaveBeenCalledWith('/skill-gap/101');
    expect(result).toEqual(mockResponse.data);
  });

  it('fetchJobRecommendations calls /jobs/recommendations with query params', async () => {
    const mockResponse = { data: { resume_id: 1, total_recommended: 2, recommendations: [] } };
    apiClient.get.mockResolvedValueOnce(mockResponse);

    const result = await fetchJobRecommendations({ resume_id: 1, limit: 10 });
    expect(apiClient.get).toHaveBeenCalledWith('/jobs/recommendations', {
      params: { resume_id: 1, limit: 10 },
    });
    expect(result).toEqual(mockResponse.data);
  });

  it('fetchLearningRoadmap calls GET /roadmap with query params', async () => {
    const mockResponse = {
      data: {
        resume_id: 1,
        target_role: 'Developer',
        overall_match_percentage: 50.0,
        roadmap_steps: [],
        matched_skills: [],
      },
    };
    apiClient.get.mockResolvedValueOnce(mockResponse);

    const result = await fetchLearningRoadmap({ resume_id: 1, target_role: 'Developer' });
    expect(apiClient.get).toHaveBeenCalledWith('/roadmap', {
      params: { resume_id: 1, target_role: 'Developer' },
    });
    expect(result).toEqual(mockResponse.data);
  });
});

