import { useState } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../lib/api';
import { Card } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Badge } from '../components/ui/badge';
import { Search, AlertCircle, Languages, Target, AlertTriangle } from 'lucide-react';

export default function ConversationsPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [search, setSearch] = useState(searchParams.get('search') || '');
  const [page, setPage] = useState(0);
  const limit = 20;

  const { data, isLoading } = useQuery({
    queryKey: ['conversations', { 
      search,
      cluster_id: searchParams.get('cluster_id'),
      offset: page * limit,
      limit 
    }],
    queryFn: () => apiClient.getConversations({
      search: search || undefined,
      cluster_id: searchParams.get('cluster_id') || undefined,
      offset: page * limit,
      limit,
    }),
  });

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(0);
    if (search) {
      setSearchParams({ search });
    } else {
      setSearchParams({});
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">Conversations</h2>
        <p className="text-muted-foreground">
          Browse and search through all conversations
        </p>
      </div>

      {/* Search Bar */}
      <form onSubmit={handleSearch} className="flex gap-2">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            type="search"
            placeholder="Search conversations..."
            className="pl-10"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        <Button type="submit">Search</Button>
      </form>

      {/* Results */}
      {isLoading ? (
        <div className="flex items-center justify-center h-64">
          <div className="text-muted-foreground">Loading conversations...</div>
        </div>
      ) : (
        <>
          <div className="space-y-4">
            {data?.items.map((conversation) => (
              <Link
                key={conversation.id}
                to={`/conversations/${conversation.id}`}
              >
                <Card className="p-4 hover:bg-accent transition-colors cursor-pointer">
                  <div className="space-y-2">
                    <div className="flex items-start justify-between">
                      <h3 className="font-semibold">
                        {conversation.summary?.request || 'Untitled Conversation'}
                      </h3>
                      <span className="text-sm text-muted-foreground">
                        {new Date(conversation.created_at).toLocaleDateString()}
                      </span>
                    </div>
                    
                    {conversation.summary && (
                      <>
                        <p className="text-sm text-muted-foreground line-clamp-2">
                          {conversation.summary.summary}
                        </p>
                        
                        {conversation.summary.task && (
                          <div className="flex items-center gap-2 text-sm">
                            <Target className="h-3 w-3 text-muted-foreground" />
                            <span className="line-clamp-1">{conversation.summary.task}</span>
                          </div>
                        )}
                        
                        <div className="flex flex-wrap items-center gap-3">
                          {conversation.summary.languages && conversation.summary.languages.length > 0 && (
                            <div className="flex items-center gap-1">
                              <Languages className="h-3 w-3 text-muted-foreground" />
                              <div className="flex gap-1">
                                {conversation.summary.languages.map((lang, idx) => (
                                  <Badge key={idx} variant="secondary" className="text-xs capitalize">
                                    {lang}
                                  </Badge>
                                ))}
                              </div>
                            </div>
                          )}
                          
                          {conversation.summary.user_frustration !== null && conversation.summary.user_frustration !== undefined && (
                            <Badge 
                              variant={conversation.summary.user_frustration >= 3 ? "destructive" : "secondary"}
                              className="text-xs"
                            >
                              Frustration: {conversation.summary.user_frustration}/5
                            </Badge>
                          )}
                          
                          {conversation.summary.concerning_score !== null && conversation.summary.concerning_score !== undefined && conversation.summary.concerning_score >= 3 && (
                            <Badge variant="destructive" className="text-xs">
                              <AlertTriangle className="h-3 w-3 mr-1" />
                              Concern: {conversation.summary.concerning_score}/5
                            </Badge>
                          )}
                          
                          {conversation.summary.assistant_errors && conversation.summary.assistant_errors.length > 0 && (
                            <Badge variant="destructive" className="text-xs">
                              <AlertCircle className="h-3 w-3 mr-1" />
                              {conversation.summary.assistant_errors.length} error{conversation.summary.assistant_errors.length > 1 ? 's' : ''}
                            </Badge>
                          )}
                        </div>
                        
                        {conversation.summary.assistant_errors && conversation.summary.assistant_errors.length > 0 && (
                          <div className="mt-2 space-y-1">
                            {conversation.summary.assistant_errors.slice(0, 2).map((error, idx) => (
                              <p key={idx} className="text-xs text-destructive line-clamp-1">
                                • {error}
                              </p>
                            ))}
                            {conversation.summary.assistant_errors.length > 2 && (
                              <p className="text-xs text-muted-foreground">
                                +{conversation.summary.assistant_errors.length - 2} more error{conversation.summary.assistant_errors.length - 2 > 1 ? 's' : ''}
                              </p>
                            )}
                          </div>
                        )}
                      </>
                    )}
                  </div>
                </Card>
              </Link>
            ))}
          </div>

          {/* Pagination */}
          {data && (
            <div className="flex items-center justify-between">
              <p className="text-sm text-muted-foreground">
                Showing {page * limit + 1} to {Math.min((page + 1) * limit, data.total)} of {data.total} conversations
              </p>
              
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPage(p => Math.max(0, p - 1))}
                  disabled={page === 0}
                >
                  Previous
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPage(p => p + 1)}
                  disabled={!data.has_more}
                >
                  Next
                </Button>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}