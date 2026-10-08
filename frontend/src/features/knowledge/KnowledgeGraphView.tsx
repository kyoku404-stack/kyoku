import React from 'react';
import type { KgEntity, KgRelationship } from '@/types/knowledge';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Network, FileText, User, Folder, Building2, Cpu, ArrowRight } from 'lucide-react';

interface KnowledgeGraphViewProps {
  entities: KgEntity[];
  relationships: KgRelationship[];
  loading?: boolean;
}

const getEntityIcon = (entityType: string) => {
  switch (entityType) {
    case 'Person':
      return <User className="w-4 h-4 text-purple-500" />;
    case 'Project':
      return <Folder className="w-4 h-4 text-blue-500" />;
    case 'Department':
      return <Building2 className="w-4 h-4 text-emerald-500" />;
    case 'Technology':
      return <Cpu className="w-4 h-4 text-amber-500" />;
    case 'Document':
    default:
      return <FileText className="w-4 h-4 text-cyan-500" />;
  }
};

export const KnowledgeGraphView: React.FC<KnowledgeGraphViewProps> = ({
  entities,
  relationships,
  loading = false,
}) => {
  if (loading) {
    return <Card className="p-8 animate-pulse bg-muted/40 h-64" />;
  }

  if (!entities.length) {
    return (
      <Card className="p-8 text-center text-muted-foreground border-dashed">
        <Network className="w-12 h-12 mx-auto mb-3 opacity-40 text-primary" />
        <p className="font-medium text-lg text-foreground">Knowledge Graph empty</p>
        <p className="text-sm mt-1">Extracted enterprise entities and relationship edges will render here.</p>
      </Card>
    );
  }

  const entityMap = new Map<string, KgEntity>();
  entities.forEach((e) => entityMap.set(e.id, e));

  return (
    <div className="space-y-6">
      {/* Entities grid */}
      <div>
        <h3 className="text-sm font-semibold mb-3 flex items-center gap-2">
          <Network className="w-4 h-4 text-primary" />
          Extracted Entities ({entities.length})
        </h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {entities.map((entity) => (
            <Card key={entity.id} className="p-3 hover:border-primary/40 transition-all">
              <div className="flex items-start justify-between gap-2">
                <div className="flex items-center gap-2.5">
                  <div className="p-2 rounded-md bg-muted">
                    {getEntityIcon(entity.entity_type)}
                  </div>
                  <div>
                    <h4 className="text-xs font-semibold text-foreground line-clamp-1">{entity.name}</h4>
                    <p className="text-[10px] text-muted-foreground">{entity.entity_type}</p>
                  </div>
                </div>
                <Badge variant="outline" className="text-[10px] px-1.5 py-0">
                  ID: {entity.id.slice(0, 4)}
                </Badge>
              </div>
              {entity.description && (
                <p className="text-xs text-muted-foreground mt-2 line-clamp-2">{entity.description}</p>
              )}
            </Card>
          ))}
        </div>
      </div>

      {/* Relationships */}
      {relationships.length > 0 && (
        <div>
          <h3 className="text-sm font-semibold mb-3 flex items-center gap-2">
            <ArrowRight className="w-4 h-4 text-primary" />
            Semantic Relationship Edges ({relationships.length})
          </h3>
          <div className="space-y-2">
            {relationships.map((rel) => {
              const src = entityMap.get(rel.source_entity_id);
              const tgt = entityMap.get(rel.target_entity_id);

              return (
                <Card key={rel.id} className="p-2.5 px-4 flex items-center justify-between text-xs">
                  <div className="flex items-center gap-2">
                    <span className="font-semibold text-foreground">
                      {src?.name || rel.source_entity_id.slice(0, 6)}
                    </span>
                    <Badge variant="secondary" className="text-[10px]">
                      {rel.relation_type}
                    </Badge>
                    <ArrowRight className="w-3 h-3 text-muted-foreground" />
                    <span className="font-semibold text-foreground">
                      {tgt?.name || rel.target_entity_id.slice(0, 6)}
                    </span>
                  </div>

                  <div className="flex items-center gap-3 text-muted-foreground text-[11px]">
                    <span>Weight: {rel.weight}</span>
                    <span>Confidence: {(rel.confidence_score * 100).toFixed(0)}%</span>
                  </div>
                </Card>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};
