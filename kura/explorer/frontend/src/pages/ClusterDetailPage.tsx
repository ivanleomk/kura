import { useParams, Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { useState } from 'react';
import { apiClient } from '../lib/api';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { ArrowLeft, MessageSquare, TrendingUp, Globe, AlertTriangle, Calendar } from 'lucide-react';
import { cn } from '../lib/utils';

interface LanguageDistribution {
  [language: string]: number;
}

interface FormattedLangItem {
  key: string;
  label: string;
  type: 'language' | 'other' | 'placeholder';
}

// Helper function to format language distribution for the cluster detail page
const formatClusterLanguageDistribution = (
  distribution: LanguageDistribution | undefined,
  threshold = 3
): FormattedLangItem[] => {
  if (!distribution || Object.keys(distribution).length === 0) {
    return [{ key: 'no-data', label: 'No language data available', type: 'placeholder' }];
  }

  const sortedLanguages = Object.entries(distribution)
    .filter(([, count]) => count > 0) // Filter out languages with zero count
    .sort(([, countA], [, countB]) => countB - countA);

  if (sortedLanguages.length === 0) { // All counts were zero or became zero after filtering
    return [{ key: 'no-data-actual', label: 'No language data available', type: 'placeholder' }];
  }

  const items: FormattedLangItem[] = [];
  let otherCount = 0;
  let otherLanguagesCount = 0;

  for (const [lang, count] of sortedLanguages) {
    if (count >= threshold) {
      items.push({
        key: lang,
        label: `${lang.charAt(0).toUpperCase() + lang.slice(1)} (${count})`,
        type: 'language',
      });
    } else {
      otherCount += count;
      otherLanguagesCount++;
    }
  }

  if (otherLanguagesCount > 0) {
    items.push({
      key: 'other',
      label: `Other (${otherCount} from ${otherLanguagesCount} languages)`,
      type: 'other',
    });
  }

  if (items.length === 0) {
    // This case implies all languages were below threshold and got grouped into "Other",
    // or the initial distribution was empty (which is handled above).
    // If only "Other" exists, items will not be empty.
    // If distribution had items but all were filtered or none met threshold and none went to other (not possible with current logic)
    return [{ key: 'no-qualifying-data', label: 'No languages meet display criteria', type: 'placeholder' }];
  }

  return items;
};

export default function ClusterDetailPage() {
  const { clusterId } = useParams<{ clusterId: string }>();
  const [frustrationFilter, setFrustrationFilter] = useState<'all' | 'low' | 'medium' | 'high' | 'critical'>('all');
  
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

  // Filter conversations by frustration level
  const filteredConversations = cluster?.conversations?.filter((conv: any) => {
    if (frustrationFilter === 'all') return true;
    if (!conv.summary?.user_frustration) return false;
    
    const frustration = conv.summary.user_frustration;
    switch (frustrationFilter) {
      case 'low': return frustration <= 2;
      case 'medium': return frustration === 3;
      case 'high': return frustration === 4;
      case 'critical': return frustration >= 5;
      default: return true;
    }
  }) || [];

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
            <div className="flex flex-wrap gap-2">
              {formatClusterLanguageDistribution(summary.language_distribution).map((item) => (
                <div
                  key={item.key}
                  className={cn(
                    "text-xs px-2.5 py-1 rounded-full border font-medium",
                    item.type === 'placeholder' 
                      ? "text-muted-foreground bg-muted"
                      : "bg-secondary text-secondary-foreground"
                  )}
                >
                  {item.label}
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
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>Conversations ({filteredConversations.length})</CardTitle>
                <CardDescription>
                  {filteredConversations.length === cluster.conversations.length 
                    ? 'All conversations in this cluster'
                    : `Filtered conversations (${filteredConversations.length} of ${cluster.conversations.length})`
                  }
                </CardDescription>
              </div>
              <div className="flex gap-2">
                <Button
                  variant={frustrationFilter === 'all' ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setFrustrationFilter('all')}
                >
                  All
                </Button>
                <Button
                  variant={frustrationFilter === 'low' ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setFrustrationFilter('low')}
                  className={frustrationFilter === 'low' ? 'bg-green-600 hover:bg-green-700' : 'text-green-600 border-green-200 hover:bg-green-50'}
                >
                  Low (1-2)
                </Button>
                <Button
                  variant={frustrationFilter === 'medium' ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setFrustrationFilter('medium')}
                  className={frustrationFilter === 'medium' ? 'bg-blue-600 hover:bg-blue-700' : 'text-blue-600 border-blue-200 hover:bg-blue-50'}
                >
                  Medium (3)
                </Button>
                <Button
                  variant={frustrationFilter === 'high' ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setFrustrationFilter('high')}
                  className={frustrationFilter === 'high' ? 'bg-orange-600 hover:bg-orange-700' : 'text-orange-600 border-orange-200 hover:bg-orange-50'}
                >
                  High (4)
                </Button>
                <Button
                  variant={frustrationFilter === 'critical' ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setFrustrationFilter('critical')}
                  className={frustrationFilter === 'critical' ? 'bg-red-600 hover:bg-red-700' : 'text-red-600 border-red-200 hover:bg-red-50'}
                >
                  Critical (5)
                </Button>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-4 max-h-[800px] overflow-y-auto">
              {filteredConversations.map((conv: any) => (
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
              {filteredConversations.length === 0 && (
                <div className="text-center py-8 text-muted-foreground">
                  No conversations match the selected frustration level.
                </div>
              )}
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