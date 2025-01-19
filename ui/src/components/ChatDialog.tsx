import { Conversation } from "@/types/conversation";

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "./ui/dialog";
import { Markdown } from "./markdown";

type Props = {
  chatId: string;
  conversation: Conversation;
};

const ChatDialog = ({ chatId, conversation }: Props) => {
  console.log(conversation);
  return (
    <Dialog>
      <DialogTrigger>
        <span className="text-sm text-muted-foreground hover:text-foreground p-2 font-mono border border-2">
          {chatId}
        </span>
      </DialogTrigger>
      <DialogContent className="bg-white max-w-4xl">
        <DialogHeader>
          <DialogTitle>Chat ID: {chatId}</DialogTitle>
        </DialogHeader>
        <DialogDescription className="space-y-4 max-h-[600px] overflow-y-auto px-2 py-4">
          {conversation.messages.map((m, index) => (
            <div
              key={index}
              className={`flex flex-col my-2 ${
                m.role === "user" ? "items-end" : "items-start"
              }`}
            >
              <div
                className={`max-w-[80%] rounded-xl px-4 py-2  ${
                  m.role === "user"
                    ? "bg-blue-500 text-white rounded-br-none"
                    : "bg-gray-200 text-gray-800 rounded-bl-none"
                }`}
              >
                <Markdown>{m.content}</Markdown>
              </div>
              <span className="text-xs text-gray-500 mt-1">
                {m.role === "user" ? "You" : "Assistant"}
              </span>
            </div>
          ))}
        </DialogDescription>
      </DialogContent>
    </Dialog>
  );
};

export default ChatDialog;
