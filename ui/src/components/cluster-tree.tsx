import { ClusterTreeNode } from "@/types/cluster";
import { useState } from "react";
import { ChevronRight, ChevronDown } from "lucide-react";

type Props = {
  clusterTree: ClusterTreeNode;
  indent?: number;
  onSelectCluster?: (cluster: ClusterTreeNode) => void;
};

const ClusterTree = ({ clusterTree, indent = 0, onSelectCluster }: Props) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const toggleExpand = () => setIsExpanded(!isExpanded);

  const handleClick = (e: React.MouseEvent) => {
    e.preventDefault();
    toggleExpand();
    if (onSelectCluster) {
      onSelectCluster(clusterTree);
    }
  };

  // Don't render the node itself if it's Root, just its children
  if (clusterTree.name === "Root") {
    return (
      <div className="text-left">
        {clusterTree.children?.map((child: ClusterTreeNode, index: number) => (
          <ClusterTree
            key={child.id || index}
            clusterTree={child}
            indent={0}
            onSelectCluster={onSelectCluster}
          />
        ))}
      </div>
    );
  }

  return (
    <div className="text-left">
      <div
        className="flex items-center hover:bg-slate-100 rounded py-2 cursor-pointer"
        style={{ paddingLeft: `${indent}px` }}
        onClick={handleClick}
      >
        {clusterTree.children && clusterTree.children.length > 0 ? (
          <div className="flex-shrink-0 mr-1">
            {isExpanded ? (
              <ChevronDown className="h-4 w-4 text-slate-500" />
            ) : (
              <ChevronRight className="h-4 w-4 text-slate-500" />
            )}
          </div>
        ) : (
          <div className="w-5" />
        )}
        <div className="font-medium text-wrap">
          {clusterTree.name}
          {clusterTree.count > 0 && (
            <span className="ml-2 text-xs text-slate-500">
              ({clusterTree.count})
            </span>
          )}
        </div>
      </div>

      {isExpanded &&
        clusterTree.children &&
        clusterTree.children.length > 0 && (
          <div className="pl-2 border-l border-slate-200 ml-2">
            {clusterTree.children.map(
              (child: ClusterTreeNode, index: number) => (
                <ClusterTree
                  key={child.id || index}
                  clusterTree={child}
                  indent={indent + 5}
                  onSelectCluster={onSelectCluster}
                />
              )
            )}
          </div>
        )}
    </div>
  );
};

export default ClusterTree;
