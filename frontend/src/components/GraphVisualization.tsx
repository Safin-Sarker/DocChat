import { useEffect, useRef, useState, useCallback } from 'react';
import { Network } from 'vis-network';
import { DataSet } from 'vis-data';
import { Network as NetworkIcon, ZoomIn, ZoomOut, Maximize2 } from 'lucide-react';
import { useGraphQuery } from '@/hooks/useGraph';
import type { GraphNode } from '@/types/api';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';

interface GraphVisualizationProps {
  entities?: string[];
}

const getNodeColor = (type: string | undefined) => {
  const colors: Record<string, string> = {
    person: '#3b82f6',
    organization: '#10b981',
    location: '#f59e0b',
    concept: '#8b5cf6',
    entity: '#6366f1',
    default: '#6b7280',
  };
  const normalizedType = (type || 'default').toLowerCase();
  return colors[normalizedType] || colors.default;
};

export const GraphVisualization = ({ entities = [] }: GraphVisualizationProps) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const networkRef = useRef<Network | null>(null);
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);

  // Use query with caching - only fetches when entities change
  const { data, isLoading } = useGraphQuery(entities);

  // Create/update network visualization when data changes
  useEffect(() => {
    if (!data || !data.nodes || data.nodes.length === 0 || !containerRef.current) {
      return;
    }

    const nodes = new DataSet(
      data.nodes.map((node) => ({
        id: node.id,
        label: node.label,
        title: node.type || 'Entity',
        color: getNodeColor(node.type),
        font: { color: '#ffffff', size: 14 },
        shape: 'dot',
        size: 20,
      }))
    );

    const edgeData = data.nodes.flatMap((node, idx) =>
      data.nodes.slice(idx + 1).map((target, edgeIdx) => ({
        id: `${node.id}-${target.id}-${edgeIdx}`,
        from: node.id,
        to: target.id,
        color: { color: 'rgba(100, 100, 100, 0.3)' },
      }))
    );
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const edges = new DataSet(edgeData) as any;

    const options = {
      nodes: {
        borderWidth: 2,
        borderWidthSelected: 4,
        shadow: true,
      },
      edges: {
        width: 1,
      },
      physics: {
        enabled: true,
        barnesHut: {
          gravitationalConstant: -3000,
          centralGravity: 0.5,
          springLength: 120,
          springConstant: 0.02,
          damping: 0.5,
        },
        stabilization: {
          enabled: true,
          iterations: 300,
          fit: true,
        },
      },
      interaction: {
        hover: true,
        tooltipDelay: 200,
        zoomView: true,
        dragView: true,
      },
    };

    // Destroy existing network before creating new one
    if (networkRef.current) {
      networkRef.current.destroy();
      networkRef.current = null;
    }

    networkRef.current = new Network(
      containerRef.current,
      { nodes, edges },
      options
    );

    // Disable physics after stabilization to stop bouncing
    networkRef.current.on('stabilizationIterationsDone', () => {
      networkRef.current?.setOptions({ physics: { enabled: false } });
    });

    networkRef.current.on('click', (params) => {
      if (params.nodes.length > 0) {
        const nodeId = params.nodes[0];
        const node = data.nodes.find((n) => n.id === nodeId);
        setSelectedNode(node || null);
      } else {
        setSelectedNode(null);
      }
    });

    // Cleanup on unmount
    return () => {
      if (networkRef.current) {
        networkRef.current.destroy();
        networkRef.current = null;
      }
    };
  }, [data]);

  const handleZoomIn = useCallback(() => {
    networkRef.current?.moveTo({ scale: (networkRef.current.getScale() || 1) * 1.2 });
  }, []);

  const handleZoomOut = useCallback(() => {
    networkRef.current?.moveTo({ scale: (networkRef.current.getScale() || 1) * 0.8 });
  }, []);

  const handleFit = useCallback(() => {
    networkRef.current?.fit({ animation: true });
  }, []);

  return (
    <Card className="h-full flex flex-col shadow-xl border-2">
      <CardHeader className="border-b bg-accent/30">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="flex items-center justify-center w-10 h-10 rounded-full bg-primary/10">
              <NetworkIcon className="w-5 h-5 text-primary" />
            </div>
            <div>
              <CardTitle>Knowledge Graph</CardTitle>
              <p className="text-sm text-muted-foreground mt-1">
                {data && data.nodes ? `${data.nodes.length} nodes` : 'No data'}
              </p>
            </div>
          </div>
          <div className="flex gap-2">
            <Button size="icon" variant="outline" onClick={handleZoomIn}>
              <ZoomIn className="w-4 h-4" />
            </Button>
            <Button size="icon" variant="outline" onClick={handleZoomOut}>
              <ZoomOut className="w-4 h-4" />
            </Button>
            <Button size="icon" variant="outline" onClick={handleFit}>
              <Maximize2 className="w-4 h-4" />
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent className="flex-1 p-0 relative min-h-[400px]">
        {isLoading ? (
          <div className="absolute inset-0 flex items-center justify-center bg-background/50 backdrop-blur-sm">
            <div className="text-center space-y-3">
              <NetworkIcon className="w-12 h-12 text-primary animate-pulse mx-auto" />
              <p className="text-sm text-muted-foreground">Loading graph...</p>
            </div>
          </div>
        ) : !data || !data.nodes || data.nodes.length === 0 ? (
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="text-center space-y-3 opacity-50">
              <NetworkIcon className="w-16 h-16 text-muted-foreground mx-auto" />
              <p className="text-lg font-medium text-foreground">No graph data</p>
              <p className="text-sm text-muted-foreground">
                Query documents to see entity relationships
              </p>
            </div>
          </div>
        ) : (
          <>
            <div ref={containerRef} className="w-full h-full absolute inset-0" />
            {selectedNode && (
              <div className="absolute bottom-4 left-4 right-4 animate-in fade-in-50 slide-in-from-bottom-2">
                <Card className="p-4 bg-background/95 backdrop-blur-sm shadow-lg">
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <h3 className="font-semibold text-lg">{selectedNode.label}</h3>
                      <Badge variant="secondary">{selectedNode.type}</Badge>
                    </div>
                    {selectedNode.properties && Object.keys(selectedNode.properties).length > 0 && (
                      <div className="text-sm text-muted-foreground space-y-1">
                        {Object.entries(selectedNode.properties).map(([key, value]) => (
                          <div key={key}>
                            <span className="font-medium">{key}:</span> {String(value)}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </Card>
              </div>
            )}
          </>
        )}
      </CardContent>
    </Card>
  );
};
