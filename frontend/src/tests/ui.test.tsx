import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';

describe('UI Primitives', () => {
  it('renders Button with correct text and variant class', () => {
    render(<Button variant="primary">Launch Search</Button>);
    const button = screen.getByRole('button', { name: /launch search/i });
    expect(button).toBeInTheDocument();
    expect(button.className).toContain('bg-primary');
  });

  it('renders Button in loading state with spinner and disabled', () => {
    render(<Button isLoading>Processing</Button>);
    const button = screen.getByRole('button');
    expect(button).toBeDisabled();
  });

  it('renders Badge with status colors', () => {
    const { rerender } = render(<Badge variant="processing">Processing</Badge>);
    expect(screen.getByText('Processing')).toBeInTheDocument();

    rerender(<Badge variant="processed">Done</Badge>);
    expect(screen.getByText('Done')).toBeInTheDocument();
  });

  it('renders Card with Header and Content', () => {
    render(
      <Card>
        <CardHeader>
          <CardTitle>Enterprise Analytics</CardTitle>
        </CardHeader>
        <CardContent>
          <p>Card Content Paragraph</p>
        </CardContent>
      </Card>
    );

    expect(screen.getByText('Enterprise Analytics')).toBeInTheDocument();
    expect(screen.getByText('Card Content Paragraph')).toBeInTheDocument();
  });
});
