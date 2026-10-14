import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import LearningRoadmapView from '../components/LearningRoadmapView';

describe('LearningRoadmapView', () => {
  const sampleRoadmap = {
    resume_id: 1,
    target_role: 'Backend Developer',
    target_location: 'San Francisco, CA',
    overall_match_percentage: 40.0,
    total_listings_analyzed: 15,
    data_source: 'Adzuna Live API',
    is_sample_data: false,
    priority_thresholds: {
      note: 'Project-defined priority thresholds, not industry standards',
    },
    resource_disclaimer:
      'Resource suggestions are general learning categories and platforms, not a specific verified course list.',
    matched_skills: [
      { skill: 'Python', demand_percentage: 80.0 },
      { skill: 'Git', demand_percentage: 60.0 },
    ],
    roadmap_steps: [
      {
        step_number: 1,
        skill: 'Docker',
        canonical_name: 'Docker',
        status: 'missing',
        demand_percentage: 73.33,
        matching_listings_count: 11,
        total_listings_analyzed: 15,
        priority: 'High',
        ai_explanation_available: true,
        explanation: 'Containerization platform for packaging microservices.',
        resource_suggestions: [
          'Official Docker documentation',
          'Interactive courses on freeCodeCamp',
        ],
        practice_project_idea: 'Containerize a FastAPI app with PostgreSQL.',
      },
      {
        step_number: 2,
        skill: 'Kubernetes',
        canonical_name: 'Kubernetes',
        status: 'needs_review',
        demand_percentage: 46.67,
        matching_listings_count: 7,
        total_listings_analyzed: 15,
        priority: 'Medium',
        ai_explanation_available: false,
        explanation: 'AI explanation unavailable',
        resource_suggestions: [],
        practice_project_idea: null,
      },
    ],
  };

  it('renders overall match %, matched skill chips, ordered steps, and AI fallback notice', () => {
    render(
      <LearningRoadmapView
        targetRole="Backend Developer"
        setTargetRole={vi.fn()}
        targetLocation="San Francisco, CA"
        setTargetLocation={vi.fn()}
        onGenerateRoadmap={vi.fn()}
        roadmapStatus="success"
        roadmapError=""
        roadmapResult={sampleRoadmap}
      />
    );

    expect(screen.getByText(/Competency Match: 40%/i)).toBeInTheDocument();
    expect(screen.getByText(/Python \(80%\)/i)).toBeInTheDocument();
    expect(screen.getByText(/Git \(60%\)/i)).toBeInTheDocument();

    expect(screen.getByText(/Step 1: Docker/i)).toBeInTheDocument();
    expect(screen.getByText(/Containerization platform for packaging microservices/i)).toBeInTheDocument();
    expect(screen.getByText(/Official Docker documentation/i)).toBeInTheDocument();

    expect(screen.getByText(/Step 2: Kubernetes/i)).toBeInTheDocument();
    expect(screen.getByTestId('ai-explanation-unavailable-alert')).toBeInTheDocument();
    expect(screen.getByText(/AI explanation unavailable/i)).toBeInTheDocument();
  });

  it('renders positive fully matched state when roadmap_steps is empty', () => {
    render(
      <LearningRoadmapView
        targetRole="Python Developer"
        setTargetRole={vi.fn()}
        targetLocation=""
        setTargetLocation={vi.fn()}
        onGenerateRoadmap={vi.fn()}
        roadmapStatus="success"
        roadmapError=""
        roadmapResult={{
          ...sampleRoadmap,
          target_role: 'Python Developer',
          overall_match_percentage: 100.0,
          roadmap_steps: [],
        }}
      />
    );

    expect(screen.getByText(/You're Fully Matched for "Python Developer"!/i)).toBeInTheDocument();
  });

  it('renders contextual progress indicator while loading', () => {
    render(
      <LearningRoadmapView
        targetRole="Backend Developer"
        setTargetRole={vi.fn()}
        targetLocation=""
        setTargetLocation={vi.fn()}
        onGenerateRoadmap={vi.fn()}
        roadmapStatus="loading"
        roadmapError=""
        roadmapResult={null}
      />
    );

    expect(
      screen.getByText(/Building Your Personalized Learning Roadmap for "Backend Developer"/i)
    ).toBeInTheDocument();
  });
});
