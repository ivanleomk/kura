import { z } from "zod";

export const MetadataDictSchema = z.record(
  z.string(),
  z.union([
    z.string(),
    z.number(),
    z.boolean(),
    z.array(z.string()),
    z.array(z.number()),
    z.array(z.boolean()),
  ])
);

export type ConversationMetadata = z.infer<typeof MetadataDictSchema>;

export const MessageSchema = z.object({
  created_at: z.string(),
  role: z.enum(["user", "assistant"]),
  content: z.string(),
});

export const ConversationSchema = z.object({
  chat_id: z.string(),
  created_at: z.string(),
  messages: z.array(MessageSchema),
  metadata: MetadataDictSchema,
});

export const ConversationListSchema = z.array(ConversationSchema);
export type ConversationsList = z.infer<typeof ConversationListSchema>;

export const ConversationSummarySchema = z.object({
  chat_id: z.string(),
  summary: z.string(),
  metadata: MetadataDictSchema,
});

export const ConversationSummaryListSchema = z.array(ConversationSummarySchema);
export type ConversationSummariesList = z.infer<
  typeof ConversationSummaryListSchema
>;

export const ConversationClusterSchema = z.object({
  id: z.string(),
  name: z.string(),
  description: z.string(),
  chat_ids: z.array(z.string()),
  parent_id: z.string().nullable(),
  x_coord: z.number(),
  y_coord: z.number(),
  level: z.number(),
  count: z.number(),
});

export const ConversationClusterListSchema = z.array(ConversationClusterSchema);
export type ConversationClustersList = z.infer<
  typeof ConversationClusterListSchema
>;
