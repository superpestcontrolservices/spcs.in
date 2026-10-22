const required = ["SUPABASE_URL", "SUPABASE_ANON_KEY", "SUPABASE_TABLES", "RLS_PROBE_FILTERS_JSON"];
const missing = required.filter((name) => !process.env[name]);
if (missing.length) {
    console.error(`Set required environment variables: ${missing.join(", ")}`);
    process.exit(2);
}

if (process.env.RLS_TEST_CONFIRM !== "staging-only") {
    console.error("Refusing to run. Set RLS_TEST_CONFIRM=staging-only for a disposable staging project.");
    process.exit(2);
}

const supabaseUrl = process.env.SUPABASE_URL.replace(/\/+$/, "");
const anonKey = process.env.SUPABASE_ANON_KEY;
const tables = [...new Set([
    ...process.env.SUPABASE_TABLES.split(",").map((name) => name.trim()).filter(Boolean),
    "enquiries"
])];
let filters;
try {
    filters = JSON.parse(process.env.RLS_PROBE_FILTERS_JSON);
} catch {
    console.error("RLS_PROBE_FILTERS_JSON must be a JSON object of safe, verified-absent equality filters.");
    process.exit(2);
}

function apiUrl(table, query) {
    const url = new URL(`/rest/v1/${encodeURIComponent(table)}`, supabaseUrl);
    if (query) {
        for (const [key, value] of new URLSearchParams(query)) {
            url.searchParams.set(key, value);
        }
    }
    return url;
}

function headers(extra = {}) {
    return {
        apikey: anonKey,
        "Content-Type": "application/json",
        ...extra
    };
}

async function expectDenied(label, response) {
    if (response.status !== 401 && response.status !== 403) {
        const body = await response.text();
        throw new Error(`${label}: expected HTTP 401/403 denial, received ${response.status}; response length ${body.length}.`);
    }
    console.log(`PASS ${label}: denied (${response.status})`);
}

async function expectFailure(label, response) {
    if (response.ok) {
        throw new Error(`${label}: expected rejection, received HTTP ${response.status}.`);
    }
    console.log(`PASS ${label}: rejected (${response.status})`);
}

async function request(table, method, body, filter) {
    const query = method === "GET" ? "select=*&limit=1" : filter;
    const preferences = method === "PATCH" || method === "DELETE"
        ? { Prefer: "tx=rollback,return=minimal" }
        : method === "POST"
            ? { Prefer: "return=minimal" }
            : {};
    return fetch(apiUrl(table, query), {
        method,
        headers: headers(preferences),
        body: body === undefined ? undefined : JSON.stringify(body)
    });
}

for (const table of tables) {
    await expectDenied(
        `SELECT ${table}`,
        await request(table, "GET", undefined, "select=*&limit=1")
    );

    const filter = filters[table];
    if (typeof filter !== "string" || !/^[A-Za-z_][A-Za-z0-9_]*=eq\.[^&]+$/.test(filter)) {
        throw new Error(`Provide a safe equality probe filter for ${table} in RLS_PROBE_FILTERS_JSON.`);
    }
    await expectDenied(
        `UPDATE ${table}`,
        await request(table, "PATCH", { name: "RLS probe only" }, filter)
    );
    await expectDenied(
        `DELETE ${table}`,
        await request(table, "DELETE", undefined, filter)
    );
}

const validEnquiry = {
    name: `RLS verification ${new Date().toISOString()}`,
    phone: "9876543210",
    email: `rls-check-${Date.now()}@example.invalid`,
    service: "Security verification test",
    message: "Automated RLS test record; review and remove only through an approved admin workflow.",
    status: "New"
};

const validInsert = await request("enquiries", "POST", validEnquiry);
if (validInsert.status !== 201 && validInsert.status !== 204) {
    const body = await validInsert.text();
    throw new Error(`Valid enquiry insert failed with HTTP ${validInsert.status}; response length ${body.length}.`);
}
console.log(`PASS valid enquiry INSERT: accepted (${validInsert.status}); test row is retained.`);

await expectFailure(
    "invalid enquiry INSERT",
    await request("enquiries", "POST", { ...validEnquiry, phone: "123" })
);
await expectFailure(
    "oversized enquiry INSERT",
    await request("enquiries", "POST", { ...validEnquiry, name: "x".repeat(101) })
);
