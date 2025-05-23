import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../lib/api';
import ClusterMap from '../components/ClusterMap';
import ClusterTree from '../components/ClusterTree';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Map, TreePine } from 'lucide-react';

type ViewMode = 'map' | 'tree';

export default function ClustersPage() {
  const [viewMode, setViewMode] = useState<ViewMode>('map');
  
  const { data: clusters, isLoading } = useQuery({
    queryKey: ['clusters'],
    queryFn: () => apiClient.getClusters({ limit: 200 }),
  });

  const { data: clusterTree } = useQuery({
    queryKey: ['cluster-tree'],
    queryFn: apiClient.getClusterTree,
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-muted-foreground">Loading clusters...</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Clusters</h2>
          <p className="text-muted-foreground">
            Explore conversation clusters and their relationships
          </p>
        </div>
        
        <div className="flex gap-2">
          <Button
            variant={viewMode === 'map' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setViewMode('map')}
            className="flex items-center gap-2"
          >
            <Map className="h-4 w-4" />
            Map View
          </Button>
          <Button
            variant={viewMode === 'tree' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setViewMode('tree')}
            className="flex items-center gap-2"
          >
            <TreePine className="h-4 w-4" />
            Tree View
          </Button>
        </div>
      </div>

      {viewMode === 'map' ? (
        <Card>
          <CardHeader>
            <CardTitle>Cluster Map</CardTitle>
            <CardDescription>
              2D visualization of clusters using UMAP coordinates. Size represents conversation count, color intensity shows frustration level.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <ClusterMap clusters={clusters?.items || []} />
          </CardContent>
        </Card>
      ) : (
        <Card>
          <CardHeader>
            <CardTitle>Cluster Hierarchy</CardTitle>
            <CardDescription>
              Navigate through the hierarchical structure of clusters
            </CardDescription>
          </CardHeader>
          <CardContent>
            <ClusterTree clusters={clusterTree || []} />
          </CardContent>
        </Card>
      )}
    </div>
  );
}