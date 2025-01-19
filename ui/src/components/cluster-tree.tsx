"use client";

import { useState } from "react";
import { ChevronRight, ChevronDown, FolderTree } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Cluster } from "@/types/analytics";
import { cn } from "@/lib/utils";

interface ClusterTreeProps {
  clusters: Cluster[];
  selectedClusterId: string | null;
  levelMap: Map<number, Cluster[]>;
  onSelectCluster: (cluster: Cluster) => void;
}

interface ClusterTreeItemProps {
  cluster: Cluster;
  allClusters: Cluster[];

  level: number;
  selectedClusterId: string | null;
  onSelectCluster: (cluster: Cluster) => void;
  levelMap: Map<number, Cluster[]>;
}

function ClusterTreeItem({
  cluster,
  allClusters,
  level,
  selectedClusterId,
  levelMap,
  onSelectCluster,
}: ClusterTreeItemProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const childClusters = allClusters.filter((c) => c.parent_id === cluster.id);

  const total_count =
    levelMap.get(level)?.reduce((acc, curr) => acc + curr.count, 0) || 0;
  const percentage = (cluster.count / total_count) * 100;

  return (
    <div className="text-md text-left">
      <div
        className={cn(
          "flex items-center gap-2 py-2 px-3 hover:bg-accent/50 rounded-md cursor-pointer transition-colors duration-200 ",
          selectedClusterId === cluster.id
            ? "bg-accent text-accent-foreground"
            : ""
        )}
        style={{ paddingLeft: `${level * 30 + 12}px` }}
        onClick={() => onSelectCluster(cluster)}
      >
        {childClusters.length > 0 ? (
          <Button
            variant="ghost"
            size="sm"
            className="h-4 w-4 p-0 hover:bg-transparent"
            onClick={(e) => {
              e.stopPropagation();
              setIsExpanded(!isExpanded);
            }}
          >
            {isExpanded ? (
              <ChevronDown className="h-3 w-3" />
            ) : (
              <ChevronRight className="h-3 w-3" />
            )}
          </Button>
        ) : (
          <div className="w-4" />
        )}
        <div className="flex justify-between w-full">
          <span className="flex-1 font-medium max-w-lg">{cluster.name}</span>
          <span className="text-xs text-muted-foreground whitespace-nowrap">
            {cluster.count.toLocaleString()} items | {percentage.toFixed(2)}%
          </span>
        </div>
      </div>
      {isExpanded &&
        childClusters.map((child) => (
          <ClusterTreeItem
            conversations={conversations}
            key={child.id}
            cluster={child}
            allClusters={allClusters}
            level={level + 1}
            selectedClusterId={selectedClusterId}
            levelMap={levelMap}
            onSelectCluster={onSelectCluster}
          />
        ))}
    </div>
  );
}

export function ClusterTree({
  clusters,
  selectedClusterId,
  onSelectCluster,
  levelMap,
}: ClusterTreeProps) {
  const rootClusters = levelMap.get(0) || [];

  return (
    <div className="h-full flex flex-col">
      <div className="flex items-center gap-2 p-4 border-b">
        <FolderTree className="h-5 w-5 text-primary" />
        <h2 className="font-semibold">Cluster Hierarchy</h2>
      </div>
      <ScrollArea className="flex-1 p-2">
        <div className="space-y-0.5">
          {rootClusters.map((cluster) => (
            <ClusterTreeItem
              key={cluster.id}
              cluster={cluster}
              levelMap={levelMap}
              allClusters={clusters}
              level={0}
              selectedClusterId={selectedClusterId}
              onSelectCluster={onSelectCluster}
            />
          ))}
        </div>
      </ScrollArea>
    </div>
  );
}
