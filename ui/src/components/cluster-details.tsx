import { ClusterTreeNode, ConversationInfo } from "../types/cluster";
import { useState } from "react";
import ConversationDialog from "./conversation-dialog";

interface ClusterDetailsProps {
  selectedCluster: ClusterTreeNode | null;
  conversationMetadataMap: Map<string, ConversationInfo>;
}

interface MetadataSummaryProps {
  aggregatedMetadata: Record<string, any[]>;
}

function MetadataSummary({ aggregatedMetadata }: MetadataSummaryProps) {
  const [aggregationMode, setAggregationMode] = useState<"individual" | "list">(
    "individual"
  );

  if (Object.keys(aggregatedMetadata).length === 0) return null;

  return (
    <div className="mt-3 border-t pt-2">
      <div className="flex justify-between items-center mb-2">
        <h4 className="text-xs font-semibold">Metadata Summary</h4>
        <div className="flex items-center gap-2">
          <span className="text-xs text-slate-600">Aggregation:</span>
          <button
            onClick={() => setAggregationMode("individual")}
            className={`text-xs px-2 py-0.5 rounded ${
              aggregationMode === "individual"
                ? "bg-blue-100 text-blue-800"
                : "bg-slate-100 text-slate-600"
            }`}
          >
            Individual
          </button>
          <button
            onClick={() => setAggregationMode("list")}
            className={`text-xs px-2 py-0.5 rounded ${
              aggregationMode === "list"
                ? "bg-blue-100 text-blue-800"
                : "bg-slate-100 text-slate-600"
            }`}
          >
            List
          </button>
        </div>
      </div>
      <div className="grid grid-cols-2 gap-2">
        {Object.entries(aggregatedMetadata).map(([key, values]) => {
          // Count occurrences based on aggregation mode
          const valueCounts = values.reduce(
            (acc: Record<string, number>, val: any) => {
              if (Array.isArray(val) && aggregationMode === "individual") {
                // For individual mode, count each item in the array separately
                val.forEach((item: any) => {
                  const itemStr = String(item);
                  acc[itemStr] = (acc[itemStr] || 0) + 1;
                });
              } else {
                // For list mode or non-array values, count the whole value
                const valueStr = Array.isArray(val)
                  ? val.join(", ")
                  : String(val);
                acc[valueStr] = (acc[valueStr] || 0) + 1;
              }
              return acc;
            },
            {}
          );

          return (
            <div key={key} className="text-xs">
              <span className="font-medium">{key}:</span>{" "}
              <div className="flex flex-wrap gap-1 mt-1">
                {Object.entries(valueCounts).map(([value, count]) => (
                  <div
                    key={`${key}-${value}`}
                    className="inline-flex items-center border rounded-full px-2 py-0.5 bg-slate-100 text-slate-800 text-[10px]"
                  >
                    {value}
                    <span className="ml-1 text-slate-500">({count})</span>
                  </div>
                ))}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

export default function ClusterDetails({
  selectedCluster,
  conversationMetadataMap,
}: ClusterDetailsProps) {
  const [selectedConversation, setSelectedConversation] =
    useState<ConversationInfo | null>(null);
  const [isDialogOpen, setIsDialogOpen] = useState(false);

  if (!selectedCluster) return null;

  // Count chats that exist in the metadata map
  // Get the actual conversation objects from the metadata map
  const chats = selectedCluster.chat_ids?.map((id: string) => {
    return conversationMetadataMap.get(id);
  });

  const aggregatedMetadata = chats.reduce(
    (acc: Record<string, any[]>, chat: ConversationInfo | undefined) => {
      if (!chat || !chat.metadata) return acc;

      // Iterate through each metadata key-value pair
      Object.entries(chat.metadata).forEach(([key, value]) => {
        if (!acc[key]) {
          // Initialize the array for this key
          acc[key] = [];
        }

        // If the value is already an array, store it as a nested array
        if (Array.isArray(value)) {
          acc[key].push(value);
        } else {
          // For primitive types (string, number, boolean), add to array
          acc[key].push(value);
        }
      });

      return acc;
    },
    {}
  );

  const handleConversationClick = (conversation: ConversationInfo) => {
    setSelectedConversation(conversation);
    setIsDialogOpen(true);
  };

  return (
    <div className="flex-1 p-4 overflow-y-auto h-[50vh]">
      <h3 className="text-sm font-semibold mb-2">Cluster Details</h3>
      <div className="rounded-md">
        <p className="font-medium">{selectedCluster.name}</p>
        {selectedCluster.description && (
          <p className="text-xs text-slate-600 mt-1">
            {selectedCluster.description}
          </p>
        )}
        <div className="flex space-x-4 mt-2">
          <p className="text-xs text-slate-600">
            <span className="font-medium">Level:</span> {selectedCluster.level}
          </p>
        </div>
        {selectedCluster.id && (
          <p className="text-xs text-slate-500 mt-1">
            ID: {selectedCluster.id}
          </p>
        )}
        <p className="text-xs text-slate-500 mt-1">
          {selectedCluster.chat_ids?.length} chats
        </p>

        {/* Metadata summary section */}
        <MetadataSummary aggregatedMetadata={aggregatedMetadata} />

        <div className="mt-3 space-y-2 ">
          {chats.map((item: ConversationInfo) => (
            <div
              key={item.chat_id}
              className="p-2 border rounded-md cursor-pointer hover:bg-slate-50 transition-colors"
              onClick={() => handleConversationClick(item)}
            >
              <p className="text-xs mb-3 text-slate-500 mt-1">
                ID: {item.chat_id}
              </p>
              <p className="text-xs font-medium text-wrap">{item.summary}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Conversation Dialog */}
      {selectedConversation && (
        <ConversationDialog
          conversation={selectedConversation}
          isOpen={isDialogOpen}
          onOpenChange={setIsDialogOpen}
        />
      )}
    </div>
  );
}
