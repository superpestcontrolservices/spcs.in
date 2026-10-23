const allowedOrigins = new Set(
    (Deno.env.get("ALLOWED_ORIGINS") ?? "https://superpest.in,https://www.superpest.in")
        .split(",")
        .map((origin) => origin.trim())
        .filter(Boolean)
);
const allowedTurnstileHosts = new Set(
    (Deno.env.get("ALLOWED_TURNSTILE_HOSTS") ?? "superpest.in,www.superpest.in")
        .split(",")
        .map((hostname) => hostname.trim().toLowerCase())
        .filter(Boolean)
);

const MAX_REQUEST_BYTES = 8192;
const MAX_LENGTHS = {
    name: 100,
    phone: 10,
    email: 254,
    service: 100,
    message: 1000
} as const;

function corsHeaders(_origin: string | null): HeadersInit {
    const headers: Record<string, string> = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "apikey, content-type",
        "Access-Control-Allow-Methods": "POST, OPTIONS",
        "Vary": "Origin"
    };
    return headers;
}

function jsonResponse(status: number, body: Record<string, string>, origin: string | null): Response {
    return new Response(JSON.stringify(body), {
        status,
        headers: {
            ...corsHeaders(origin),
            "Content-Type": "application/json",
            "Cache-Control": "no-store"
        }
    });
}

function isRecord(value: unknown): value is Record<string, unknown> {
    return typeof value === "object" && value !== null && !Array.isArray(value);
}

function readText(body: Record<string, unknown>, key: keyof typeof MAX_LENGTHS): string | null {
    const value = body[key];
    if (typeof value !== "string") return null;
    const normalized = value.trim();
    return normalized.length <= MAX_LENGTHS[key] ? normalized : null;
}

function getClientIp(request: Request): string | null {
    const trustedProxyAddress = request.headers.get("cf-connecting-ip") ??
        request.headers.get("x-real-ip") ??
        request.headers.get("x-forwarded-for")?.split(",")[0]?.trim();
    return trustedProxyAddress && trustedProxyAddress.length <= 64 ? trustedProxyAddress : null;
}

async function hashClientIp(ip: string, secret: string): Promise<string> {
    const key = await crypto.subtle.importKey(
        "raw",
        new TextEncoder().encode(secret),
        { name: "HMAC", hash: "SHA-256" },
        false,
        ["sign"]
    );
    const signature = await crypto.subtle.sign("HMAC", key, new TextEncoder().encode(ip));
    return Array.from(new Uint8Array(signature), (byte) => byte.toString(16).padStart(2, "0")).join("");
}

async function verifyTurnstile(
    token: string,
    secret: string,
    ip: string
): Promise<boolean> {
    const response = await fetch("https://challenges.cloudflare.com/turnstile/v0/siteverify", {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: new URLSearchParams({ secret, response: token, remoteip: ip })
    });
    if (!response.ok) return false;

    const result: unknown = await response.json();
    if (!isRecord(result) || result.success !== true) return false;
    if (typeof result.hostname !== "string" || !allowedTurnstileHosts.has(result.hostname.toLowerCase())) {
        return false;
    }
    return result.action === "enquiry";
}

Deno.serve(async (request: Request): Promise<Response> => {
    const origin = request.headers.get("origin");
    const headers = corsHeaders(origin);

    if (request.method === "OPTIONS") {
        if (!origin || !allowedOrigins.has(origin)) {
            return new Response(null, { status: 403, headers });
        }
        return new Response(null, { status: 204, headers });
    }

    if (request.method !== "POST" || !origin || !allowedOrigins.has(origin)) {
        return jsonResponse(403, { message: "Unable to submit enquiry." }, origin);
    }

    const contentLength = Number(request.headers.get("content-length") || 0);
    if (contentLength > MAX_REQUEST_BYTES) {
        return jsonResponse(413, { message: "Unable to submit enquiry." }, origin);
    }

    let rawBody: string;
    try {
        rawBody = await request.text();
    } catch {
        return jsonResponse(400, { message: "Unable to submit enquiry." }, origin);
    }
    if (new TextEncoder().encode(rawBody).byteLength > MAX_REQUEST_BYTES) {
        return jsonResponse(413, { message: "Unable to submit enquiry." }, origin);
    }

    let body: unknown;
    try {
        body = JSON.parse(rawBody);
    } catch {
        return jsonResponse(400, { message: "Unable to submit enquiry." }, origin);
    }
    if (!isRecord(body)) {
        return jsonResponse(400, { message: "Unable to submit enquiry." }, origin);
    }

    if (typeof body.website === "string" && body.website.trim()) {
        return new Response(null, { status: 204, headers });
    }

    const name = readText(body, "name");
    const phone = readText(body, "phone");
    const email = readText(body, "email");
    const service = readText(body, "service");
    const message = readText(body, "message");
    const turnstileToken = typeof body.turnstileToken === "string" ? body.turnstileToken.trim() : "";

    if (
        !name ||
        !phone ||
        !email ||
        !service ||
        message === null ||
        !/^[0-9]{10}$/.test(phone) ||
        !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email) ||
        turnstileToken.length === 0 ||
        turnstileToken.length > 2048
    ) {
        return jsonResponse(400, { message: "Unable to submit enquiry." }, origin);
    }

    const supabaseUrl = Deno.env.get("SUPABASE_URL");
    const serviceRoleKey = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY");
    const turnstileSecret = Deno.env.get("TURNSTILE_SECRET_KEY");
    const rateLimitSecret = Deno.env.get("RATE_LIMIT_HMAC_SECRET");
    const resendApiKey = Deno.env.get("RESEND_API_KEY");
    const notificationFrom = Deno.env.get("ENQUIRY_NOTIFICATION_FROM");
    const notificationTo = Deno.env.get("ENQUIRY_NOTIFICATION_TO");
    if (
        !supabaseUrl ||
        !serviceRoleKey ||
        !turnstileSecret ||
        !rateLimitSecret ||
        !resendApiKey ||
        !notificationFrom ||
        !notificationTo
    ) {
        console.error("enquiry_submit_error", { stage: "configuration" });
        return jsonResponse(503, { message: "Unable to submit enquiry." }, origin);
    }

    const clientIp = getClientIp(request);
    if (!clientIp) {
        return jsonResponse(400, { message: "Unable to submit enquiry." }, origin);
    }

    try {
        if (!(await verifyTurnstile(turnstileToken, turnstileSecret, clientIp))) {
            return jsonResponse(400, { message: "Unable to submit enquiry." }, origin);
        }

        const ipHash = await hashClientIp(clientIp, rateLimitSecret);
        const rateResponse = await fetch(new URL("/rest/v1/rpc/check_enquiry_rate_limit", supabaseUrl), {
            method: "POST",
            headers: {
                apikey: serviceRoleKey,
                Authorization: `Bearer ${serviceRoleKey}`,
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ p_ip_hash: ipHash })
        });
        if (!rateResponse.ok) {
            console.error("enquiry_submit_error", { stage: "rate_limit" });
            return jsonResponse(503, { message: "Unable to submit enquiry." }, origin);
        }
        if (await rateResponse.json() !== true) {
            return jsonResponse(429, { message: "Unable to submit enquiry." }, origin);
        }

        const insertResponse = await fetch(new URL("/rest/v1/enquiries", supabaseUrl), {
            method: "POST",
            headers: {
                apikey: serviceRoleKey,
                Authorization: `Bearer ${serviceRoleKey}`,
                "Content-Type": "application/json",
                Prefer: "return=minimal"
            },
            body: JSON.stringify({
                name,
                phone,
                email,
                service,
                message,
                status: "New"
            })
        });
        if (!insertResponse.ok) {
            console.error("enquiry_submit_error", { stage: "database_insert", status: insertResponse.status });
            return jsonResponse(503, { message: "Unable to submit enquiry." }, origin);
        }

        let notificationSent = false;
        try {
            const notificationResponse = await fetch("https://api.resend.com/emails", {
                method: "POST",
                headers: {
                    Authorization: `Bearer ${resendApiKey}`,
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    from: notificationFrom,
                    to: [notificationTo],
                    reply_to: email,
                    subject: "New website enquiry",
                    text: [
                        "A new enquiry was submitted on the website.",
                        "",
                        `Name: ${name}`,
                        `Phone: ${phone}`,
                        `Email: ${email}`,
                        `Service: ${service}`,
                        "",
                        "Message:",
                        message
                    ].join("\n")
                })
            });
            notificationSent = notificationResponse.ok;
            if (!notificationSent) {
                console.error("enquiry_notification_error", { status: notificationResponse.status });
            }
        } catch {
            console.error("enquiry_notification_error", { stage: "upstream" });
        }

        if (!notificationSent) {
            return jsonResponse(202, { notification: "failed" }, origin);
        }

        return new Response(null, {
            status: 204,
            headers: { ...headers, "Cache-Control": "no-store" }
        });
    } catch {
        console.error("enquiry_submit_error", { stage: "upstream" });
        return jsonResponse(503, { message: "Unable to submit enquiry." }, origin);
    }
});
