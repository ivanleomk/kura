import { useState } from 'react';
import { Link } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { AlertTriangle, Globe, Calendar, Languages, Target, AlertCircle } from 'lucide-react';
import { cn } from '../lib/utils';

interface ConversationSummary {
  request?: string;
  summary?: string;
  task?: string;
  languages?: string[];
  user_frustration?: number;
  concerning_score?: number;
  assistant_errors?: string[];
}

interface Conversation {
  id: string;
  created_at: string;
  summary?: ConversationSummary;
  metadata?: any;
  message_count?: number;
}

interface FrustrationFacets {
  low: number;
  medium: number;
  high: number;
  critical: number;
}

interface ConversationListProps {
  conversations: Conversation[];
  title?: string;
  description?: string;
  showCard?: boolean;
  maxHeight?: string;
  facets?: FrustrationFacets; // Optional facets from backend
}

type FrustrationFilter = 'all' | 'low' | 'medium' | 'high' | 'critical';

export default function ConversationList({ 
  conversations, 
  title = "Conversations", 
  description,
  showCard = true,
  maxHeight = "800px",
  facets
}: ConversationListProps) {
  const [frustrationFilter, setFrustrationFilter] = useState<FrustrationFilter>('all');

  // Calculate conversation counts by frustration level
  // Use backend facets if available, otherwise calculate from current conversations
  const frustrationCounts = facets ? {
    all: conversations.length,
    low: facets.low,
    medium: facets.medium,
    high: facets.high,
    critical: facets.critical
  } : {
    all: conversations.length,
    low: conversations.filter((conv) => conv.summary?.user_frustration && conv.summary.user_frustration <= 2).length,
    medium: conversations.filter((conv) => conv.summary?.user_frustration === 3).length,
    high: conversations.filter((conv) => conv.summary?.user_frustration === 4).length,
    critical: conversations.filter((conv) => conv.summary?.user_frustration && conv.summary.user_frustration >= 5).length,
  };

  // Filter conversations by frustration level
  const filteredConversations = conversations.filter((conv) => {
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
  });

  const renderFilterButtons = () => (
    <div className="flex gap-2 flex-wrap">
      <Button
        variant={frustrationFilter === 'all' ? 'default' : 'outline'}
        size="sm"
        onClick={() => setFrustrationFilter('all')}
      >
        All ({frustrationCounts.all})
      </Button>
      <Button
        variant={frustrationFilter === 'low' ? 'default' : 'outline'}
        size="sm"
        onClick={() => setFrustrationFilter('low')}
        className={frustrationFilter === 'low' ? 'bg-green-600 hover:bg-green-700' : 'text-green-600 border-green-200 hover:bg-green-50'}
      >
        Low ({frustrationCounts.low})
      </Button>
      <Button
        variant={frustrationFilter === 'medium' ? 'default' : 'outline'}
        size="sm"
        onClick={() => setFrustrationFilter('medium')}
        className={frustrationFilter === 'medium' ? 'bg-blue-600 hover:bg-blue-700' : 'text-blue-600 border-blue-200 hover:bg-blue-50'}
      >
        Medium ({frustrationCounts.medium})
      </Button>
      <Button
        variant={frustrationFilter === 'high' ? 'default' : 'outline'}
        size="sm"
        onClick={() => setFrustrationFilter('high')}
        className={frustrationFilter === 'high' ? 'bg-orange-600 hover:bg-orange-700' : 'text-orange-600 border-orange-200 hover:bg-orange-50'}
      >
        High ({frustrationCounts.high})
      </Button>
      <Button
        variant={frustrationFilter === 'critical' ? 'default' : 'outline'}
        size="sm"
        onClick={() => setFrustrationFilter('critical')}
        className={frustrationFilter === 'critical' ? 'bg-red-600 hover:bg-red-700' : 'text-red-600 border-red-200 hover:bg-red-50'}
      >
        Critical ({frustrationCounts.critical})
      </Button>
    </div>
  );

  const renderConversations = () => (
    <div className="space-y-4" style={{ maxHeight, overflowY: 'auto' }}>
      {filteredConversations.map((conv) => (
        <Link
          key={conv.id}
          to={`/conversations/${conv.id}`}
          className="block p-4 rounded-lg border hover:bg-accent transition-colors"
        >
          <div className="space-y-2">
            <div className="flex items-start justify-between">
              <p className="font-medium text-lg">{conv.summary?.request || 'Untitled Conversation'}</p>
              <span className="text-sm text-muted-foreground">
                {new Date(conv.created_at).toLocaleDateString()}
              </span>
            </div>
            
            <p className="text-sm text-muted-foreground line-clamp-3">
              {conv.summary?.summary || 'No summary available'}
            </p>
            
            {conv.summary?.task && (
              <div className="flex items-center gap-2 text-sm">
                <Target className="h-3 w-3 text-muted-foreground" />
                <span className="line-clamp-1">{conv.summary.task}</span>
              </div>
            )}
            
            <div className="flex flex-wrap items-center gap-3">
              {conv.summary?.languages && conv.summary.languages.length > 0 && (
                <div className="flex items-center gap-1">
                  <Languages className="h-3 w-3 text-muted-foreground" />
                  <div className="flex gap-1">
                    {conv.summary.languages.map((lang, idx) => (
                      <Badge key={idx} variant="secondary" className="text-xs capitalize">
                        {lang}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}
              
              {conv.summary?.user_frustration && (
                <div className="flex items-center gap-1">
                  <AlertTriangle className={cn(
                    "h-4 w-4",
                    conv.summary.user_frustration <= 2 ? "text-green-500" :
                    conv.summary.user_frustration <= 3 ? "text-blue-500" :
                    conv.summary.user_frustration <= 4 ? "text-orange-500" :
                    "text-red-500"
                  )} />
                  <span className="text-sm">Frustration: {conv.summary.user_frustration}/5</span>
                </div>
              )}
              
              {conv.summary?.concerning_score !== null && conv.summary?.concerning_score !== undefined && conv.summary.concerning_score >= 3 && (
                <Badge variant="destructive" className="text-xs">
                  <AlertTriangle className="h-3 w-3 mr-1" />
                  Concern: {conv.summary.concerning_score}/5
                </Badge>
              )}
              
              {conv.summary?.assistant_errors && conv.summary.assistant_errors.length > 0 && (
                <Badge variant="destructive" className="text-xs">
                  <AlertCircle className="h-3 w-3 mr-1" />
                  {conv.summary.assistant_errors.length} error{conv.summary.assistant_errors.length > 1 ? 's' : ''}
                </Badge>
              )}
            </div>
            
            {conv.summary?.assistant_errors && conv.summary.assistant_errors.length > 0 && (
              <div className="mt-2 space-y-1">
                {conv.summary.assistant_errors.slice(0, 2).map((error, idx) => (
                  <p key={idx} className="text-xs text-destructive line-clamp-1">
                    • {error}
                  </p>
                ))}
                {conv.summary.assistant_errors.length > 2 && (
                  <p className="text-xs text-muted-foreground">
                    +{conv.summary.assistant_errors.length - 2} more error{conv.summary.assistant_errors.length - 2 > 1 ? 's' : ''}
                  </p>
                )}
              </div>
            )}
          </div>
        </Link>
      ))}
      {filteredConversations.length === 0 && (
        <div className="text-center py-8 text-muted-foreground">
          No conversations match the selected frustration level.
        </div>
      )}
    </div>
  );

  if (!showCard) {
    return (
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold">{title} ({filteredConversations.length})</h3>
            {description && (
              <p className="text-sm text-muted-foreground">
                {filteredConversations.length === conversations.length 
                  ? description
                  : `Filtered conversations (${filteredConversations.length} of ${conversations.length})`
                }
              </p>
            )}
          </div>
          {renderFilterButtons()}
        </div>
        {renderConversations()}
      </div>
    );
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>{title} ({filteredConversations.length})</CardTitle>
            <CardDescription>
              {filteredConversations.length === conversations.length 
                ? (description || 'All conversations')
                : `Filtered conversations (${filteredConversations.length} of ${conversations.length})`
              }
            </CardDescription>
          </div>
          {renderFilterButtons()}
        </div>
      </CardHeader>
      <CardContent>
        {renderConversations()}
      </CardContent>
    </Card>
  );
} 