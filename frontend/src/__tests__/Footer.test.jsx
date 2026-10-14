import React from 'react';
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import Footer from '../components/Footer';

describe('Footer Component', () => {
  it('renders copyright and brand name', () => {
    render(<Footer />);
    expect(screen.getByText(/SkillSync AI/i)).toBeInTheDocument();
    expect(screen.getByText(/Intelligent Skill Gap Analyzer/i)).toBeInTheDocument();
  });
});
