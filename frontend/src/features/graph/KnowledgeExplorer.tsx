/**
 * KEEP Enterprise Platform — KnowledgeExplorer Component (Phase 2.4).
 *
 * Interactive SVG topology visualization canvas with dynamic layout,
 * node selection, directed semantic relationship edges, type-based color coding,
 * pan, zoom, and real-time query filtering.
 *
 * Specification: docs/API/api-contract.md Section 11 & devdocs/p2/p2.4.txt
 * Author: Member 3 (Frontend Lead)
 */

import React, { useState, useMemo, useRef } from 'react';
import { Button } from '@/components/ui/button';
import {
  ZoomIn,
  ZoomOut,
  Maximize2,
  Layers,
  Sparkles,
} from 'lucide-react';
import type { ExplorerNode, ExplorerLink } from '@/types/graph';

interface KnowledgeExplorerProps {
  nodes: ExplorerNode[];
  links: ExplorerLink[];
  selectedEntityId: string | null;
  onSelectEntity: (id: string) => void;
  searchQuery?: string;
  selectedEntityType?: string;
  loading?: boolean;
}

const TYPE_COLORS: Record<string, { bg: string; stroke: string; text: string }> = {
  DEPARTMENT: { bg: '#3b82f6', stroke: '#1d4ed8', text: '#ffffff' }, // Blue
  PROJECT: { bg: '#8b5cf6', stroke: '#6d28d9', text: '#ffffff' },    // Purple
  EMPLOYEE: { bg: '#10b981', stroke: '#047857', text: '#ffffff' },   // Green
  DOCUMENT: { bg: '#f59e0b', stroke: '#b45309', text: '#ffffff' },   // Amber
  POLICY: { bg: '#f43f5e', stroke: '#be123c', text: '#ffffff' },     // Rose
  TECHNOLOGY: { bg: '#06b6d4', stroke: '#0e7490', text: '#ffffff' }, // Cyan
  TOPIC: { bg: '#14b8a6', stroke: '#0f766e', text: '#ffffff' },      // Teal
  CONCEPT: { bg: '#6366f1', stroke: '#4338ca', text: '#ffffff' },    // Indigo
  TASK: { bg: '#eab308', stroke: '#a16207', text: '#ffffff' },       // Yellow
  ORGANIZATION: { bg: '#ec4899', stroke: '#be185d', text: '#ffffff'},// Pink
};

const DEFAULT_COLOR = { bg: '#64748b', stroke: '#334155', text: '#ffffff' };

export const KnowledgeExplorer: React.FC<KnowledgeExplorerProps> = ({
  nodes,
  links,
  selectedEntityId,
  onSelectEntity,
  searchQuery = '',
  selectedEntityType = 'ALL',
  loading = false,
}) => {
  const [zoom, setZoom] = useState<number>(1);
  const [pan, setPan] = useState<{ x: number; y: number }>({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
  const [hoveredNodeId, setHoveredNodeId] = useState<string | null>(null);

  const containerRef = useRef<HTMLDivElement>(null);

  // Compute 2D node coordinates in a circular/force-dispersed layout
  const positionedNodes = useMemo(() => {
    if (nodes.length === 0) return [];

    const width = 800;
    const height = 550;
    const centerX = width / 2;
    const centerY = height / 2;

    const total = nodes.length;
    return nodes.map((node, index) => {
      // Distribute in concentric rings based on degree/value
      const ring = index % 3;
      const radius = 90 + ring * 100 + (index % 5) * 15;
      const angle = (2 * Math.PI * index) / total + (ring * 0.4);

      const x = centerX + radius * Math.cos(angle);
      const y = centerY + radius * Math.sin(angle);

      // Node size scaled by val / degree
      const r = Math.max(14, Math.min(28, 12 + node.val * 0.5));

      return {
        ...node,
        x,
        y,
        r,
      };
    });
  }, [nodes]);

  // Lookup map for fast edge rendering
  const nodePositionMap = useMemo(() => {
    const map = new Map<string, { x: number; y: number; r: number; label: string; type: string }>();
    positionedNodes.forEach((n) => {
      map.set(n.id, { x: n.x, y: n.y, r: n.r, label: n.label, type: n.type });
    });
    return map;
  }, [positionedNodes]);

  // Filter evaluation
  const isNodeDimmed = (node: ExplorerNode) => {
    if (selectedEntityType !== 'ALL' && node.type !== selectedEntityType) {
      return true;
    }
    if (searchQuery.trim()) {
      return !node.label.toLowerCase().includes(searchQuery.toLowerCase());
    }
    return false;
  };

  // Pan interaction
  const handleMouseDown = (e: React.MouseEvent) => {
    setIsDragging(true);
    setDragStart({ x: e.clientX - pan.x, y: e.clientY - pan.y });
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (isDragging) {
      setPan({ x: e.clientX - dragStart.x, y: e.clientY - dragStart.y });
    }
  };

  const handleMouseUp = () => {
    setIsDragging(false);
  };

  const resetView = () => {
    setZoom(1);
    setPan({ x: 0, y: 0 });
  };

  return (
    <div
      ref={containerRef}
      className="relative flex flex-col h-[560px] w-full rounded-xl border border-border bg-card/60 backdrop-blur-md overflow-hidden shadow-xs select-none"
      data-testid="knowledge-explorer"
    >
      {/* Canvas Top Bar Controls */}
      <div className="absolute top-3 right-3 z-10 flex items-center gap-1.5 rounded-lg border border-border/80 bg-background/80 p-1 backdrop-blur-sm shadow-xs">
        <Button
          variant="ghost"
          size="icon"
          className="h-7 w-7"
          onClick={() => setZoom((z) => Math.min(z + 0.2, 2.5))}
          title="Zoom In"
        >
          <ZoomIn className="h-3.5 w-3.5" />
        </Button>
        <Button
          variant="ghost"
          size="icon"
          className="h-7 w-7"
          onClick={() => setZoom((z) => Math.max(z - 0.2, 0.4))}
          title="Zoom Out"
        >
          <ZoomOut className="h-3.5 w-3.5" />
        </Button>
        <Button
          variant="ghost"
          size="icon"
          className="h-7 w-7"
          onClick={resetView}
          title="Reset View"
        >
          <Maximize2 className="h-3.5 w-3.5" />
        </Button>
      </div>

      {/* Canvas Type Legend */}
      <div className="absolute bottom-3 left-3 z-10 hidden sm:flex items-center gap-2 rounded-lg border border-border/70 bg-background/80 px-2.5 py-1.5 backdrop-blur-sm text-[11px] text-muted-foreground shadow-xs">
        <span className="font-semibold text-foreground flex items-center gap-1">
          <Layers className="h-3 w-3" /> Ontology:
        </span>
        <div className="flex items-center gap-1.5">
          <span className="h-2.5 w-2.5 rounded-full bg-blue-500" /> Dept
          <span className="h-2.5 w-2.5 rounded-full bg-purple-500" /> Project
          <span className="h-2.5 w-2.5 rounded-full bg-emerald-500" /> Employee
          <span className="h-2.5 w-2.5 rounded-full bg-amber-500" /> Document
          <span className="h-2.5 w-2.5 rounded-full bg-rose-500" /> Policy
          <span className="h-2.5 w-2.5 rounded-full bg-cyan-500" /> Tech
        </div>
      </div>

      {/* SVG Interactive Canvas */}
      <svg
        className={`w-full h-full cursor-${isDragging ? 'grabbing' : 'grab'}`}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
      >
        <defs>
          <marker
            id="arrow"
            viewBox="0 0 10 10"
            refX="18"
            refY="5"
            markerWidth="5"
            markerHeight="5"
            orient="auto-start-reverse"
          >
            <path d="M 0 1 L 9 5 L 0 9 z" fill="currentColor" className="text-muted-foreground/60" />
          </marker>
        </defs>

        <g transform={`translate(${pan.x}, ${pan.y}) scale(${zoom})`}>
          {/* Directed Links */}
          {links.map((link, idx) => {
            const src = nodePositionMap.get(link.source);
            const tgt = nodePositionMap.get(link.target);
            if (!src || !tgt) return null;

            const isHighlighted =
              selectedEntityId === link.source ||
              selectedEntityId === link.target ||
              hoveredNodeId === link.source ||
              hoveredNodeId === link.target;

            return (
              <g key={`edge-${idx}`}>
                <line
                  x1={src.x}
                  y1={src.y}
                  x2={tgt.x}
                  y2={tgt.y}
                  stroke={isHighlighted ? '#8b5cf6' : 'currentColor'}
                  strokeWidth={isHighlighted ? 2.5 : 1.2}
                  strokeOpacity={isHighlighted ? 0.9 : 0.3}
                  className="text-muted-foreground transition-all"
                  markerEnd="url(#arrow)"
                />
                {/* Edge Label on hover or selected */}
                {isHighlighted && (
                  <text
                    x={(src.x + tgt.x) / 2}
                    y={(src.y + tgt.y) / 2 - 4}
                    textAnchor="middle"
                    fill="currentColor"
                    className="text-[9px] font-semibold text-foreground fill-foreground pointer-events-none drop-shadow-sm"
                  >
                    {link.label}
                  </text>
                )}
              </g>
            );
          })}

          {/* Node Circles */}
          {positionedNodes.map((node) => {
            const colors = TYPE_COLORS[node.type] || DEFAULT_COLOR;
            const isSelected = selectedEntityId === node.id;
            const isHovered = hoveredNodeId === node.id;
            const dimmed = isNodeDimmed(node);

            return (
              <g
                key={node.id}
                transform={`translate(${node.x}, ${node.y})`}
                className={`cursor-pointer transition-opacity duration-200 ${
                  dimmed ? 'opacity-20 pointer-events-none' : 'opacity-100'
                }`}
                onClick={(e) => {
                  e.stopPropagation();
                  onSelectEntity(node.id);
                }}
                onMouseEnter={() => setHoveredNodeId(node.id)}
                onMouseLeave={() => setHoveredNodeId(null)}
                data-testid={`graph-node-${node.id}`}
              >
                {/* Selection Halo Glow */}
                {(isSelected || isHovered) && (
                  <circle
                    r={node.r + 7}
                    fill="none"
                    stroke={colors.bg}
                    strokeWidth="3"
                    strokeDasharray="4 2"
                    className="animate-spin-slow opacity-80"
                  />
                )}

                {/* Node Body */}
                <circle
                  r={node.r}
                  fill={colors.bg}
                  stroke={isSelected ? '#ffffff' : colors.stroke}
                  strokeWidth={isSelected ? 3 : 1.5}
                  className="transition-transform hover:scale-110 drop-shadow-md"
                />

                {/* Node Label */}
                <text
                  y={node.r + 14}
                  textAnchor="middle"
                  className={`text-[10px] font-medium pointer-events-none select-none transition-all ${
                    isSelected
                      ? 'fill-foreground font-bold text-[11px]'
                      : 'fill-muted-foreground'
                  }`}
                >
                  {node.label.length > 16 ? node.label.slice(0, 15) + '…' : node.label}
                </text>
              </g>
            );
          })}
        </g>
      </svg>

      {/* Empty State / Loading Overlay */}
      {loading && (
        <div className="absolute inset-0 z-20 flex flex-col items-center justify-center bg-background/60 backdrop-blur-xs">
          <Sparkles className="h-8 w-8 text-primary animate-pulse" />
          <p className="mt-2 text-xs font-medium text-muted-foreground">Constructing Topology...</p>
        </div>
      )}

      {!loading && nodes.length === 0 && (
        <div className="absolute inset-0 flex flex-col items-center justify-center p-6 text-center">
          <div className="flex h-12 w-12 items-center justify-center rounded-full bg-primary/10 text-primary mb-3">
            <Layers className="h-6 w-6" />
          </div>
          <h4 className="text-sm font-semibold text-foreground">No Graph Entities Detected</h4>
          <p className="text-xs text-muted-foreground mt-1 max-w-sm">
            Click &ldquo;Build Graph&rdquo; above to map your organization structure, projects, tasks, and document triples.
          </p>
        </div>
      )}
    </div>
  );
};
