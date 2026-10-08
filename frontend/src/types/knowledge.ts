/**
 * KEEP Enterprise Platform — Knowledge Graph Types.
 * Aligned with database schema `kg_entities` and `kg_relationships` tables.
 */

export type EntityType = 'Person' | 'Project' | 'Technology' | 'Department' | 'Document' | 'Policy';
export type RelationType = 'AUTHOR_OF' | 'ASSIGNED_TO' | 'DEPENDS_ON' | 'BELONGS_TO' | 'MENTIONS' | 'LEADS';

export interface KgEntity {
  id: string;
  organization_id: string;
  name: string;
  entity_type: EntityType | string;
  description?: string | null;
  source_document_id?: string | null;
  properties: Record<string, unknown>;
  created_at: string;
  updated_at?: string | null;
}

export interface KgRelationship {
  id: string;
  organization_id: string;
  source_entity_id: string;
  target_entity_id: string;
  relation_type: RelationType | string;
  weight: number;
  confidence_score: number;
  source_document_id?: string | null;
  properties: Record<string, unknown>;
  created_at: string;
  updated_at?: string | null;
}

export interface KgEntityCreate {
  name: string;
  entity_type: EntityType | string;
  description?: string;
  source_document_id?: string;
  properties?: Record<string, unknown>;
}

export interface KgRelationshipCreate {
  source_entity_id: string;
  target_entity_id: string;
  relation_type: RelationType | string;
  weight?: number;
  confidence_score?: number;
  source_document_id?: string;
  properties?: Record<string, unknown>;
}

export interface KgQueryRequest {
  entity_name?: string;
  entity_type?: EntityType | string;
  relation_type?: RelationType | string;
  depth?: number;
  limit?: number;
}

export interface KgQueryResponse {
  entities: KgEntity[];
  relationships: KgRelationship[];
  total_entities: number;
  total_relationships: number;
}
