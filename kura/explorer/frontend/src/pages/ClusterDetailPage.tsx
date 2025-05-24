import { useParams, Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../lib/api';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { ArrowLeft, MessageSquare, TrendingUp, Globe, AlertTriangle, Calendar } from 'lucide-react';
import { cn } from '../lib/utils';

export default function ClusterDetailPage() {
  const { clusterId } = useParams<{ clusterId: string }>();
  
  const { data: cluster, isLoading } = useQuery({
    queryKey: ['cluster', clusterId],
    queryFn: () => apiClient.getCluster(clusterId!),
    enabled: !!clusterId,
  });

  const { data: summary } = useQuery({
    queryKey: ['cluster-summary', clusterId],
    queryFn: () => apiClient.getClusterSummary(clusterId!),
    enabled: !!clusterId,
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-muted-foreground">Loading cluster details...</div>
      </div>
    );
  }

  if (!cluster) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-muted-foreground">Cluster not found</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Link to="/clusters">
          <Button variant="ghost" size="sm">
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Clusters
          </Button>
        </Link>
      </div>

      <div>
        <h2 className="text-3xl font-bold tracking-tight">{cluster.name}</h2>
        <p className="text-muted-foreground">{cluster.description}</p>
      </div>

      {/* Stats Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Conversations</CardTitle>
            <MessageSquare className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{cluster.conversation_count}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Avg Frustration</CardTitle>
            <AlertTriangle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {cluster.avg_frustration?.toFixed(1) || 'N/A'}/5
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Level</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{cluster.level}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Languages</CardTitle>
            <Globe className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{cluster.languages?.length || 0}</div>
          </CardContent>
        </Card>
      </div>

      {/* Language Distribution */}
      {summary?.language_distribution && (
        <Card>
          <CardHeader>
            <CardTitle>Language Distribution</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {Object.entries(summary.language_distribution).map(([lang, count]) => (
                <div key={lang} className="flex items-center justify-between">
                  <span className="capitalize">{lang}</span>
                  <span className="text-muted-foreground">{count} conversations</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* All Conversations */}
      {cluster.conversations && cluster.conversations.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Conversations ({cluster.conversations.length})</CardTitle>
            <CardDescription>All conversations in this cluster</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4 max-h-[800px] overflow-y-auto">
              {cluster.conversations.map((conv: any) => (
                <Link
                  key={conv.id}
                  to={`/conversations/${conv.id}`}
                  className="block p-4 rounded-lg border hover:bg-accent transition-colors"
                >
                  <div className="space-y-2">
                    <p className="font-medium text-lg">{conv.summary?.request || 'Untitled Conversation'}</p>
                    <p className="text-sm text-muted-foreground line-clamp-3">
                      {conv.summary?.summary || 'No summary available'}
                    </p>
                    
                    <div className="flex items-center gap-4 text-sm">
                      {conv.summary?.user_frustration && (
                        <div className="flex items-center gap-1">
                          <AlertTriangle className={cn(
                            "h-4 w-4",
                            conv.summary.user_frustration <= 2 ? "text-green-500" :
                            conv.summary.user_frustration <= 3 ? "text-blue-500" :
                            conv.summary.user_frustration <= 4 ? "text-orange-500" :
                            "text-red-500"
                          )} />
                          <span>Frustration: {conv.summary.user_frustration}/5</span>
                        </div>
                      )}
                      
                      {conv.summary?.languages?.[0] && (
                        <div className="flex items-center gap-1">
                          <Globe className="h-4 w-4 text-muted-foreground" />
                          <span className="capitalize">{conv.summary.languages[0]}</span>
                        </div>
                      )}
                      
                      <div className="flex items-center gap-1 text-muted-foreground">
                        <Calendar className="h-4 w-4" />
                        <span>{new Date(conv.created_at).toLocaleDateString()}</span>
                      </div>
                    </div>
                  </div>
                </Link>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Child Clusters */}
      {cluster.children && cluster.children.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Sub-clusters</CardTitle>
            <CardDescription>Clusters within this cluster</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {cluster.children.map((child: any) => (
                <Link
                  key={child.id}
                  to={`/clusters/${child.id}`}
                  className="block p-3 rounded-lg border hover:bg-accent transition-colors"
                >
                  <p className="font-medium">{child.name}</p>
                  <p className="text-sm text-muted-foreground">{child.description}</p>
                </Link>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}