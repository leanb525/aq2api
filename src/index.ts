/**
 * Amazon Q to OpenAI API Bridge - Cloudflare Worker
 *
 * This worker provides OpenAI and Anthropic compatible endpoints
 * that proxy requests to Amazon Q API.
 */

// Environment variables interface
export interface Env {
  // KV Namespace for storing credentials (optional)
  CREDENTIALS: KVNamespace;

  // Credentials can be set as environment variables
  CLIENT_ID?: string;
  CLIENT_SECRET?: string;
  REFRESH_TOKEN?: string;
  ACCESS_TOKEN?: string;

  // Configuration
  AMAZONQ_ENDPOINT?: string;
  SSO_OIDC_ENDPOINT?: string;
  LOG_REQUESTS?: string;
  LOG_RESPONSES?: string;
  TOKEN_REFRESH_MARGIN?: string;
}

// Constants
const AMAZONQ_ENDPOINT = "https://codewhisperer.us-east-1.amazonaws.com";
const SSO_OIDC_ENDPOINT = "https://oidc.us-east-1.amazonaws.com";
const ANTHROPIC_API_VERSION = "2023-06-01";
const STREAM_CHUNK_SIZE = 1024;
const BUFFER_MAX_SIZE = 10240;
const TOKEN_REFRESH_MARGIN = 300; // seconds

// Client detection hints for forced streaming
const STREAMING_USER_AGENT_HINTS = [
  "claudecode",
  "claude code",
  "claude-code",
  "anthropic/ide",
  "anthropic-ide",
  "anthropic-client",
  "amazon q developer",
  "amazonq-ide",
];

// Utility functions
function parseBoolean(value: string | undefined): boolean | undefined {
  if (!value) return undefined;
  const normalized = value.trim().toLowerCase();
  if (["1", "true", "yes", "on"].includes(normalized)) return true;
  if (["0", "false", "no", "off"].includes(normalized)) return false;
  return undefined;
}

function normalizeStreamFlag(value: any): boolean | undefined {
  if (value === null || value === undefined) return undefined;
  if (typeof value === "boolean") return value;
  if (typeof value === "number") return Boolean(value);
  if (typeof value === "string") {
    const val = value.trim().toLowerCase();
    if (!val) return undefined;
    if (["true", "1", "yes", "on", "sse", "stream", "delta"].includes(val)) return true;
    if (["false", "0", "no", "off"].includes(val)) return false;
    return undefined;
  }
  if (typeof value === "object") {
    for (const key of ["type", "mode", "format", "value", "enabled"]) {
      if (key in value) {
        const normalized = normalizeStreamFlag(value[key]);
        if (normalized !== undefined) return normalized;
      }
    }
    return undefined;
  }
  return Boolean(value);
}

function generateId(prefix: string = "id"): string {
  return `${prefix}_${crypto.randomUUID().replace(/-/g, "").substring(0, 16)}`;
}

// Authentication Manager
class AmazonQAuthManager {
  private env: Env;
  private credentials: any;

  constructor(env: Env) {
    this.env = env;
    this.credentials = null;
  }

  async loadCredentials(): Promise<void> {
    // Try to load from KV first
    if (this.env.CREDENTIALS) {
      try {
        const stored = await this.env.CREDENTIALS.get("credentials", "json");
        if (stored) {
          this.credentials = stored;
          return;
        }
      } catch (e) {
        console.error("Failed to load credentials from KV:", e);
      }
    }

    // Fall back to environment variables
    this.credentials = {
      client_id: this.env.CLIENT_ID,
      client_secret: this.env.CLIENT_SECRET,
      refresh_token: this.env.REFRESH_TOKEN,
      access_token: this.env.ACCESS_TOKEN,
    };
  }

  async saveCredentials(): Promise<void> {
    if (this.env.CREDENTIALS && this.credentials) {
      try {
        await this.env.CREDENTIALS.put("credentials", JSON.stringify(this.credentials));
      } catch (e) {
        console.error("Failed to save credentials to KV:", e);
      }
    }
  }

  async refreshAccessToken(): Promise<string> {
    if (!this.credentials?.refresh_token) {
      throw new Error("No refresh_token available");
    }

    const url = `${this.env.SSO_OIDC_ENDPOINT || SSO_OIDC_ENDPOINT}/token`;
    const payload = {
      grantType: "refresh_token",
      refreshToken: this.credentials.refresh_token,
      clientId: this.credentials.client_id,
      clientSecret: this.credentials.client_secret,
    };

    console.log("Refreshing access token...");

    const response = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error("Token refresh failed:", response.status, errorText);
      throw new Error(`Token refresh failed: ${response.status} ${errorText}`);
    }

    const data = await response.json<any>();
    this.credentials.access_token = data.accessToken;
    this.credentials.expires_in = data.expiresIn;

    await this.saveCredentials();

    console.log("Access token refreshed successfully");
    return this.credentials.access_token;
  }

  async getAccessToken(): Promise<string> {
    if (!this.credentials) {
      await this.loadCredentials();
    }

    if (!this.credentials?.access_token) {
      return await this.refreshAccessToken();
    }

    return this.credentials.access_token;
  }

  async setCredentials(newCredentials: any): Promise<void> {
    this.credentials = {
      ...this.credentials,
      ...newCredentials,
    };
    await this.saveCredentials();
  }
}

// Amazon Q Client
class AmazonQClient {
  private authManager: AmazonQAuthManager;
  private endpoint: string;

  constructor(authManager: AmazonQAuthManager, env: Env) {
    this.authManager = authManager;
    this.endpoint = env.AMAZONQ_ENDPOINT || AMAZONQ_ENDPOINT;
  }

  private async getHeaders(): Promise<Record<string, string>> {
    const accessToken = await this.authManager.getAccessToken();
    return {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${accessToken}`,
      "x-amzn-codewhisperer-optout": "false",
    };
  }

  async sendMessage(
    message: string,
    conversationId: string | null,
    modelId: string = "claude-sonnet-4.5",
    stream: boolean = false,
    retryOnAuthError: boolean = true
  ): Promise<Response> {
    const convId = conversationId || generateId("conv");
    const url = `${this.endpoint}/generateAssistantResponse`;

    const payload = {
      conversationState: {
        chatTriggerType: "MANUAL",
        conversationId: convId,
        currentMessage: {
          userInputMessage: {
            content: message,
            images: [],
            modelId: modelId,
            origin: "IDE",
            userInputMessageContext: {
              editorState: {
                useRelevantDocuments: false,
                workspaceFolders: [],
              },
              envState: {
                operatingSystem: "linux",
              },
            },
          },
        },
        history: [],
      },
    };

    let headers = await this.getHeaders();

    console.log("Sending request to Amazon Q:", url);

    let response = await fetch(url, {
      method: "POST",
      headers,
      body: JSON.stringify(payload),
    });

    // Handle 403 errors by refreshing token
    if (response.status === 403 && retryOnAuthError) {
      console.warn("Received 403, refreshing token and retrying...");
      try {
        await this.authManager.refreshAccessToken();
        headers = await this.getHeaders();
        response = await fetch(url, {
          method: "POST",
          headers,
          body: JSON.stringify(payload),
        });
      } catch (e) {
        console.error("Token refresh failed:", e);
      }
    }

    if (!response.ok) {
      const errorText = await response.text();
      console.error("Amazon Q request failed:", response.status, errorText);
      throw new Error(`Amazon Q request failed: ${response.status}`);
    }

    return response;
  }
}

// Format Converter
class OpenAIConverter {
  static messagesToContent(messages: any[]): string {
    for (let i = messages.length - 1; i >= 0; i--) {
      const msg = messages[i];
      if (msg.role === "user") {
        const content = msg.content;

        // Handle Anthropic format (content is array)
        if (Array.isArray(content)) {
          const textParts: string[] = [];
          for (const item of content) {
            if (item.type === "text") {
              textParts.push(item.text || "");
            }
          }
          return textParts.join(" ");
        }

        // Handle OpenAI format (content is string)
        return content || "";
      }
    }
    return "";
  }

  static extractJsonFromBuffer(buffer: string): [string | null, string] {
    const startPattern = '{"content":';
    const start = buffer.indexOf(startPattern);

    if (start === -1) {
      return [null, buffer];
    }

    let depth = 0;
    let inString = false;
    let escapeNext = false;

    for (let i = start; i < buffer.length; i++) {
      const char = buffer[i];

      if (escapeNext) {
        escapeNext = false;
        continue;
      }

      if (char === "\\") {
        escapeNext = true;
        continue;
      }

      if (char === '"') {
        inString = !inString;
      }

      if (!inString) {
        if (char === "{") {
          depth++;
        } else if (char === "}") {
          depth--;
          if (depth === 0) {
            return [buffer.substring(start, i + 1), buffer.substring(i + 1)];
          }
        }
      }
    }

    return [null, buffer];
  }

  static parseEventStream(rawResponse: string): string {
    const contents: string[] = [];
    let remaining = rawResponse;

    while (true) {
      const [jsonStr, newRemaining] = this.extractJsonFromBuffer(remaining);
      remaining = newRemaining;

      if (!jsonStr) break;

      try {
        const obj = JSON.parse(jsonStr);
        if (obj.content && typeof obj.content === "string") {
          contents.push(obj.content);
        }
      } catch (e) {
        // Skip invalid JSON
      }
    }

    if (contents.length > 0) {
      return contents.join("");
    }

    // Fallback: return printable lines
    const printableLines: string[] = [];
    for (const line of remaining.split("\n")) {
      const stripped = line.trim();
      if (stripped && !stripped.startsWith(":")) {
        printableLines.push(stripped);
      }
    }
    return printableLines.join("\n");
  }

  static amazonqToOpenaiResponse(
    amazonqRawResponse: string,
    model: string,
    conversationId: string
  ): any {
    const content = this.parseEventStream(amazonqRawResponse);

    return {
      id: `chatcmpl-${conversationId.substring(0, 8)}`,
      object: "chat.completion",
      created: Math.floor(Date.now() / 1000),
      model: model,
      choices: [
        {
          index: 0,
          message: {
            role: "assistant",
            content: content,
          },
          finish_reason: "stop",
        },
      ],
      usage: {
        prompt_tokens: 0,
        completion_tokens: 0,
        total_tokens: 0,
      },
    };
  }

  static createStreamChunk(
    content: string,
    model: string,
    chunkType: string = "content",
    formatType: string = "openai",
    messageId?: string,
    finalText?: string
  ): string {
    if (formatType === "anthropic") {
      const msgId = messageId || generateId("msg");
      let eventName = "";
      let chunk: any;

      if (chunkType === "start") {
        eventName = "message_start";
        chunk = {
          type: "message_start",
          message: {
            id: msgId,
            type: "message",
            role: "assistant",
            content: [],
            model: model,
            stop_reason: null,
            stop_sequence: null,
            usage: { input_tokens: 0, output_tokens: 0 },
          },
        };
      } else if (chunkType === "content_start") {
        eventName = "content_block_start";
        chunk = {
          type: "content_block_start",
          index: 0,
          content_block: { type: "text", text: "" },
        };
      } else if (chunkType === "content") {
        eventName = "content_block_delta";
        chunk = {
          type: "content_block_delta",
          index: 0,
          delta: { type: "text_delta", text: content },
        };
      } else if (chunkType === "content_end") {
        eventName = "content_block_stop";
        chunk = { type: "content_block_stop", index: 0 };
      } else if (chunkType === "end") {
        eventName = "message_delta";
        chunk = {
          type: "message_delta",
          delta: { stop_reason: "end_turn", stop_sequence: null },
          usage: { output_tokens: 0 },
        };
      } else {
        eventName = "message_stop";
        chunk = {
          type: "message_stop",
          message: {
            id: msgId,
            type: "message",
            role: "assistant",
            model: model,
            content: [{ type: "text", text: finalText || "" }],
            stop_reason: "end_turn",
            stop_sequence: null,
            usage: { input_tokens: 0, output_tokens: 0 },
          },
        };
      }

      const prefix = eventName ? `event: ${eventName}\n` : "";
      return `${prefix}data: ${JSON.stringify(chunk)}\n\n`;
    } else {
      // OpenAI format
      let delta: any = {};
      if (chunkType === "start") {
        delta = { role: "assistant", content: "" };
      } else if (chunkType === "content") {
        delta = { content: content };
      }

      const chunk = {
        id: generateId("chatcmpl"),
        object: "chat.completion.chunk",
        created: Math.floor(Date.now() / 1000),
        model: model,
        choices: [
          {
            index: 0,
            delta: delta,
            finish_reason: chunkType === "end" ? "stop" : null,
          },
        ],
      };

      return `data: ${JSON.stringify(chunk)}\n\n`;
    }
  }
}

// Main request handler
async function handleChatRequest(
  request: Request,
  env: Env,
  formatType: "openai" | "anthropic"
): Promise<Response> {
  try {
    const data = await request.json<any>();

    const messages = data.messages || [];
    const model = data.model || "claude-sonnet-4.5";

    // Determine if streaming is needed
    let stream = normalizeStreamFlag(data.stream);

    if (stream === undefined || stream === null) {
      const url = new URL(request.url);
      stream = normalizeStreamFlag(url.searchParams.get("stream"));
    }

    if (stream === undefined || stream === null) {
      for (const key of ["response_mode", "responseMode", "response_format", "responseFormat"]) {
        stream = normalizeStreamFlag(data[key]);
        if (stream !== undefined && stream !== null) break;
      }
    }

    if (stream === undefined || stream === null) {
      if (formatType === "anthropic") {
        stream = true;
      } else {
        const acceptHeader = request.headers.get("Accept") || "";
        if (acceptHeader.toLowerCase().includes("text/event-stream")) {
          stream = true;
        }
      }
    }

    if (!stream) {
      const userAgent = (request.headers.get("User-Agent") || "").toLowerCase();
      const clientName = (
        request.headers.get("X-Client-App") ||
        request.headers.get("X-App-Name") ||
        request.headers.get("X-Request-Client") ||
        ""
      ).toLowerCase();

      const haystack = `${userAgent} ${clientName}`.trim();
      if (haystack) {
        for (const hint of STREAMING_USER_AGENT_HINTS) {
          if (haystack.includes(hint)) {
            stream = true;
            console.log(`Detected streaming client: ${haystack}`);
            break;
          }
        }
      }
    }

    if (stream === undefined || stream === null) {
      stream = false;
    }

    if (!messages || messages.length === 0) {
      return new Response(JSON.stringify({ error: "messages parameter cannot be empty" }), {
        status: 400,
        headers: { "Content-Type": "application/json" },
      });
    }

    const authManager = new AmazonQAuthManager(env);
    const client = new AmazonQClient(authManager, env);

    const content = OpenAIConverter.messagesToContent(messages);
    const conversationId = generateId("conv");

    let modelId = "claude-sonnet-4.5";
    if (["claude-sonnet-4.5", "claude-sonnet-4", "amazon-q"].includes(model)) {
      if (model === "claude-sonnet-4") {
        modelId = "claude-sonnet-4";
      }
    }

    const amazonqResponse = await client.sendMessage(content, conversationId, modelId, stream);

    if (stream) {
      // Stream response
      const { readable, writable } = new TransformStream();
      const writer = writable.getWriter();
      const encoder = new TextEncoder();

      // Process stream in background
      (async () => {
        try {
          const messageId = generateId("msg");
          const accumulatedContent: string[] = [];

          // Send start events
          if (formatType === "anthropic") {
            await writer.write(encoder.encode(
              OpenAIConverter.createStreamChunk("", model, "start", "anthropic", messageId)
            ));
            await writer.write(encoder.encode(
              OpenAIConverter.createStreamChunk("", model, "content_start", "anthropic", messageId)
            ));
          } else {
            await writer.write(encoder.encode(
              OpenAIConverter.createStreamChunk("", model, "start", "openai")
            ));
          }

          // Read and process chunks
          const reader = amazonqResponse.body?.getReader();
          if (!reader) throw new Error("No response body");

          const decoder = new TextDecoder();
          let buffer = "";

          while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });

            // Prevent buffer overflow
            if (buffer.length > BUFFER_MAX_SIZE) {
              console.warn("Buffer overflow, truncating");
              buffer = buffer.substring(buffer.length - BUFFER_MAX_SIZE);
            }

            // Extract JSON objects from buffer
            while (true) {
              const [jsonStr, newBuffer] = OpenAIConverter.extractJsonFromBuffer(buffer);
              buffer = newBuffer;

              if (!jsonStr) break;

              try {
                const obj = JSON.parse(jsonStr);
                if (obj.content && typeof obj.content === "string") {
                  const text = obj.content;
                  accumulatedContent.push(text);

                  const chunk = OpenAIConverter.createStreamChunk(
                    text,
                    model,
                    "content",
                    formatType,
                    messageId
                  );
                  await writer.write(encoder.encode(chunk));
                }
              } catch (e) {
                // Skip invalid JSON
              }
            }
          }

          // Send end events
          if (formatType === "anthropic") {
            const finalText = accumulatedContent.join("");
            await writer.write(encoder.encode(
              OpenAIConverter.createStreamChunk("", model, "content_end", "anthropic", messageId)
            ));
            await writer.write(encoder.encode(
              OpenAIConverter.createStreamChunk("", model, "end", "anthropic", messageId)
            ));
            await writer.write(encoder.encode(
              OpenAIConverter.createStreamChunk("", model, "stop", "anthropic", messageId, finalText)
            ));
          } else {
            await writer.write(encoder.encode(
              OpenAIConverter.createStreamChunk("", model, "end", "openai")
            ));
            await writer.write(encoder.encode("data: [DONE]\n\n"));
          }

          await writer.close();
        } catch (e) {
          console.error("Stream error:", e);
          const errorChunk = {
            error: { message: String(e), type: "stream_error" },
          };
          await writer.write(encoder.encode(`data: ${JSON.stringify(errorChunk)}\n\n`));
          await writer.close();
        }
      })();

      const headers: Record<string, string> = {
        "Content-Type": "text/event-stream; charset=utf-8",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
      };

      if (formatType === "anthropic") {
        headers["anthropic-version"] = ANTHROPIC_API_VERSION;
        headers["x-request-id"] = generateId("req");
      }

      return new Response(readable, { headers });
    } else {
      // Non-stream response
      const rawResponse = await amazonqResponse.text();
      const openaiResponse = OpenAIConverter.amazonqToOpenaiResponse(rawResponse, model, conversationId);

      if (formatType === "anthropic") {
        const anthropicResponse = {
          id: generateId("msg"),
          type: "message",
          role: "assistant",
          content: [
            {
              type: "text",
              text: openaiResponse.choices[0].message.content,
            },
          ],
          model: model,
          stop_reason: "end_turn",
          stop_sequence: null,
          usage: { input_tokens: 0, output_tokens: 0 },
        };

        return new Response(JSON.stringify(anthropicResponse), {
          headers: {
            "Content-Type": "application/json",
            "anthropic-version": ANTHROPIC_API_VERSION,
            "x-request-id": generateId("req"),
          },
        });
      } else {
        return new Response(JSON.stringify(openaiResponse), {
          headers: { "Content-Type": "application/json" },
        });
      }
    }
  } catch (e) {
    console.error("Request error:", e);
    return new Response(
      JSON.stringify({
        error: {
          message: String(e),
          type: "server_error",
          code: "internal_error",
        },
      }),
      {
        status: 500,
        headers: { "Content-Type": "application/json" },
      }
    );
  }
}

// Main worker export
export default {
  async fetch(request: Request, env: Env, ctx: ExecutionContext): Promise<Response> {
    const url = new URL(request.url);

    // CORS headers
    const corsHeaders = {
      "Access-Control-Allow-Origin": "*",
      "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
      "Access-Control-Allow-Headers": "Content-Type, Authorization, anthropic-version, x-api-key",
    };

    // Handle CORS preflight
    if (request.method === "OPTIONS") {
      return new Response(null, { headers: corsHeaders });
    }

    // Route handlers
    if (url.pathname === "/v1/chat/completions" && request.method === "POST") {
      const response = await handleChatRequest(request, env, "openai");
      Object.entries(corsHeaders).forEach(([key, value]) => response.headers.set(key, value));
      return response;
    }

    if (url.pathname === "/v1/messages" && request.method === "POST") {
      const response = await handleChatRequest(request, env, "anthropic");
      Object.entries(corsHeaders).forEach(([key, value]) => response.headers.set(key, value));
      return response;
    }

    if (url.pathname === "/v1/models" && request.method === "GET") {
      return new Response(
        JSON.stringify({
          object: "list",
          data: [
            {
              id: "claude-sonnet-4.5",
              object: "model",
              created: Math.floor(Date.now() / 1000),
              owned_by: "anthropic",
            },
            {
              id: "claude-sonnet-4",
              object: "model",
              created: Math.floor(Date.now() / 1000),
              owned_by: "anthropic",
            },
            {
              id: "amazon-q",
              object: "model",
              created: Math.floor(Date.now() / 1000),
              owned_by: "amazon",
            },
          ],
        }),
        {
          headers: { ...corsHeaders, "Content-Type": "application/json" },
        }
      );
    }

    if (url.pathname === "/credentials" && request.method === "POST") {
      try {
        const credentials = await request.json<any>();
        const authManager = new AmazonQAuthManager(env);
        await authManager.setCredentials(credentials);

        return new Response(
          JSON.stringify({ message: "Credentials saved successfully" }),
          {
            headers: { ...corsHeaders, "Content-Type": "application/json" },
          }
        );
      } catch (e) {
        return new Response(
          JSON.stringify({ error: String(e) }),
          {
            status: 500,
            headers: { ...corsHeaders, "Content-Type": "application/json" },
          }
        );
      }
    }

    if (url.pathname === "/health" && request.method === "GET") {
      return new Response(
        JSON.stringify({
          status: "ok",
          timestamp: new Date().toISOString(),
        }),
        {
          headers: { ...corsHeaders, "Content-Type": "application/json" },
        }
      );
    }

    if (url.pathname === "/" && request.method === "GET") {
      return new Response(
        JSON.stringify({
          message: "Amazon Q to OpenAI API Bridge - Cloudflare Worker",
          version: "2.0.0",
          auth_method: "OAuth 2.0",
          endpoints: {
            openai_chat: "/v1/chat/completions",
            anthropic_messages: "/v1/messages",
            models: "/v1/models",
            credentials: "/credentials",
            health: "/health",
          },
          default_model: "claude-sonnet-4.5",
        }),
        {
          headers: { ...corsHeaders, "Content-Type": "application/json" },
        }
      );
    }

    return new Response("Not Found", {
      status: 404,
      headers: corsHeaders,
    });
  },
};
