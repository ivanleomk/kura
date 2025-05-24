import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ChevronRight, ChevronDown, Network, AlertTriangle } from 'lucide-react';
import type { ClusterTreeNode } from '../lib/api';
import { cn } from '../lib/utils';
import { Button } from './ui/button';

interface ClusterTreeProps {
  clusters: ClusterTreeNode[];
}

interface TreeNodeProps {
  node: ClusterTreeNode;
  level: number;
  totalConversations: number;
}

function TreeNode({ node, level, totalConversations }: TreeNodeProps) {
  const navigate = useNavigate();
  const [isExpanded, setIsExpanded] = useState(level < 2);
  const hasChildren = node.children && node.children.length > 0;

  const frustrationColor = () => {
    if (!node.avg_frustration) return '';
    if (node.avg_frustration <= 2) return 'text-green-600';
    if (node.avg_frustration <= 3) return 'text-blue-600';
    if (node.avg_frustration <= 4) return 'text-orange-600';
    return 'text-red-600';
  };

  const satisfactionColor = () => {
    if (!node.avg_frustration) return '';
    const satisfaction = 5 - node.avg_frustration;
    if (satisfaction >= 3) return 'text-green-600';
    if (satisfaction >= 2) return 'text-blue-600';
    if (satisfaction >= 1) return 'text-orange-600';
    return 'text-red-600';
  };

  const conversationPercentage = totalConversations > 0 ? ((node.conversation_count || 0) / totalConversations) * 100 : 0;
  const meanSatisfaction = node.avg_frustration ? 5 - node.avg_frustration : null;

  return (
    <div className="select-none">
      <div
        className={cn(
          'flex items-center gap-2 py-2 px-3 rounded-lg hover:bg-accent cursor-pointer transition-colors',
          'group'
        )}
        style={{ paddingLeft: `${level * 24 + 12}px` }}
        onClick={() => navigate(`/clusters/${node.id}`)}
      >
        {hasChildren && (
          <Button
            variant="ghost"
            size="sm"
            className="h-6 w-6 p-0"
            onClick={(e) => {
              e.stopPropagation();
              setIsExpanded(!isExpanded);
            }}
          >
            {isExpanded ? (
              <ChevronDown className="h-4 w-4" />
            ) : (
              <ChevronRight className="h-4 w-4" />
            )}
          </Button>
        )}
        {!hasChildren && <div className="w-6" />}

        <Network className="h-4 w-4 text-muted-foreground" />

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className="font-medium truncate">{node.name}</span>
            {node.avg_frustration && node.avg_frustration > 3.5 && (
              <AlertTriangle className={cn('h-3 w-3', frustrationColor())} />
            )}
          </div>
          <p className="text-sm text-muted-foreground truncate">
            {node.description}
          </p>

          {/* Conversation percentage bar */}
          <div className="mt-2 flex items-center gap-2">
            <div className="flex-1 bg-gray-200 rounded-full h-2">
              <div
                className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                style={{ width: `${Math.min(conversationPercentage, 100)}%` }}
              />
            </div>
            <span className="text-xs text-muted-foreground min-w-0">
              {conversationPercentage.toFixed(1)}%
            </span>
          </div>
        </div>

        <div className="flex items-center gap-4 text-sm">
          <span className="text-muted-foreground">
            {node.conversation_count}
          </span>
          {meanSatisfaction && (
            <div className="flex flex-col items-end">
              <span className={cn('font-medium text-xs', frustrationColor())}>
                {node.avg_frustration!.toFixed(1)}/5
              </span>
            </div>
          )}
        </div>
      </div>

      {hasChildren && isExpanded && (
        <div>
          {node.children.map((child) => (
            <TreeNode key={child.id} node={child} level={level + 1} totalConversations={totalConversations} />
          ))}
        </div>
      )}
    </div>
  );
}

export default function ClusterTree({ clusters }: ClusterTreeProps) {
  const [expandAll, setExpandAll] = useState(false);

  // Force re-render with all expanded/collapsed
  const [key, setKey] = useState(0);

  // Function to recursively sort nodes by conversation count
  const sortNodesByConversationCount = (nodes: ClusterTreeNode[]): ClusterTreeNode[] => {
    return nodes
      .map(node => ({
        ...node,
        ...(node.children && { children: sortNodesByConversationCount(node.children) })
      }))
      .sort((a, b) => (b.conversation_count || 0) - (a.conversation_count || 0));
  };

  // Sort clusters by conversation count
  const sortedClusters = sortNodesByConversationCount(clusters);

  // Calculate total conversations across all clusters
  const calculateTotalConversations = (nodes: ClusterTreeNode[]): number => {
    return nodes.reduce((total, node) => {
      const nodeConversations = node.conversation_count || 0;
      const childrenConversations = node.children ? calculateTotalConversations(node.children) : 0;
      return total + nodeConversations + childrenConversations;
    }, 0);
  };

  const totalConversations = calculateTotalConversations(clusters);

  const handleExpandAll = () => {
    setExpandAll(!expandAll);
    setKey(prev => prev + 1);
  };

  return (
    <div className="space-y-4">
      <div className="flex justify-end">
        <Button
          variant="outline"
          size="sm"
          onClick={handleExpandAll}
          className="text-xs"
        >
          {expandAll ? 'Collapse All' : 'Expand All'}
        </Button>
      </div>

      <div className="border rounded-lg p-4" key={key}>
        {sortedClusters.map((cluster) => (
          <TreeNode key={cluster.id} node={cluster} level={0} totalConversations={totalConversations} />
        ))}
      </div>
    </div>
  );
}
