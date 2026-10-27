/**
 * KEEP Enterprise Platform — Knowledge Graph & Enterprise Intelligence Types (Phase 2.4).
 * Aligned with backend schemas (backend/app/schemas/graph.py) and API contracts.
 */

export enum EntityType {
  ORGANIZATION = 'ORGANIZATION',
  DEPARTMENT = 'DEPARTMENT',
  TEAM = 'TEAM',
  EMPLOYEE = 'EMPLOYEE',
  DOCUMENT = 'DOCUMENT',
  POLICY = 'POLICY',
  SOP = 'SOP',
  MEETING = 'MEETING',
  REPORT = 'REPORT',
  RESEARCH_PAPER = 'RESEARCH_PAPER',
  PROJECT = 'PROJECT',
  TASK = 'TASK',
  MILESTONE = 'MILESTONE',
  RISK = 'RISK',
  DECISION = 'DECISION',
  TECHNOLOGY = 'TECHNOLOGY',
  TOPIC = 'TOPIC',
  CONCEPT = 'CONCEPT',
}

export enum RelationType {
  WORKS_IN = 'WORKS_IN',
  LEADS = 'LEADS',
  PARTICIPATES_IN = 'PARTICIPATES_IN',
  AUTHORED = 'AUTHORED',
  CONTAINS = 'CONTAINS',
  REFERENCES = 'REFERENCES',
  APPLIES_TO = 'APPLIES_TO',
  DEPENDS_ON = 'DEPENDS_ON',
  DISCUSSED = 'DISCUSSED',
  EXPERT_IN = 'EXPERT_IN',
  GOVERNED_BY = 'GOVERNED_BY',
  BLOCKS = 'BLOCKS',
  BLOCKED_BY = 'BLOCKED_BY',
  REPORTS_TO = 'REPORTS_TO',
  BELONGS_TO = 'BELONGS_TO',
  OWNED_BY = 'OWNED_BY',
  MEMBER_OF = 'MEMBER_OF',
  CONTRIBUTES_TO = 'CONTRIBUTES_TO',
  PART_OF = 'PART_OF',
  AUTHORS = 'AUTHORS',
  MENTIONS = 'MENTIONS',
}

export interface GraphBuildRequest {
  rebuild_all?: boolean;
  confidence_threshold?: number;
  include_documents?: boolean;
  include_organizational?: boolean;
}

export interface GraphBuildResponse {
  organization_id: string;
  entities_created: number;
  entities_updated: number;
  relationships_created: number;
  duration_seconds: number;
  total_entities: number;
  total_relationships: number;
}

export interface GraphUpdateRequest {
  document_id?: string;
  text_content: string;
  metadata?: Record<string, unknown>;
}

export interface ExtractedEntityItem {
  id: string;
  name: string;
  entity_type: string;
}

export interface ExtractedRelationshipItem {
  source: string;
  relation: string;
  target: string;
}

export interface GraphUpdateResponse {
  entities_extracted: number;
  relationships_extracted: number;
  extracted_entities: ExtractedEntityItem[];
  extracted_relationships: ExtractedRelationshipItem[];
}

export interface EntityResponse {
  id: string;
  organization_id: string;
  name: string;
  entity_type: string;
  properties: Record<string, unknown>;
  in_degree: number;
  out_degree: number;
  created_at?: string;
}

export interface OutgoingRelationshipItem {
  relationship_id: string;
  target_entity_id: string;
  target_entity_name: string;
  target_entity_type: string;
  relation_type: string;
  weight: number;
}

export interface IncomingRelationshipItem {
  relationship_id: string;
  source_entity_id: string;
  source_entity_name: string;
  source_entity_type: string;
  relation_type: string;
  weight: number;
}

export interface EntityRelationshipsResponse {
  entity_id: string;
  outgoing_relationships: OutgoingRelationshipItem[];
  incoming_relationships: IncomingRelationshipItem[];
}

export interface GraphQueryRequest {
  start_entity_id: string;
  max_depth?: number;
  allowed_relation_types?: string[];
  allowed_entity_types?: string[];
}

export interface GraphPathNode {
  id: string;
  name: string;
  entity_type: string;
  depth: number;
}

export interface GraphPathEdge {
  source: string;
  target: string;
  relation_type: string;
  weight: number;
}

export interface GraphQueryResponse {
  nodes: GraphPathNode[];
  edges: GraphPathEdge[];
  total_paths: number;
  max_depth_reached: number;
}

export interface ExplorerNode {
  id: string;
  label: string;
  type: string;
  val: number;
  x?: number;
  y?: number;
}

export interface ExplorerLink {
  source: string;
  target: string;
  label: string;
  weight: number;
}

export interface GraphMetricsResponse {
  total_entities: number;
  total_relationships: number;
  density: number;
  top_hub?: string | null;
}

export interface GraphExplorerResponse {
  nodes: ExplorerNode[];
  links: ExplorerLink[];
  metrics: GraphMetricsResponse;
}

export interface ExpertItem {
  user_id: string;
  full_name: string;
  department?: string | null;
  score: number;
  authored_documents_count: number;
  contributed_projects: string[];
  evidence_citations: string[];
}

export interface ExpertiseResponse {
  topic: string;
  experts: ExpertItem[];
}

export interface DependencyTreeNode {
  id: string;
  name: string;
  entity_type: string;
  depth: number;
  relation: string;
}

export interface RootEntityInfo {
  id: string;
  name: string;
  entity_type: string;
}

export interface ImpactAnalysisResponse {
  root_entity: RootEntityInfo;
  affected_departments: string[];
  dependent_projects: string[];
  impacted_tasks_count: number;
  severity_score: number;
  dependency_tree: DependencyTreeNode[];
}

export interface GraphFilterState {
  searchQuery: string;
  selectedEntityType: string;
  maxDepth: number;
  showOrphans: boolean;
}
