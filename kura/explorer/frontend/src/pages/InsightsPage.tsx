import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../lib/api';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, Legend } from 'recharts';
import { TrendingUp, Globe, AlertTriangle, Layers } from 'lucide-react';

export default function InsightsPage() {
  const { data: languageStats } = useQuery({
    queryKey: ['language-stats'],
    queryFn: apiClient.getLanguageStats,
  });

  const { data: frustrationMap } = useQuery({
    queryKey: ['frustration-map'],
    queryFn: () => apiClient.getFrustrationMap(),
  });

  const { data: themes } = useQuery({
    queryKey: ['themes'],
    queryFn: () => apiClient.getThemes(2),
  });

  const { data: outliers } = useQuery({
    queryKey: ['outliers'],
    queryFn: apiClient.getOutliers,
  });

  const { data: patterns } = useQuery({
    queryKey: ['common-patterns'],
    queryFn: apiClient.getCommonPatterns,
  });

  const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899'];

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">Insights</h2>
        <p className="text-muted-foreground">
          Analyze patterns and trends across your conversation data
        </p>
      </div>

      <Tabs defaultValue="languages" className="space-y-4">
        <TabsList>
          <TabsTrigger value="languages" className="flex items-center gap-2">
            <Globe className="h-4 w-4" />
            Languages
          </TabsTrigger>
          <TabsTrigger value="frustration" className="flex items-center gap-2">
            <AlertTriangle className="h-4 w-4" />
            Frustration
          </TabsTrigger>
          <TabsTrigger value="themes" className="flex items-center gap-2">
            <Layers className="h-4 w-4" />
            Themes
          </TabsTrigger>
          <TabsTrigger value="outliers" className="flex items-center gap-2">
            <TrendingUp className="h-4 w-4" />
            Outliers
          </TabsTrigger>
        </TabsList>

        {/* Language Analysis */}
        <TabsContent value="languages" className="space-y-6">
          <div className="grid gap-6 lg:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle>Language Distribution</CardTitle>
                <CardDescription>
                  Breakdown of conversations by language
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="h-[400px]">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={languageStats}
                        cx="50%"
                        cy="50%"
                        labelLine={false}
                        label={({ name, percentage }) => `${name} (${percentage.toFixed(0)}%)`}
                        outerRadius={120}
                        fill="#8884d8"
                        dataKey="count"
                      >
                        {languageStats?.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                        ))}
                      </Pie>
                      <Tooltip />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Top Languages</CardTitle>
                <CardDescription>
                  Most common languages in conversations
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="h-[400px]">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={languageStats?.slice(0, 10)}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="language" angle={-45} textAnchor="end" height={100} />
                      <YAxis />
                      <Tooltip />
                      <Bar dataKey="count" fill="#3b82f6" />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Frustration Analysis */}
        <TabsContent value="frustration" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Frustration by Cluster</CardTitle>
              <CardDescription>
                Average user frustration levels across different clusters
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="h-[500px]">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart 
                    data={frustrationMap?.sort((a, b) => b.avg_frustration - a.avg_frustration).slice(0, 15)}
                    layout="horizontal"
                  >
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis type="number" domain={[0, 5]} />
                    <YAxis dataKey="cluster_name" type="category" width={200} />
                    <Tooltip />
                    <Bar dataKey="avg_frustration" fill="#ef4444" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>

          {patterns && (
            <div className="grid gap-4 md:grid-cols-3">
              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm font-medium">Average Length</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-2xl font-bold">
                    {patterns.avg_conversation_length?.toFixed(1)} messages
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm font-medium">User Starts</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-2xl font-bold">
                    {patterns.user_initiated_percentage?.toFixed(0)}%
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm font-medium">Assistant Ends</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-2xl font-bold">
                    {patterns.assistant_ended_percentage?.toFixed(0)}%
                  </p>
                </CardContent>
              </Card>
            </div>
          )}
        </TabsContent>

        {/* Themes Analysis */}
        <TabsContent value="themes" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Common Themes</CardTitle>
              <CardDescription>
                Recurring topics across clusters
              </CardDescription>
            </CardHeader>
            <CardContent>
              {themes && themes.length > 0 ? (
                <div className="space-y-4">
                  {themes.map((theme, index) => (
                    <div key={index} className="border rounded-lg p-4">
                      <div className="flex items-start justify-between">
                        <div>
                          <h4 className="font-medium">{theme.theme}</h4>
                          <p className="text-sm text-muted-foreground mt-1">
                            Appears in {theme.frequency} clusters
                          </p>
                        </div>
                      </div>
                      <div className="mt-2 flex flex-wrap gap-2">
                        {theme.cluster_ids.slice(0, 5).map((clusterId) => (
                          <span
                            key={clusterId}
                            className="text-xs bg-secondary px-2 py-1 rounded"
                          >
                            {clusterId}
                          </span>
                        ))}
                        {theme.cluster_ids.length > 5 && (
                          <span className="text-xs text-muted-foreground">
                            +{theme.cluster_ids.length - 5} more
                          </span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-muted-foreground text-center py-8">
                  No common themes found
                </p>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Outliers Analysis */}
        <TabsContent value="outliers" className="space-y-6">
          <div className="grid gap-4 md:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle>High Frustration Conversations</CardTitle>
                <CardDescription>
                  Conversations with frustration score of 5
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-bold text-orange-500">
                  {outliers?.high_frustration.length || 0}
                </div>
                <p className="text-sm text-muted-foreground mt-1">
                  conversations need attention
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Very Short Conversations</CardTitle>
                <CardDescription>
                  Conversations with 2 or fewer messages
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-bold text-blue-500">
                  {outliers?.very_short.length || 0}
                </div>
                <p className="text-sm text-muted-foreground mt-1">
                  potentially incomplete interactions
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Multilingual Conversations</CardTitle>
                <CardDescription>
                  Using 3 or more languages
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-bold text-green-500">
                  {outliers?.multilingual.length || 0}
                </div>
                <p className="text-sm text-muted-foreground mt-1">
                  complex language interactions
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Assistant Errors</CardTitle>
                <CardDescription>
                  Conversations with error indicators
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-bold text-red-500">
                  {outliers?.assistant_errors.length || 0}
                </div>
                <p className="text-sm text-muted-foreground mt-1">
                  potential failures to investigate
                </p>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}