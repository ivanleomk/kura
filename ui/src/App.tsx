import { useState } from "react";

import UploadForm from "./components/upload-form";
import {
  ConversationClustersList,
  ConversationsList,
  ConversationSummariesList,
} from "./types/kura";
import {
  ConversationInfo,
  ConversationInfoSchema,
  ClusterTreeNode,
} from "./types/cluster";
import { buildClusterTree, flattenClusterTree } from "./lib/tree";
import ClusterTree from "./components/cluster-tree";
import ClusterDetails from "./components/cluster-details";
import { Button } from "./components/ui/button";
import { X } from "lucide-react";
import ClusterMap from "./components/cluster-map";

function App() {
  const [conversations, setConversations] = useState<ConversationsList | null>(
    null
  );
  const [summaries, setSummaries] = useState<ConversationSummariesList | null>(
    null
  );
  const [clusters, setClusters] = useState<ConversationClustersList | null>(
    null
  );
  const [conversationMetadataMap, setConversationMetadataMap] = useState<
    Map<string, ConversationInfo>
  >(new Map());

  const [clusterTree, setClusterTree] = useState<ClusterTreeNode | null>(null);
  const [selectedCluster, setSelectedCluster] =
    useState<ClusterTreeNode | null>(null);

  const [flatClusterNodes, setFlatClusterNodes] = useState<ClusterTreeNode[]>(
    []
  );

  const resetVisualisations = () => {
    setConversations(null);
    setSummaries(null);
    setClusters(null);
    setConversationMetadataMap(new Map());
    setClusterTree(null);
    setSelectedCluster(null);
  };

  const handleVisualiseClusters = () => {
    if (!clusters || !conversations) return;
    const metadataMap = new Map<string, ConversationInfo>();
    for (const conversation of conversations) {
      const summary = summaries?.find(
        (sum) => sum.chat_id === conversation.chat_id
      )?.summary;
      if (!summary) {
        throw new Error(
          `No summary found for conversation ${conversation.chat_id}`
        );
      }

      const conversationWithSummary = ConversationInfoSchema.parse({
        ...conversation,
        summary,
      });

      metadataMap.set(conversation.chat_id, conversationWithSummary);
    }

    // Create this so we can quickly compute the cluster metadata
    setConversationMetadataMap(metadataMap);

    // Now we build a tree of clusters
    const clusterTree = buildClusterTree(clusters, null, 0);
    setClusterTree(clusterTree);

    const flatClusterNodes = flattenClusterTree(clusterTree, []);
    setFlatClusterNodes(flatClusterNodes);
  };

  return (
    <div className="min-h-screen flex flex-col">
      {!clusterTree && (
        <div className="p-4 ">
          <UploadForm
            setConversations={setConversations}
            conversations={conversations}
            setSummaries={setSummaries}
            summaries={summaries}
            setClusters={setClusters}
            clusters={clusters}
            handleVisualiseClusters={handleVisualiseClusters}
          />
        </div>
      )}

      {clusterTree && (
        <div className="flex flex-1 h-screen">
          <div className="w-1/3 min-w-[300px] border-r flex flex-col">
            <div className="p-4 border-b">
              <div className="flex justify-between items-center">
                <h2 className="text-lg font-bold">Cluster Hierarchy</h2>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={resetVisualisations}
                  className="text-slate-500 hover:text-slate-700"
                >
                  <X className="h-4 w-4 mr-1" />
                  Reset
                </Button>
              </div>
            </div>
            <div className="p-4 overflow-y-auto h-[40vh] border-b">
              <ClusterTree
                clusterTree={clusterTree}
                onSelectCluster={setSelectedCluster}
              />
            </div>

            {selectedCluster && (
              <div className="flex-1 overflow-y-auto">
                <ClusterDetails
                  selectedCluster={selectedCluster}
                  conversationMetadataMap={conversationMetadataMap}
                />
              </div>
            )}
          </div>
          <div className="flex-1 flex items-center justify-center text-slate-700 font-bold">
            {selectedCluster && clusters && (
              <ClusterMap
                clusters={flatClusterNodes.filter(
                  (item) => item.level == selectedCluster.level
                )}
              />
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
