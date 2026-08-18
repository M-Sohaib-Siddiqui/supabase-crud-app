import { serve } from "https://deno.land/std@0.168.0/http/server.ts";

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
};

interface ValidationRequest {
  filename: string;
  file_size: number;
  mime_type?: string;
  file_base64?: string;
}

serve(async (req) => {
  // Handle CORS preflight
  if (req.method === "OPTIONS") {
    return new Response("ok", { headers: corsHeaders });
  }

  try {
    const payload: ValidationRequest = await req.json();
    const { filename, file_size, mime_type, file_base64 } = payload;

    const MAX_SIZE_BYTES = 10 * 1024 * 1024; // 10 MB
    const ALLOWED_EXTENSIONS = ["png", "jpg", "jpeg", "gif", "pdf", "txt", "csv", "json", "md"];

    const ext = filename.split(".").pop()?.toLowerCase() || "";

    const errors: string[] = [];

    // 1. Validate File Size
    if (!file_size || file_size <= 0) {
      errors.push("Invalid file size (must be greater than 0 bytes).");
    } else if (file_size > MAX_SIZE_BYTES) {
      errors.push(`File size (${(file_size / (1024 * 1024)).toFixed(2)} MB) exceeds max limit of 10 MB.`);
    }

    // 2. Validate Extension
    if (!ALLOWED_EXTENSIONS.includes(ext)) {
      errors.push(`File extension '.${ext}' is not permitted. Allowed: ${ALLOWED_EXTENSIONS.join(", ")}`);
    }

    // 3. Calculate Checksum if Base64 content provided
    let fileHash: string | null = null;
    if (file_base64) {
      try {
        const binaryString = atob(file_base64);
        const bytes = new Uint8Array(binaryString.length);
        for (let i = 0; i < binaryString.length; i++) {
          bytes[i] = binaryString.charCodeAt(i);
        }
        const hashBuffer = await crypto.subtle.digest("SHA-256", bytes);
        const hashArray = Array.from(new Uint8Array(hashBuffer));
        fileHash = hashArray.map((b) => b.toString(16).padStart(2, "0")).join("");
      } catch (e) {
        console.warn("Hash calculation failed:", e);
      }
    }

    const isValid = errors.length === 0;

    const responsePayload = {
      valid: isValid,
      status: isValid ? "validated" : "rejected",
      filename,
      extension: ext,
      file_size,
      mime_type: mime_type || "application/octet-stream",
      file_hash: fileHash,
      errors,
      processed_at: new Date().toISOString(),
      metadata: {
        is_image: ["png", "jpg", "jpeg", "gif"].includes(ext),
        is_document: ["pdf", "txt", "csv", "json", "md"].includes(ext),
        server_node: "Deno Edge Functions",
      },
    };

    return new Response(JSON.stringify(responsePayload), {
      headers: { ...corsHeaders, "Content-Type": "application/json" },
      status: isValid ? 200 : 400,
    });
  } catch (error) {
    return new Response(
      JSON.stringify({
        valid: false,
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
