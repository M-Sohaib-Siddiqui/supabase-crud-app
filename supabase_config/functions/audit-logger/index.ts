import { serve } from "https://deno.land/std@0.168.0/http/server.ts";

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
};

interface AuditRequest {
  action: string;
  resource_type: string;
  resource_id: string;
  user_id?: string;
  details?: Record<string, unknown>;
}

serve(async (req) => {
  if (req.method === "OPTIONS") {
    return new Response("ok", { headers: corsHeaders });
  }

  try {
    const payload: AuditRequest = await req.json();
    const { action, resource_type, resource_id, user_id, details } = payload;

    const logEntry = {
      id: crypto.randomUUID(),
      action: action || "ACCESS",
      resource_type: resource_type || "storage",
      resource_id: resource_id || "unknown",
      user_id: user_id || "anonymous_user",
      details: details || {},
      ip_address: req.headers.get("x-forwarded-for") || "127.0.0.1",
      user_agent: req.headers.get("user-agent") || "Python-Supabase-SDK",
      logged_at: new Date().toISOString(),
    };

    console.log("AUDIT EVENT LOGGED:", JSON.stringify(logEntry));

    return new Response(
      JSON.stringify({
        status: "success",
        message: "Audit event recorded successfully",
        audit_log: logEntry,
      }),
      {
        headers: { ...corsHeaders, "Content-Type": "application/json" },
        status: 200,
      }
    );
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
