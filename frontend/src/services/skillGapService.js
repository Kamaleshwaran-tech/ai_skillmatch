import apiClient from '../api/client';

/**
 * Fetch market demand data from GET /api/market-demand.
 * @param {Object} params { role, location, limit }
 */
export const fetchMarketDemand = async (params = {}) => {
  const response = await apiClient.get('/market-demand', { params });
  return response.data;
};

/**
 * Upload resume file via POST /api/resumes/upload.
 * @param {File} file
 */
export const uploadResumeFile = async (file) => {
  const formData = new FormData();
  formData.append('file', file);
  const response = await apiClient.post('/resumes/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};

/**
 * Fetch the user's current active resume (and latest analysis) from GET /api/resumes/active.
 */
export const fetchActiveResume = async () => {
  const response = await apiClient.get('/resumes/active');
  return response.data;
};

/**
 * Fetch all of a user's resumes (active + past history) from GET /api/resumes.
 */
export const fetchUserResumes = async () => {
  const response = await apiClient.get('/resumes');
  return response.data;
};

/**
 * Set a specific resume from history as the active resume via POST /api/resumes/{id}/activate.
 * @param {number} resumeId
 */
export const activateResume = async (resumeId) => {
  const response = await apiClient.post(`/resumes/${resumeId}/activate`);
  return response.data;
};

/**
 * Fetch skills for a specific resume from GET /api/resumes/{id}/skills.
 * @param {number} resumeId
 */
export const fetchResumeSkills = async (resumeId) => {
  const response = await apiClient.get(`/resumes/${resumeId}/skills`);
  return response.data;
};

/**
 * Delete resume from DELETE /api/resumes/{id}.
 * @param {number} resumeId
 */
export const deleteResumeFile = async (resumeId) => {
  const response = await apiClient.delete(`/resumes/${resumeId}`);
  return response.data;
};

/**
 * Run skill gap analysis via POST /api/skill-gap/analyze.
 * @param {Object} payload { resume_id, target_role, target_location, limit }
 */
export const analyzeSkillGap = async (payload) => {
  const response = await apiClient.post('/skill-gap/analyze', payload);
  return response.data;
};

/**
 * Retrieve persisted skill gap analysis from GET /api/skill-gap/{id}.
 * @param {number} analysisId
 */
export const fetchSkillGapAnalysis = async (analysisId) => {
  const response = await apiClient.get(`/skill-gap/${analysisId}`);
  return response.data;
};

/**
 * Fetch personalized job recommendations for a resume from GET /api/jobs/recommendations.
 * @param {Object} params { resume_id, location, limit, min_match }
 */
export const fetchJobRecommendations = async (params = {}) => {
  const response = await apiClient.get('/jobs/recommendations', { params });
  return response.data;
};

/**
 * Fetch deterministic, market-driven learning roadmap from GET /api/roadmap.
 * @param {Object} params { resume_id, target_role, target_location, limit }
 */
export const fetchLearningRoadmap = async (params = {}) => {
  const response = await apiClient.get('/roadmap', { params });
  return response.data;
};


