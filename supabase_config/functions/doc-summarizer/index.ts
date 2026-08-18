import { serve } from "https://deno.land/std@0.168.0/http/server.ts";

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
};

interface SummarizeRequest {
  filename: string;
  text_content?: string;
  file_base64?: string;
}

serve(async (req) => {
  if (req.method === "OPTIONS") {
    return new Response("ok", { headers: corsHeaders });
  }

  try {
    const payload: SummarizeRequest = await req.json();
    let text = payload.text_content || "";

    // If Base64 provided, decode to string
    if (!text && payload.file_base64) {
      try {
        text = atob(payload.file_base64);
      } catch {
        text = "[Binary Content - Cannot extract plain text]";
      }
    }

    if (!text || text.trim().length === 0) {
      text = "Empty or unreadable file content.";
    }

    const cleanText = text.replace(/\s+/g, " ").trim();
    const words = cleanText.split(" ").filter((w) => w.length > 0);
    const lines = text.split("\n").length;
    const charCount = text.length;

    // Extract top frequent words (excluding common stop words)
    const stopWords = new Set(["the", "is", "in", "at", "of", "and", "a", "to", "for", "with", "on", "that", "by", "this", "an", "be", "are", "from"]);
    const frequencyMap: Record<string, number> = {};
    for (const rawWord of words) {
      const word = rawWord.toLowerCase().replace(/[^a-z0-9]/g, "");
      if (word.length > 3 && !stopWords.has(word)) {
        frequencyMap[word] = (frequencyMap[word] || 0) + 1;
      }
    }

    const topKeywords = Object.entries(frequencyMap)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 5)
      .map(([word]) => word);

    // Generate concise summary snippet
    const summarySnippet =
      cleanText.length > 250
        ? cleanText.substring(0, 247) + "..."
        : cleanText;

    const responsePayload = {
      filename: payload.filename,
      char_count: charCount,
      word_count: words.length,
      line_count: lines,
      top_keywords: topKeywords,
      summary: summarySnippet,
      processed_at: new Date().toISOString(),
    };

    return new Response(JSON.stringify(responsePayload), {
      headers: { ...corsHeaders, "Content-Type": "application/json" },
      status: 200,
    });
  } catch (error) {
    return new Response(
      JSON.stringify({
        status: "error",
        error: error instanceof Error ? error.message : "Unknown error",
      }),
      {
        headers: { ...corsHeaders, "Content-Type": "application/json" },
        status: 500,
      }
    );
  }
});
