import React from 'react';
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import RecommendedJobCard from '../components/RecommendedJobCard';

describe('RecommendedJobCard', () => {
  const sampleJob = {
    job_id: 'sample-123',
    title: 'Senior Full Stack Python Developer',
    company: 'Tech Innovations Inc',
    location: 'San Francisco, CA',
    salary_range: '$140,000 - $180,000',
    posted_date: '2026-10-01T10:00:00Z',
    match_percentage: 85.5,
    matched_skills: ['Python', 'FastAPI', 'Docker'],
    missing_skills: ['Kubernetes', 'AWS'],
    description_snippet: 'Exciting role building distributed microservices and APIs with Python.',
    apply_url: 'https://api.adzuna.com/v1/api/redirect/sample-123?utm_source=skillsync',
  };

  it('renders job title, company, location, and salary', () => {
    render(<RecommendedJobCard job={sampleJob} />);
    expect(screen.getByText('Senior Full Stack Python Developer')).toBeInTheDocument();
    expect(screen.getByText('Tech Innovations Inc')).toBeInTheDocument();
    expect(screen.getByText('San Francisco, CA')).toBeInTheDocument();
    expect(screen.getByText('$140,000 - $180,000')).toBeInTheDocument();
  });

  it('renders match percentage badge prominently', () => {
    render(<RecommendedJobCard job={sampleJob} />);
    expect(screen.getByText('85.5%')).toBeInTheDocument();
    expect(screen.getByText(/^match$/i)).toBeInTheDocument();
  });

  it('renders matched and missing skill chips', () => {
    render(<RecommendedJobCard job={sampleJob} />);
    // Matched
    expect(screen.getByText('Python')).toBeInTheDocument();
    expect(screen.getByText('FastAPI')).toBeInTheDocument();
    expect(screen.getByText('Docker')).toBeInTheDocument();
    // Missing
    expect(screen.getByText('Kubernetes')).toBeInTheDocument();
    expect(screen.getByText('AWS')).toBeInTheDocument();
  });

  it('renders Apply button with target=_blank and rel=noopener noreferrer pointing to apply_url', () => {
    render(<RecommendedJobCard job={sampleJob} />);
    const applyBtn = screen.getByRole('link', { name: /apply on adzuna/i });
    expect(applyBtn).toBeInTheDocument();
    expect(applyBtn).toHaveAttribute('href', sampleJob.apply_url);
    expect(applyBtn).toHaveAttribute('target', '_blank');
    expect(applyBtn).toHaveAttribute('rel', 'noopener noreferrer');
  });

  it('renders unscored job card with N/A badge when match_percentage is null or is_scorable is false', () => {
    const unscoredJob = {
      ...sampleJob,
      job_id: 'unscored-456',
      match_percentage: null,
      is_scorable: false,
    };
    render(<RecommendedJobCard job={unscoredJob} />);
    expect(screen.getByText('N/A')).toBeInTheDocument();
    expect(screen.getByText(/^unscored$/i)).toBeInTheDocument();
  });
});
