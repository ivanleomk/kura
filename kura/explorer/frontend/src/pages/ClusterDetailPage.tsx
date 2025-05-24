import { useParams, Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../lib/api';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { ArrowLeft, MessageSquare, TrendingUp, Globe, AlertTriangle } from 'lucide-react';
import { cn } from '../lib/utils';
import ConversationList from '../components/ConversationList';

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
        <ConversationList
          conversations={cluster.conversations}
          title="Conversations"
          description="All conversations in this cluster"
        />
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
