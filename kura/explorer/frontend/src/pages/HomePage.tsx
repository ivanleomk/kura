import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { apiClient } from '../lib/api';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { MessageSquare, Network, TrendingUp, AlertTriangle, Globe, Hash } from 'lucide-react';
import { Button } from '../components/ui/button';

export default function HomePage() {
  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ['stats'],
    queryFn: apiClient.getStats,
  });

  const { data: languageStats } = useQuery({
    queryKey: ['language-stats'],
    queryFn: apiClient.getLanguageStats,
  });

  const { data: outliers } = useQuery({
    queryKey: ['outliers'],
    queryFn: apiClient.getOutliers,
  });

  const { data: frustrationMap } = useQuery({
    queryKey: ['frustration-map'],
    queryFn: () => apiClient.getFrustrationMap(5),
  });

  if (statsLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-muted-foreground">Loading statistics...</div>
      </div>
    );
  }

  const topFrustratedClusters = frustrationMap?.slice(0, 5).sort((a, b) => b.avg_frustration - a.avg_frustration) || [];
  const topLanguages = languageStats?.slice(0, 5) || [];

  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">Dashboard</h2>
        <p className="text-muted-foreground">
          Overview of your Kura checkpoint data
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Conversations</CardTitle>
            <MessageSquare className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.total_conversations.toLocaleString()}</div>
            <p className="text-xs text-muted-foreground">
              {stats?.total_messages.toLocaleString()} total messages
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Clusters</CardTitle>
            <Network className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.total_clusters}</div>
            <p className="text-xs text-muted-foreground">
              {stats?.root_clusters} root clusters, {stats?.max_cluster_level + 1} levels deep
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Summaries</CardTitle>
            <Hash className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.total_summaries.toLocaleString()}</div>
            <p className="text-xs text-muted-foreground">
              Analyzed conversations
            </p>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* High Frustration Clusters */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <AlertTriangle className="h-5 w-5 text-orange-500" />
              High Frustration Areas
            </CardTitle>
            <CardDescription>
              Clusters with the highest average user frustration
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {topFrustratedClusters.map((cluster) => (
                <Link
                  key={cluster.cluster_id}
                  to={`/clusters/${cluster.cluster_id}`}
                  className="block"
                >
                  <div className="flex items-center justify-between p-3 rounded-lg border hover:bg-accent transition-colors">
                    <div>
                      <p className="font-medium">{cluster.cluster_name}</p>
                      <p className="text-sm text-muted-foreground">
                        {cluster.conversation_count} conversations
                      </p>
                    </div>
                    <div className="text-right">
                      <div className="text-lg font-semibold text-orange-500">
                        {cluster.avg_frustration.toFixed(1)}/5
                      </div>
                      <p className="text-xs text-muted-foreground">frustration</p>
                    </div>
                  </div>
                </Link>
              ))}
            </div>
            <div className="mt-4 pt-4 border-t">
              <Link to="/insights">
                <Button variant="outline" className="w-full">
                  View Frustration Heatmap
                </Button>
              </Link>
            </div>
          </CardContent>
        </Card>

        {/* Language Distribution */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Globe className="h-5 w-5 text-blue-500" />
              Language Distribution
            </CardTitle>
            <CardDescription>
              Most common languages in conversations
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {topLanguages.map((lang) => (
                <div key={lang.language} className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <span className="font-medium capitalize">{lang.language}</span>
                    <span className="text-sm text-muted-foreground">
                      {lang.count} conversations
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-24 bg-secondary rounded-full h-2">
                      <div
                        className="bg-primary h-2 rounded-full transition-all"
                        style={{ width: `${lang.percentage}%` }}
                      />
                    </div>
                    <span className="text-sm font-medium w-12 text-right">
                      {lang.percentage.toFixed(0)}%
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Outliers Summary */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <TrendingUp className="h-5 w-5 text-purple-500" />
            Notable Patterns
          </CardTitle>
          <CardDescription>
            Conversations that stand out from typical patterns
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <div className="text-center p-4 rounded-lg border">
              <div className="text-2xl font-bold text-orange-500">
                {outliers?.high_frustration.length || 0}
              </div>
              <p className="text-sm text-muted-foreground mt-1">
                High frustration
              </p>
            </div>
            <div className="text-center p-4 rounded-lg border">
              <div className="text-2xl font-bold text-blue-500">
                {outliers?.very_short.length || 0}
              </div>
              <p className="text-sm text-muted-foreground mt-1">
                Very short
              </p>
            </div>
            <div className="text-center p-4 rounded-lg border">
              <div className="text-2xl font-bold text-green-500">
                {outliers?.multilingual.length || 0}
              </div>
              <p className="text-sm text-muted-foreground mt-1">
                Multilingual
              </p>
            </div>
            <div className="text-center p-4 rounded-lg border">
              <div className="text-2xl font-bold text-red-500">
                {outliers?.assistant_errors.length || 0}
              </div>
              <p className="text-sm text-muted-foreground mt-1">
                Assistant errors
              </p>
            </div>
          </div>
          <div className="mt-4 pt-4 border-t flex justify-center">
            <Link to="/insights">
              <Button variant="outline">
                Explore All Outliers
              </Button>
            </Link>
          </div>
        </CardContent>
      </Card>

      {/* Quick Actions */}
      <div className="grid gap-4 md:grid-cols-3">
        <Link to="/clusters">
          <Card className="hover:bg-accent transition-colors cursor-pointer">
            <CardHeader>
              <CardTitle className="text-lg">Explore Clusters</CardTitle>
              <CardDescription>
                Navigate the cluster hierarchy and visualize relationships
              </CardDescription>
            </CardHeader>
          </Card>
        </Link>
        
        <Link to="/conversations">
          <Card className="hover:bg-accent transition-colors cursor-pointer">
            <CardHeader>
              <CardTitle className="text-lg">Browse Conversations</CardTitle>
              <CardDescription>
                Search and filter through all conversations
              </CardDescription>
            </CardHeader>
          </Card>
        </Link>
        
        <Link to="/insights">
          <Card className="hover:bg-accent transition-colors cursor-pointer">
            <CardHeader>
              <CardTitle className="text-lg">View Insights</CardTitle>
              <CardDescription>
                Analyze patterns and trends across your data
              </CardDescription>
            </CardHeader>
          </Card>
        </Link>
      </div>
    </div>
  );
}