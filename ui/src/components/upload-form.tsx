"use client";

import { useState } from "react";
import { analyticsSchema, type Analytics } from "@/types/analytics";
import { Card, CardContent } from "./ui/card";
import UploadDialog from "./upload-dialog";
import {
  Conversation,
  ConversationFile,
  ConversationType,
  conversationTypes,
} from "@/types/conversation";
import { Button } from "./ui/button";
import { ChevronDown, ChevronUp, X } from "lucide-react";
import { Badge } from "./ui/badge";
import { Collapsible } from "@radix-ui/react-collapsible";
import { CollapsibleContent, CollapsibleTrigger } from "./ui/collapsible";
import { Input } from "./ui/input";
import { Label } from "./ui/label";
import { Checkbox } from "./ui/checkbox";

interface UploadButtonProps {
  onSuccess: (data: Analytics) => void;
  resetData: () => void;
  setAllConversations: (conversations: Conversation[]) => void;
}

export function UploadForm({
  onSuccess,
  resetData,
  setAllConversations,
}: UploadButtonProps) {
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [conversations, setConversations] = useState<ConversationFile[]>([]);
  const [isConfigOpen, setIsConfigOpen] = useState(false);

  const [enableCheckpoint, setEnableCheckpoint] = useState(true);
  const [maxClusters, setMaxClusters] = useState<number | null>(null);

  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async () => {
    if (conversations.length === 0) return;
    resetData();

    setIsLoading(true);
    try {
      const jsonData = conversations
        .map((item) => item.conversations)
        .reduce((acc, curr) => acc.concat(curr), []);
        
      const response = await fetch("http://127.0.0.1:8000/api/analyse", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          data: jsonData,
          max_clusters: maxClusters,
          disable_checkpoints: !enableCheckpoint,
        }),
      });

      if (!response.ok) {
        throw new Error("Upload failed");
      }

      const data = await response.json();
      const validatedData = analyticsSchema.parse(data);

      onSuccess(validatedData);
      setAllConversations(jsonData);
    } catch (error) {
      console.error(error);
      alert("Error uploading file");
    } finally {
      setIsLoading(false);
    }
  };

  const addConversations = (conversation: ConversationFile) => {
    if (conversations.find((c) => c.file_name === conversation.file_name)) {
      throw new Error("Conversation was already provided");
    }
    setConversations((prev: ConversationFile[]) => [...prev, conversation]);
  };

  const getBadgeVariant = (type: ConversationType) => {
    switch (type) {
      case "Claude":
        return "default";
      case "OpenAI":
        return "secondary";
      case "Kura":
        return "outline";
      default:
        return "default";
    }
  };

  const removeConversation = (file_name: string) => {
    setConversations((prev: ConversationFile[]) =>
      prev.filter((conversation) => conversation.file_name !== file_name)
    );
  };

  return (
    <Card className="max-w-2xl mx-auto">
      <CardContent className="p-6 space-y-6">
        <UploadDialog
          isDialogOpen={isDialogOpen}
          setIsDialogOpen={setIsDialogOpen}
          addConversations={addConversations}
        />
        <div className="space-y-4">
          {conversations.map((conversation: ConversationFile) => (
            <div
              key={conversation.file_name}
              className="flex items-center justify-between bg-muted/50 p-3 rounded-lg border"
            >
              <div className="flex items-center gap-2">
                <span className="text-sm font-medium">
                  {conversation.file_name}
                </span>
                <Badge
                  variant={getBadgeVariant(conversation.type)}
                  className="font-semibold"
                >
                  {
                    conversationTypes.find((t) => t.value === conversation.type)
                      ?.value
                  }
                </Badge>
              </div>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => removeConversation(conversation.file_name)}
                className="hover:bg-background/80"
              >
                <X className="h-4 w-4" />
              </Button>
            </div>
          ))}
        </div>

        <Collapsible open={isConfigOpen} onOpenChange={setIsConfigOpen}>
          <CollapsibleTrigger asChild>
            <div className="flex items-center justify-between space-x-4 px-1 hover:bg-muted/50 rounded-lg p-4 cursor-pointer">
              <h4 className="text-sm font-semibold">Advanced Configuration</h4>

              {isConfigOpen ? (
                <ChevronUp className="h-4 w-4" />
              ) : (
                <ChevronDown className="h-4 w-4" />
              )}
              <span className="sr-only">Toggle</span>
            </div>
          </CollapsibleTrigger>
          <CollapsibleContent className="space-y-4">
            <div className="grid gap-2">
              <Label htmlFor="max_clusters">Max Clusters</Label>
              <Input
                id="max_clusters"
                placeholder="Enter max clusters"
                value={maxClusters || ""}
                onChange={(e) => setMaxClusters(Number(e.target.value))}
              />
            </div>
            <div className="flex gap-2">
              <Label htmlFor="enable_checkpoint">Enable Checkpoint</Label>
              <Checkbox
                id="enable_checkpoint"
                checked={enableCheckpoint}
                onCheckedChange={() => setEnableCheckpoint(!enableCheckpoint)}
              />
            </div>
          </CollapsibleContent>
        </Collapsible>
        <Button
          className="w-full font-bold border-black border-2 cursor-pointer"
          variant="secondary"
          disabled={conversations.length === 0 || isLoading}
          onClick={handleSubmit}
        >
          {isLoading ? "Loading..." : "Submit for Clustering"}
        </Button>
      </CardContent>
    </Card>
  );
}
