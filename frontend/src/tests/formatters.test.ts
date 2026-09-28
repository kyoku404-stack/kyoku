import { describe, it, expect } from 'vitest';
import { formatBytes, formatStatusLabel } from '@/utils/formatters';

describe('Formatters Utility', () => {
  it('correctly formats bytes into human-readable strings', () => {
    expect(formatBytes(0)).toBe('0 Bytes');
    expect(formatBytes(1024)).toBe('1 KB');
    expect(formatBytes(1048576)).toBe('1 MB');
    expect(formatBytes(1073741824)).toBe('1 GB');
  });

  it('correctly formats status labels', () => {
    expect(formatStatusLabel('pending')).toBe('Pending');
    expect(formatStatusLabel('PROCESSING')).toBe('Processing');
    expect(formatStatusLabel('PROCESSED')).toBe('Processed');
    expect(formatStatusLabel('FAILED')).toBe('Failed');
  });
});
