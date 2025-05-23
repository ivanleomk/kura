import { useState, useEffect } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../lib/api';
import { Card } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Search, Filter } from 'lucide-react';

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
                key={conversation.chat_id}
                to={`/conversations/${conversation.chat_id}`}
              >
                <Card className="p-4 hover:bg-accent transition-colors cursor-pointer">
                  <div className="space-y-2">
                    <div className="flex items-start justify-between">
                      <h3 className="font-semibold">
                        {conversation.summary?.title || 'Untitled Conversation'}
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
                        
                        <div className="flex items-center gap-4 text-sm">
                          <span>
                            Language: <span className="font-medium capitalize">
                              {conversation.summary.language}
                            </span>
                          </span>
                          <span>
                            Frustration: <span className="font-medium">
                              {conversation.summary.frustration}/5
                            </span>
                          </span>
                        </div>
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