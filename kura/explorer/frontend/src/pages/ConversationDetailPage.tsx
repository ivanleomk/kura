import { useParams, Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../lib/api';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { ArrowLeft, User, Bot, Calendar } from 'lucide-react';

export default function ConversationDetailPage() {
  const { conversationId } = useParams<{ conversationId: string }>();
  
  const { data: conversation, isLoading } = useQuery({
    queryKey: ['conversation', conversationId],
    queryFn: () => apiClient.getConversation(conversationId!),
    enabled: !!conversationId,
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-muted-foreground">Loading conversation...</div>
      </div>
    );
  }

  if (!conversation) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-muted-foreground">Conversation not found</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Link to="/conversations">
          <Button variant="ghost" size="sm">
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Conversations
          </Button>
        </Link>
      </div>

      <div>
        <h2 className="text-3xl font-bold tracking-tight">
          {conversation.summary?.title || 'Conversation Details'}
        </h2>
        {conversation.summary && (
          <p className="text-muted-foreground mt-2">{conversation.summary.summary}</p>
        )}
      </div>

      {/* Metadata */}
      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">Created</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold">
              {new Date(conversation.created_at).toLocaleDateString()}
            </p>
            <p className="text-xs text-muted-foreground">
              {new Date(conversation.created_at).toLocaleTimeString()}
            </p>
          </CardContent>
        </Card>

        {conversation.summary && (
          <>
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium">Language</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-2xl font-bold capitalize">
                  {conversation.summary.language}
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium">Frustration Level</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-2xl font-bold">
                  {conversation.summary.frustration}/5
                </p>
              </CardContent>
            </Card>
          </>
        )}
      </div>

      {/* Associated Clusters */}
      {conversation.clusters && conversation.clusters.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Associated Clusters</CardTitle>
            <CardDescription>This conversation belongs to these clusters</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              {conversation.clusters.map((cluster) => (
                <Link key={cluster.id} to={`/clusters/${cluster.id}`}>
                  <Button variant="outline" size="sm">
                    {cluster.name}
                  </Button>
                </Link>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Messages */}
      <Card>
        <CardHeader>
          <CardTitle>Messages</CardTitle>
          <CardDescription>
            {conversation.messages?.length || 0} messages in this conversation
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {conversation.messages?.map((message, index) => (
              <div
                key={index}
                className={cn(
                  "flex gap-3 p-4 rounded-lg",
                  message.role === 'user' ? 'bg-secondary' : 'bg-muted'
                )}
              >
                <div className="flex-shrink-0">
                  {message.role === 'user' ? (
                    <User className="h-5 w-5" />
                  ) : (
                    <Bot className="h-5 w-5" />
                  )}
                </div>
                <div className="flex-1 space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="font-medium capitalize">{message.role}</span>
                    <span className="text-xs text-muted-foreground">
                      {new Date(message.created_at).toLocaleTimeString()}
                    </span>
                  </div>
                  <div className="text-sm whitespace-pre-wrap">{message.content}</div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

function cn(...classes: string[]) {
  return classes.filter(Boolean).join(' ');
}