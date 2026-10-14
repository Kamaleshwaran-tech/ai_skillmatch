import React from 'react';
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import SampleDataBanner from '../components/SampleDataBanner';

describe('SampleDataBanner', () => {
  it('renders the sample data banner when isSampleData is true', () => {
    render(<SampleDataBanner isSampleData={true} message="Custom sample message" />);
    expect(screen.getByText(/Custom sample message/i)).toBeInTheDocument();
  });

  it('renders default message when isSampleData is true and no message is provided', () => {
    render(<SampleDataBanner isSampleData={true} />);
    expect(screen.getByText(/SAMPLE DATA — not live/i)).toBeInTheDocument();
  });

  it('renders nothing when isSampleData is false', () => {
    const { container } = render(<SampleDataBanner isSampleData={false} />);
    expect(container).toBeEmptyDOMElement();
  });
});
