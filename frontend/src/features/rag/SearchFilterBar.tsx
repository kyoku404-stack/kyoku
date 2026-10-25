/**
 * KEEP Enterprise Platform — SearchFilterBar Component (Phase 2.2).
 *
 * Configurable hybrid retrieval weights, candidate limits (top_k),
 * and retrieval mode presets for precision engineering of RAG answers.
 *
 * Specification: devdocs/p2/p2.2.txt Chapter 5 & docs/decisions/decisions.md ADR-035
 * Author: Member 3 (Frontend Lead)
 */

import React from 'react';
import { Sliders, RotateCcw, Sparkles, Hash, Scale } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface SearchFilterBarProps {
  hybridDenseWeight: number;
  setHybridDenseWeight: (val: number) => void;
  hybridSparseWeight: number;
  setHybridSparseWeight: (val: number) => void;
  topK: number;
  setTopK: (val: number) => void;
}

export const SearchFilterBar: React.FC<SearchFilterBarProps> = ({
  hybridDenseWeight,
  setHybridDenseWeight,
  hybridSparseWeight,
  setHybridSparseWeight,
  topK,
  setTopK,
}) => {
  const setPreset = (dense: number, sparse: number, k: number) => {
    setHybridDenseWeight(dense);
    setHybridSparseWeight(sparse);
    setTopK(k);
  };

  const handleDenseChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const dense = parseFloat(e.target.value);
    setHybridDenseWeight(dense);
    // Complementary sparse weight to keep total normalized near 1.0
    setHybridSparseWeight(parseFloat((1.0 - dense).toFixed(2)));
  };

  const resetDefaults = () => {
    setPreset(0.65, 0.35, 5);
  };

  return (
    <div
      className="flex flex-wrap items-center justify-between gap-4 rounded-xl border border-border bg-card/60 p-3.5 backdrop-blur-sm"
      data-testid="rag-search-filter-bar"
    >
      <div className="flex flex-wrap items-center gap-6">
        {/* Title / Icon */}
        <div className="flex items-center gap-2 text-sm font-semibold text-foreground">
          <Sliders className="h-4 w-4 text-primary" />
          <span>Retrieval Engine Parameters</span>
        </div>

        {/* Dense Weight Slider */}
        <div className="flex items-center gap-2.5">
          <label
            htmlFor="dense-slider"
            className="flex items-center gap-1 text-xs font-medium text-muted-foreground whitespace-nowrap"
          >
            <Sparkles className="h-3.5 w-3.5 text-purple-400" />
            Dense (Semantic):
          </label>
          <input
            id="dense-slider"
            type="range"
            min="0"
            max="1"
            step="0.05"
            value={hybridDenseWeight}
            onChange={handleDenseChange}
            className="h-1.5 w-24 cursor-pointer accent-purple-500 rounded-lg bg-muted"
            data-testid="slider-dense-weight"
          />
          <span className="font-mono text-xs font-semibold text-foreground w-8">
            {hybridDenseWeight.toFixed(2)}
          </span>
        </div>

        {/* Sparse Weight Display */}
        <div className="flex items-center gap-2.5">
          <label className="flex items-center gap-1 text-xs font-medium text-muted-foreground whitespace-nowrap">
            <Hash className="h-3.5 w-3.5 text-blue-400" />
            Sparse (Lexical):
          </label>
          <span className="font-mono text-xs font-semibold text-foreground w-8">
            {hybridSparseWeight.toFixed(2)}
          </span>
        </div>

        {/* Top-K Selector */}
        <div className="flex items-center gap-2">
          <label
            htmlFor="top-k-select"
            className="flex items-center gap-1 text-xs font-medium text-muted-foreground whitespace-nowrap"
          >
            <Scale className="h-3.5 w-3.5 text-amber-400" />
            Top-K Passages:
          </label>
          <select
            id="top-k-select"
            value={topK}
            onChange={(e) => setTopK(parseInt(e.target.value, 10))}
            className="h-8 rounded-md border border-border bg-background px-2.5 text-xs font-medium text-foreground focus:outline-none focus:ring-1 focus:ring-primary"
            data-testid="select-top-k"
          >
            <option value="3">3 chunks</option>
            <option value="5">5 chunks (default)</option>
            <option value="8">8 chunks</option>
            <option value="12">12 chunks (deep)</option>
          </select>
        </div>
      </div>

      {/* Preset & Reset Buttons */}
      <div className="flex items-center gap-2">
        <button
          type="button"
          onClick={() => setPreset(0.65, 0.35, 5)}
          className={`px-2.5 py-1 text-xs font-medium rounded-md transition-colors ${
            hybridDenseWeight === 0.65 && hybridSparseWeight === 0.35
              ? 'bg-primary/20 text-primary border border-primary/30'
              : 'bg-muted/50 text-muted-foreground hover:bg-muted hover:text-foreground'
          }`}
          data-testid="preset-balanced"
        >
          Balanced (RRF)
        </button>

        <button
          type="button"
          onClick={() => setPreset(0.85, 0.15, 5)}
          className={`px-2.5 py-1 text-xs font-medium rounded-md transition-colors ${
            hybridDenseWeight === 0.85 && hybridSparseWeight === 0.15
              ? 'bg-primary/20 text-primary border border-primary/30'
              : 'bg-muted/50 text-muted-foreground hover:bg-muted hover:text-foreground'
          }`}
          data-testid="preset-semantic"
        >
          Semantic Focus
        </button>

        <button
          type="button"
          onClick={() => setPreset(0.20, 0.80, 5)}
          className={`px-2.5 py-1 text-xs font-medium rounded-md transition-colors ${
            hybridDenseWeight === 0.20 && hybridSparseWeight === 0.80
              ? 'bg-primary/20 text-primary border border-primary/30'
              : 'bg-muted/50 text-muted-foreground hover:bg-muted hover:text-foreground'
          }`}
          data-testid="preset-keyword"
        >
          Exact Keyword
        </button>

        <Button
          type="button"
          variant="ghost"
          size="sm"
          onClick={resetDefaults}
          title="Reset to defaults"
          className="h-7 px-2 text-xs text-muted-foreground hover:text-foreground"
          data-testid="btn-reset-filters"
        >
          <RotateCcw className="h-3 w-3 mr-1" />
          Reset
        </Button>
      </div>
    </div>
  );
};
