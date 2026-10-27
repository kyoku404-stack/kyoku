/**
 * KEEP Enterprise Platform — GraphFilterBar Component (Phase 2.4).
 *
 * Provides real-time filtering, entity-type toggles, graph build triggers,
 * and text extraction inputs.
 *
 * Specification: docs/API/api-contract.md Section 11 & devdocs/p2/p2.4.txt
 * Author: Member 3 (Frontend Lead)
 */

import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  Search,
  RefreshCw,
  PlusCircle,
  Cpu,
} from 'lucide-react';
import { EntityType } from '@/types/graph';
import type { GraphFilterState } from '@/types/graph';

interface GraphFilterBarProps {
  filters: GraphFilterState;
  onFilterChange: (filters: GraphFilterState) => void;
  onRefresh: () => void;
  onTriggerBuild: (rebuildAll: boolean) => void;
  onTriggerUpdate: (textContent: string) => void;
  isBuilding?: boolean;
}

export const GraphFilterBar: React.FC<GraphFilterBarProps> = ({
  filters,
  onFilterChange,
  onRefresh,
  onTriggerBuild,
  onTriggerUpdate,
  isBuilding = false,
}) => {
  const [showIngestInput, setShowIngestInput] = useState(false);
  const [inputText, setInputText] = useState('');

  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    onFilterChange({
      ...filters,
      searchQuery: e.target.value,
    });
  };

  const handleTypeChange = (typeVal: string) => {
    onFilterChange({
      ...filters,
      selectedEntityType: typeVal,
    });
  };

  const submitTextUpdate = (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputText.trim()) return;
    onTriggerUpdate(inputText.trim());
    setInputText('');
    setShowIngestInput(false);
  };

  return (
    <div className="flex flex-col gap-3 rounded-xl border border-border bg-card p-3 shadow-xs">
      <div className="flex flex-wrap items-center justify-between gap-3">
        {/* Search Input */}
        <div className="relative flex-1 min-w-[240px]">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search entity node by name..."
            value={filters.searchQuery}
            onChange={handleSearchChange}
            className="pl-9 h-9 text-sm"
            data-testid="graph-search-input"
          />
        </div>

        {/* Entity Type Filter */}
        <div className="w-[180px]">
          <select
            value={filters.selectedEntityType}
            onChange={(e) => handleTypeChange(e.target.value)}
            className="h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-xs shadow-xs focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring text-foreground font-medium cursor-pointer"
            data-testid="graph-type-select"
          >
            <option value="ALL">All Entity Types</option>
            <option value={EntityType.DEPARTMENT}>Departments</option>
            <option value={EntityType.PROJECT}>Projects</option>
            <option value={EntityType.EMPLOYEE}>Employees</option>
            <option value={EntityType.DOCUMENT}>Documents</option>
            <option value={EntityType.POLICY}>Policies</option>
            <option value={EntityType.TECHNOLOGY}>Technologies</option>
            <option value={EntityType.TOPIC}>Topics & Concepts</option>
            <option value={EntityType.TASK}>Tasks</option>
          </select>
        </div>

        {/* Action Controls */}
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={onRefresh}
            className="h-9 gap-1.5 text-xs"
            data-testid="graph-refresh-btn"
          >
            <RefreshCw className="h-3.5 w-3.5" />
            Refresh
          </Button>

          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowIngestInput(!showIngestInput)}
            className="h-9 gap-1.5 text-xs"
            data-testid="graph-incremental-btn"
          >
            <PlusCircle className="h-3.5 w-3.5 text-blue-500" />
            Extract Text
          </Button>

          <Button
            size="sm"
            disabled={isBuilding}
            onClick={() => onTriggerBuild(false)}
            className="h-9 gap-1.5 text-xs bg-primary hover:bg-primary/90 text-primary-foreground font-semibold shadow-xs"
            data-testid="graph-build-btn"
          >
            <Cpu className={`h-3.5 w-3.5 ${isBuilding ? 'animate-spin' : ''}`} />
            {isBuilding ? 'Constructing...' : 'Build Graph'}
          </Button>
        </div>
      </div>

      {/* Incremental Text Extraction Bar */}
      {showIngestInput && (
        <form onSubmit={submitTextUpdate} className="flex items-center gap-2 pt-2 border-t border-border">
          <Input
            placeholder="Enter unstructured text statement to extract named entities & relationships (e.g. 'Project Titan is led by Alice and applies to Engineering')..."
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            className="flex-1 h-9 text-xs"
            autoFocus
            data-testid="graph-incremental-input"
          />
          <Button type="submit" size="sm" className="h-9 text-xs" disabled={!inputText.trim() || isBuilding}>
            Extract & Link
          </Button>
          <Button type="button" variant="ghost" size="sm" className="h-9 text-xs" onClick={() => setShowIngestInput(false)}>
            Cancel
          </Button>
        </form>
      )}
    </div>
  );
};
