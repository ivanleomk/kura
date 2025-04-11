import {
  ConversationClustersList,
  ConversationsList,
  ConversationSummariesList,
} from "@/types/kura";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "./ui/card";
import { Input } from "./ui/input";
import {
  parseConversationClusterFile,
  parseConversationFile,
  parseConversationSummaryFile,
} from "@/lib/parse";
import { Button } from "./ui/button";

type UploadFormProps = {
  setConversations: (conversations: ConversationsList) => void;
  conversations: ConversationsList | null;
  setSummaries: (summaries: ConversationSummariesList) => void;
  summaries: ConversationSummariesList | null;
  setClusters: (clusters: ConversationClustersList) => void;
  clusters: ConversationClustersList | null;
  handleVisualiseClusters: () => void;
};

const UploadForm = ({
  setConversations,
  conversations,
  setSummaries,
  summaries,
  setClusters,
  clusters,
  handleVisualiseClusters,
}: UploadFormProps) => {
  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;

    if (!files) return;

    for (const file of files) {
      if (file.name === "conversations.json") {
        console.log("Parsing conversation file");
        const conversations = await parseConversationFile(file);
        if (conversations) {
          setConversations(conversations);
        }
      }

      if (file.name === "summaries.jsonl") {
        console.log("Parsing conversation summary file");
        const summaries = await parseConversationSummaryFile(file);
        if (summaries) {
          setSummaries(summaries);
        }
      }

      if (file.name === "dimensionality.jsonl") {
        console.log("Parsing conversation cluster file");
        const clusters = await parseConversationClusterFile(file);
        if (clusters) {
          setClusters(clusters);
        }
      }
    }
  };
  return (
    <Card className="max-w-2xl mx-auto mt-10">
      <CardHeader>
        <CardTitle>Load Checkpoint</CardTitle>
        <CardDescription>
          Select the checkpoint directory created by Kura{" "}
        </CardDescription>
      </CardHeader>
      <CardContent>
        <Input
          type="file"
          multiple
          //@ts-ignore
          webkitdirectory=""
          className="cursor-pointer"
          accept=""
          onChange={handleFileChange}
        />
        <div className="mt-4 text-left text-muted-foreground text-sm">
          {conversations && summaries && clusters && (
            <div>
              <p>
                Loaded in {conversations.length} conversations,{" "}
                {summaries?.length} summaries, {clusters?.length} clusters
              </p>
              <Button className="w-full mt-4" onClick={handleVisualiseClusters}>
                Visualise Clusters
              </Button>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
};

export default UploadForm;
