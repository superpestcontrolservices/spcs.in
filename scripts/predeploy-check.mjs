#!/usr/bin/env node
import fs from "node:fs";
import path from "node:path";
import process from "node:process";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const args = process.argv.slice(2);
const dirIndex = args.indexOf("--publish-dir");
const publishDir = path.resolve(root, dirIndex >= 0 ? args[dirIndex + 1] : "_site");
const failures = [];

function fail(file, line, reason) {
    failures.push(`${path.relative(publishDir, file)}:${line} - ${reason}`);
}

if (!fs.existsSync(publishDir) || !fs.statSync(publishDir).isDirectory()) {
    console.error(`Pre-deploy check: publish folder does not exist: ${path.relative(root, publishDir)}`);
    console.error("Build the exact publish directory first, then rerun this check.");
    process.exit(1);
}

function walk(directory) {
    const entries = fs.readdirSync(directory, { withFileTypes: true });
    const results = [];
    for (const entry of entries) {
        const full = path.join(directory, entry.name);
        if (entry.isDirectory()) results.push(...walk(full));
        else if (entry.isFile()) results.push(full);
    }
    return results;
}

const files = walk(publishDir);
const relative = (file) => path.relative(publishDir, file).split(path.sep).join("/");
const forbiddenText = [
    ["REPLACE_WITH_", /REPLACE_WITH_/i],
    ["[[TO-FILL", /\[\[TO-FILL/i],
    ["localhost", /\blocalhost\b/i],
    ["127.0.0.1", /\b127\.0\.0\.1\b/],
    ["example.com", /\bexample\.com\b/i],
    ["service_role", /service[\s_-]*role/i],
    ["sb_secret", /\bsb_secret\b/i],
    [".env", /\.env(?:\b|\/|\\)/i],
];
const reportName = /(?:^|\/)(?:.*audit.*\.md|SECURITY_[^/]*|LAUNCH_[^/]*|AI_READINESS_[^/]*)$/i;
const customerCsvHeader = /(?:customer|enquir|client).*(?:email|phone|mobile|address)|(?:email|phone|mobile).*(?:customer|enquir|client)/i;

function stripVisible(line) {
    return line
        .replace(/<!--.*?-->/g, "")
        .replace(/<script\b[^>]*>.*?<\/script\s*>/gi, "")
        .replace(/<style\b[^>]*>.*?<\/style\s*>/gi, "")
        .replace(/<[^>]*>/g, " ")
        .replace(/&(?:nbsp|amp|lt|gt|quot|#39);/gi, " ");
}

for (const file of files) {
    const rel = relative(file);
    const lower = rel.toLowerCase();
    if (/^(?:\.env|\.env\.)/i.test(path.basename(rel))) {
        fail(file, 1, "environment file is in the publish folder");
    }
    if (reportName.test(rel)) fail(file, 1, "internal audit/report file is in the publish folder");
    if (/\.(?:bak|zip|sql)$/i.test(rel)) fail(file, 1, "backup/archive/SQL file is in the publish folder");
    if (lower.endsWith(".csv")) {
        const header = fs.readFileSync(file, "utf8").split(/\r?\n/, 1)[0] ?? "";
        if (customerCsvHeader.test(header)) fail(file, 1, "CSV appears to contain customer data");
    }

    const content = fs.readFileSync(file, "utf8");
    const lines = content.split(/\r?\n/);
    for (let index = 0; index < lines.length; index += 1) {
        for (const [name, pattern] of forbiddenText) {
            if (pattern.test(lines[index])) fail(file, index + 1, `prohibited marker or sensitive-pattern name: ${name}`);
        }
        if (/\bTODO\s*:/i.test(stripVisible(lines[index]))) {
            fail(file, index + 1, "visible TODO placeholder");
        }
    }
}

const htmlFiles = files.filter((file) => file.toLowerCase().endsWith(".html"));
const htmlByRelative = new Map(htmlFiles.map((file) => [relative(file), file]));
const sitemapPath = path.join(publishDir, "sitemap.xml");
const sitemapUrls = [];
if (fs.existsSync(sitemapPath)) {
    const xml = fs.readFileSync(sitemapPath, "utf8");
    for (const match of xml.matchAll(/<loc>\s*([^<]+)\s*<\/loc>/gi)) {
        const line = xml.slice(0, match.index).split(/\r?\n/).length;
        sitemapUrls.push({ url: match[1].trim(), line });
    }
} else {
    console.warn("Pre-deploy check: sitemap.xml is absent; sitemap-specific checks skipped.");
}

for (const { url, line } of sitemapUrls) {
    let pathname;
    try {
        pathname = new URL(url).pathname;
    } catch {
        fail(sitemapPath, line, "invalid sitemap URL");
        continue;
    }
    let rel = decodeURIComponent(pathname).replace(/^\/+/, "");
    if (!rel || pathname.endsWith("/")) rel = path.join(rel, "index.html").replaceAll("\\", "/");
    let target = htmlByRelative.get(rel);
    if (!target && !path.extname(rel)) {
        target = htmlByRelative.get(`${rel.replace(/\/+$/, "")}/index.html`);
    }
    if (!target) {
        fail(sitemapPath, line, `sitemap URL has no matching HTML file: ${pathname}`);
        continue;
    }
    const robots = fs.readFileSync(target, "utf8").match(/<meta\b(?=[^>]*\bname=["']robots["'])[^>]*\bcontent=["']([^"']*)["'][^>]*>/i);
    if (robots?.[1] && /\bnoindex\b/i.test(robots[1])) {
        fail(target, 1, "page in sitemap has noindex");
    }
}

function resolveLocalLink(sourceFile, rawValue) {
    let value = rawValue.trim();
    if (!value || /^(?:#|mailto:|tel:|sms:|javascript:|data:|blob:)/i.test(value)) return null;
    if (/^[a-z][a-z\d+.-]*:/i.test(value) || value.startsWith("//")) {
        let parsed;
        try {
            parsed = new URL(value, "https://www.superpest.in");
        } catch {
            return null;
        }
        if (!["www.superpest.in", "superpest.in"].includes(parsed.hostname.toLowerCase())) return null;
        value = parsed.pathname;
    }
    let clean;
    try {
        clean = decodeURIComponent(value.split(/[?#]/, 1)[0]);
    } catch {
        clean = value.split(/[?#]/, 1)[0];
    }
    const resolved = clean.startsWith("/")
        ? path.join(publishDir, clean.replace(/^\/+/, ""))
        : path.resolve(path.dirname(sourceFile), clean);
    const exact = caseSensitivePath(resolved);
    if (exact && fs.statSync(exact).isDirectory()) return path.join(exact, "index.html");
    if (exact) return exact;
    if (!path.extname(resolved)) {
        const indexFile = path.join(resolved, "index.html");
        const exactIndex = caseSensitivePath(indexFile);
        if (exactIndex) return exactIndex;
    }
    return resolved;
}

function caseSensitivePath(target) {
    const relative = path.relative(publishDir, target);
    if (relative === ".." || relative.startsWith(`..${path.sep}`) || path.isAbsolute(relative)) return null;
    let current = publishDir;
    for (const segment of relative.split(path.sep).filter(Boolean)) {
        let entries;
        try {
            entries = fs.readdirSync(current);
        } catch {
            return null;
        }
        if (!entries.includes(segment)) return null;
        current = path.join(current, segment);
    }
    return fs.existsSync(current) ? current : null;
}

function hasReviewSchema(value) {
    if (Array.isArray(value)) return value.some(hasReviewSchema);
    if (!value || typeof value !== "object") return false;
    const types = Array.isArray(value["@type"]) ? value["@type"] : [value["@type"]];
    return types.some((type) => type === "Review" || type === "AggregateRating")
        || Object.values(value).some(hasReviewSchema);
}

for (const file of htmlFiles) {
    const source = fs.readFileSync(file, "utf8");
    const activeMarkup = source.replace(/<noscript\b[^>]*>[\s\S]*?<\/noscript\s*>/gi, "");
    const stylesheetTags = /<link\b[^>]*>/gi;
    for (const match of activeMarkup.matchAll(stylesheetTags)) {
        const tag = match[0];
        if (/\srel=["']stylesheet["']/i.test(tag) && /\shref=["'][^"']+\.css(?:[?#][^"']*)?["']/i.test(tag)) {
            const line = source.slice(0, match.index).split(/\r?\n/).length;
            fail(file, line, "render-blocking stylesheet link");
        }
    }
    const jsonLdBlocks = /<script\b[^>]*type=["']application\/ld\+json["'][^>]*>([\s\S]*?)<\/script\s*>/gi;
    for (const match of source.matchAll(jsonLdBlocks)) {
        const line = source.slice(0, match.index).split(/\r?\n/).length;
        try {
            const schema = JSON.parse(match[1]);
            if (hasReviewSchema(schema)) {
                fail(file, line, "review or aggregate-rating structured data is not permitted");
            }
        } catch {
            fail(file, line, "invalid JSON-LD syntax");
        }
    }
    const links = /<(?:a|area|img|script|link|source|iframe)\b[^>]*?\b(?:href|src|poster)=["']([^"']+)["'][^>]*>/gi;
    for (const match of source.matchAll(links)) {
        const target = resolveLocalLink(file, match[1]);
        if (target && !fs.existsSync(target)) {
            const line = source.slice(0, match.index).split(/\r?\n/).length;
            fail(file, line, `broken internal link: ${match[1].split(/[?#]/, 1)[0]}`);
        }
    }
}

if (failures.length) {
    console.error(`Pre-deploy check failed with ${failures.length} issue(s):`);
    for (const failure of failures) console.error(`- ${failure}`);
    process.exit(1);
}
console.log(`Pre-deploy check passed: ${files.length} files, ${htmlFiles.length} HTML pages, ${sitemapUrls.length} sitemap URLs.`);
