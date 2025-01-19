import { Dialog } from "@radix-ui/react-dialog";
import {
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "./ui/dialog";
import { Button } from "./ui/button";
import { Plus } from "lucide-react";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "./ui/select";
import { useEffect, useState } from "react";
import { Label } from "./ui/label";
import { Input } from "./ui/input";
import {
  ConversationsSchema,
  ConversationType,
  conversationTypes,
} from "@/types/conversation";
import { ConversationFile } from "@/types/conversation";

type Props = {
  isDialogOpen: boolean;
  setIsDialogOpen: (isDialogOpen: boolean) => void;
  addConversations: (conversations: ConversationFile) => void;
};

const UploadDialog = ({
  isDialogOpen,
  setIsDialogOpen,
  addConversations,
}: Props) => {
  const [selectedType, setSelectedType] = useState<ConversationType>("Claude");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  const [error, setError] = useState<string | null>(null);

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) {
      setError("Please select a file");
      return;
    }

    if (file.type !== "application/json") {
      setError("Please upload a JSON file");
      return;
    }

    setSelectedFile(file);
  };

  const parseConversations = (file: File) => {
    if (selectedType === "Claude") {
      file.text().then((text) => {
        try {
          const jsonData = JSON.parse(text);
          const conversations = jsonData.map((conversation: any) => {
            return {
              chat_id: conversation["uuid"],
              created_at: conversation["created_at"],
              messages: conversation["chat_messages"]
                .sort((a: any, b: any) => {
                  return (
                    new Date(a["created_at"]).getTime() -
                    new Date(b["created_at"]).getTime()
                  );
                })
                .map((message: any) => {
                  return {
                    created_at: message["created_at"],
                    role: message["sender"] === "human" ? "user" : "assistant",
                    content: message["content"]
                      .filter((item: any) => item["type"] === "text")
                      .map((item: any) => item["text"])
                      .join("\n"),
                  };
                }),
            };
          });
          const parsedConversations = ConversationsSchema.parse(conversations);
          addConversations({
            type: "Claude",
            file_name: file.name,
            conversations: parsedConversations,
          });
          setIsDialogOpen(false);
        } catch (error) {
          console.log(error);
          setError(
            "Unable to parse the conversations file. The file is either not in the correct format or has previously been added to the list of files"
          );
        }
      });
    } else if (selectedType === "Kura") {
      file.text().then((text) => {
        try {
          const jsonData = JSON.parse(text);
          const conversations = jsonData;
          const parsedConversations = ConversationsSchema.parse(conversations);
          addConversations({
            type: "Kura",
            file_name: file.name,
            conversations: parsedConversations,
          });
          setIsDialogOpen(false);
        } catch (error) {
          console.log(error);
        }
      });
    } else {
      setError("OpenAI conversations are not supported yet");
    }
  };

  const handleAddConversations = () => {
    if (selectedFile) {
      setError(null);
      parseConversations(selectedFile);
    }
  };

  useEffect(() => {
    if (selectedFile) {
      setError(null);
    }
  }, [selectedFile]);

  return (
    <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
      <DialogTrigger asChild>
        <Button variant="outline" className="w-full border-2">
          <Plus className="mr-2 h-4 w-4" />
          Add Conversations
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-lg bg-white">
        <DialogHeader>
          <DialogTitle>Add Conversations</DialogTitle>
        </DialogHeader>
        <div className="flex flex-col gap-4">
          <p>Select the type of conversations you want to upload</p>
        </div>
        <div className="space-y-4 pt-4">
          <Select
            value={selectedType}
            onValueChange={(value) =>
              setSelectedType(value as ConversationType)
            }
          >
            <SelectTrigger className="w-full">
              <SelectValue placeholder="Select conversation type" />
            </SelectTrigger>
            <SelectContent>
              {conversationTypes.map((type) => (
                <SelectItem key={type.value} value={type.value}>
                  {type.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <div className="grid w-full items-center gap-1.5">
            <Label htmlFor="conversations">Conversations</Label>
            <Input
              id="conversations"
              type="file"
              multiple
              className="cursor-pointer"
              onChange={handleFileSelect}
              disabled={!selectedType}
            />
          </div>
        </div>
        <div className="flex justify-center items-center">
          <p className="text-sm text-red-500">{error}</p>
        </div>
        <Button
          className="w-full"
          onClick={handleAddConversations}
          disabled={!selectedFile || !selectedType}
        >
          Add
        </Button>
      </DialogContent>
    </Dialog>
  );
};

export default UploadDialog;
