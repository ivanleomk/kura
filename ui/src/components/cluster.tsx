import { useState } from "react";
import { Cluster } from "@/types/analytics";
import { ClusterTree } from "./cluster-tree";
import ClusterDetail from "./cluster-details";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import PointVisualisation from "./umap_visualisation";
import { Conversation } from "@/types/conversation";

const getClusterDepth = (clusters: Cluster[]) => {
  const levelMap = new Map<number, Cluster[]>();
  let currentLevel = 0;
  let currentLevelNodes = clusters.filter((item) => item.parent_id === null);

  while (currentLevelNodes.length > 0) {
    levelMap.set(currentLevel, currentLevelNodes);

    const parentIds = currentLevelNodes.map((n) => n.id);
    currentLevelNodes = clusters.filter((item) =>
      parentIds.includes(item.parent_id ?? "")
    );
    currentLevel++;
  }

  return levelMap;
};

const ClusterVisualisation = ({
  clusters,
  conversations,
}: {
  clusters: Cluster[];
  conversations: Conversation[];
}) => {
  const [selectedClusterId, setSelectedClusterId] = useState<string | null>(
    null
  );

  const selectedCluster = clusters.find((c) => c.id === selectedClusterId);

  const updateSelectedCluster = (cluster: Cluster) => {
    setSelectedClusterId(cluster.id);
  };

  const levelMap = getClusterDepth(clusters);

  return (
    <div className="w-full flex flex-col items-center">
      <div className="space-y-1 mb-8 mx-auto text-center">
        <h2 className="text-lg font-medium">Clusters</h2>
        <p className="text-sm text-muted-foreground">
          Visualise your clusters here
        </p>
      </div>

      <div className="w-full px-2" style={{ maxWidth: "1400px" }}>
        <Tabs defaultValue="tree" className="min-h-[600px] w-full">
          <TabsList className="mb-4">
            <TabsTrigger value="tree">Tree View</TabsTrigger>
            <TabsTrigger value="map">Map View</TabsTrigger>
          </TabsList>
          <TabsContent value="tree">
            <div className="flex items-start w-full gap-4">
              <div className="w-2/5">
                <ClusterDetail
                  conversations={conversations}
                  cluster={selectedCluster || null}
                />
              </div>
              <div className="w-3/5">
                <ClusterTree
                  clusters={clusters}
                  selectedClusterId={selectedClusterId}
                  onSelectCluster={updateSelectedCluster}
                  levelMap={levelMap}
                />
              </div>
            </div>
          </TabsContent>
          <TabsContent value="map">
            <div className="h-[600px] w-full border rounded-md">
              <PointVisualisation clusters={clusters} levelMap={levelMap} />
            </div>
          </TabsContent>
        </Tabs>
      </div>

      <div className="py-20" />
    </div>
  );
};

export default ClusterVisualisation;
