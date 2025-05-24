import { useParams, Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../lib/api';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { ArrowLeft, User, Bot, Calendar, Clock } from 'lucide-react';
import { useMemo } from 'react';

export default function ConversationDetailPage() {
  const { conversationId } = useParams<{ conversationId: string }>();

  const { data: conversation, isLoading } = useQuery({
    queryKey: ['conversation', conversationId],
    queryFn: () => apiClient.getConversation(conversationId!),
    enabled: !!conversationId,
  });

  // Format message content with markdown-like rendering
  const formatMessageContent = useMemo(() => {
    return (content: string) => {
      // Split by code blocks first
      const parts = content.split(/(```[\s\S]*?```)/);

      return parts.map((part, index) => {
        if (part.startsWith('```') && part.endsWith('```')) {
          // Code block
          const code = part.slice(3, -3);
          const [lang, ...codeLines] = code.split('\n');
          const codeContent = codeLines.join('\n').trim();

          return (
            <div key={index} className="my-3">
              {lang && lang.trim() && (
                <div className="bg-zinc-800 dark:bg-zinc-900 text-zinc-400 text-xs px-3 py-1 rounded-t-md inline-block">
                  {lang}
                </div>
              )}
              <pre className="bg-zinc-800 dark:bg-zinc-900 text-zinc-100 p-4 rounded-md rounded-tl-none overflow-x-auto">
                <code className="text-xs font-mono">{codeContent || code}</code>
              </pre>
            </div>
          );
        } else {
          // Process regular text with markdown features
          const lines = part.split('\n');
          return (
            <div key={index}>
              {lines.map((line, lineIndex) => {
                // Check for headers
                if (line.match(/^#{1,6}\s/)) {
                  const level = line.match(/^(#{1,6})/)[1].length;
                  const text = line.replace(/^#{1,6}\s/, '');
                  const Tag = `h${level}` as keyof JSX.IntrinsicElements;
                  const sizeClass = ['text-2xl', 'text-xl', 'text-lg', 'text-base', 'text-sm', 'text-sm'][level - 1];
                  return <Tag key={lineIndex} className={`${sizeClass} font-semibold mt-3 mb-2`}>{text}</Tag>;
                }

                // Check for bullet points
                if (line.match(/^[-*]\s/)) {
                  const text = line.replace(/^[-*]\s/, '');
                  return (
                    <li key={lineIndex} className="ml-4 list-disc">
                      {formatInlineElements(text)}
                    </li>
                  );
                }

                // Check for numbered lists
                if (line.match(/^\d+\.\s/)) {
                  const text = line.replace(/^\d+\.\s/, '');
                  return (
                    <li key={lineIndex} className="ml-4 list-decimal">
                      {formatInlineElements(text)}
                    </li>
                  );
                }

                // Regular paragraph
                return (
                  <div key={lineIndex} className={lineIndex > 0 ? 'mt-2' : ''}>
                    {formatInlineElements(line)}
                  </div>
                );
              })}
            </div>
          );
        }
      });
    };

    function formatInlineElements(text: string) {
      // Split by inline code, bold, and italic patterns
      const elements = text.split(/(`[^`]+`|\*\*[^*]+\*\*|\*[^*]+\*|_[^_]+_)/);

      return elements.map((element, i) => {
        // Inline code
        if (element.startsWith('`') && element.endsWith('`')) {
          return (
            <code key={i} className="bg-zinc-200 dark:bg-zinc-800 px-1 py-0.5 rounded text-xs font-mono">
              {element.slice(1, -1)}
            </code>
          );
        }

        // Bold
        if (element.startsWith('**') && element.endsWith('**')) {
          return <strong key={i}>{element.slice(2, -2)}</strong>;
        }

        // Italic
        if ((element.startsWith('*') && element.endsWith('*')) ||
            (element.startsWith('_') && element.endsWith('_'))) {
          return <em key={i}>{element.slice(1, -1)}</em>;
        }

        return <span key={i}>{element}</span>;
      });
    }
  }, []);

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
          {conversation.summary?.request || 'Conversation Details'}
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
                  {conversation.summary.languages?.[0] || 'unknown'}
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium">Frustration Level</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-2xl font-bold">
                  {conversation.summary.user_frustration}/5
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
              {conversation.clusters.map((clusterName, index) => (
                <Button key={index} variant="outline" size="sm">
                  {clusterName}
                </Button>
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
          <div className="space-y-4 max-h-[800px] overflow-y-auto pr-2">
            {conversation.messages?.map((message, index) => (
              <div
                key={index}
                className={cn(
                  "flex gap-4 p-4 rounded-lg border transition-all",
                  message.role === 'user'
                    ? 'bg-blue-50 dark:bg-blue-950/20 border-blue-200 dark:border-blue-800'
                    : 'bg-zinc-50 dark:bg-zinc-950/20 border-zinc-200 dark:border-zinc-800'
                )}
              >
                <div className="flex-shrink-0 mt-1">
                  <div className={cn(
                    "p-2 rounded-lg",
                    message.role === 'user'
                      ? 'bg-blue-500 text-white'
                      : 'bg-zinc-700 text-white'
                  )}>
                    {message.role === 'user' ? (
                      <User className="h-5 w-5" />
                    ) : (
                      <Bot className="h-5 w-5" />
                    )}
                  </div>
                </div>
                <div className="flex-1 space-y-2 min-w-0">
                  <div className="flex items-center gap-3 flex-wrap">
                    <span className="font-semibold text-sm">
                      {message.role === 'user' ? 'User' : 'Assistant'}
                    </span>
                    <span className="text-xs text-muted-foreground flex items-center gap-1">
                      <Clock className="h-3 w-3" />
                      {new Date(message.created_at).toLocaleTimeString([], {
                        hour: '2-digit',
                        minute: '2-digit'
                      })}
                    </span>
                  </div>
                  <div className="text-sm leading-relaxed break-words">
                    {formatMessageContent(message.content)}
                  </div>
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
