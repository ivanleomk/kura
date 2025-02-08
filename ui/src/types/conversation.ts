import { z } from "zod";

export const MessageSchema = z.object({
  created_at: z.string(),
  role: z.enum(["user", "assistant"]),
  content: z.string(),
});

export const ConversationSchema = z.object({
  chat_id: z.string(),
  created_at: z.string(),
  messages: z.array(MessageSchema),
});

export const ConversationsSchema = z.array(ConversationSchema);

export type Conversation = z.infer<typeof ConversationSchema>;

export type ConversationType = "Claude" | "OpenAI" | "Kura";

export const conversationTypes: { value: ConversationType; label: string }[] = [
  {
    value: "Claude",
    label: "Claude Conversations",
  },
  {
    value: "OpenAI",
    label: "OpenAI Conversations",
  },
  {
    value: "Kura",
    label: "Kura Conversations",
  },
];

export type ConversationFile = {
  type: ConversationType;
  file_name: string;
  conversations: Conversation[];
};
