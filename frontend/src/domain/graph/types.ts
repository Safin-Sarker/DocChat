export interface GraphQueryRequest {
  entities: string[];
  max_depth?: number;
  limit?: number;
}

export interface GraphNode {
  id: string;
  label: string;
  type: string;
  properties?: Record<string, any>;
}

export interface GraphQueryResponse {
  nodes: GraphNode[];
}
