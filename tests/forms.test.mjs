import test from "node:test";
import assert from "node:assert/strict";
import {
    isValidEnquiry,
    normalizeEnquiryValues
} from "../js/enquiry-validation.mjs";

const validValues = {
    name: "  Test Customer  ",
    phone: "9876543210",
    email: "test@example.invalid",
    service: "Cockroach Control",
    message: "Please call after 5 PM."
};

let clock = 10000;
let fetchCalls = [];
let nextResponse = { ok: true, status: 204 };

class FakeElement {
    constructor(tagName) {
        this.tagName = tagName;
        this.children = [];
        this.attributes = {};
        this.dataset = {};
        this.listeners = {};
        this.classNames = new Set();
        this.classList = {
            toggle: (name, enabled) => {
                if (enabled) this.classNames.add(name);
                else this.classNames.delete(name);
            }
        };
        this.textContent = "";
    }

    setAttribute(name, value) {
        this.attributes[name] = value;
    }

    append(...elements) {
        this.children.push(...elements);
    }

    replaceChildren(...elements) {
        this.children = elements;
    }

    addEventListener(name, callback) {
        this.listeners[name] = callback;
    }
}

class FakeForm extends FakeElement {
    constructor() {
        super("form");
        this.fields = new Map();
        this.elements = { namedItem: (name) => this.fields.get(name) || null };
        this.button = new FakeElement("button");
        this.button.type = "submit";
        this.turnstileResponse = { value: "verified-test-token" };
        this.status = null;
        this.widget = null;
        this.resetCount = 0;
        for (const [name, value] of Object.entries(validValues)) {
            const field = name === "service"
                ? new FakeElement("SELECT")
                : { addEventListener() {} };
            field.name = name;
            field.value = value;
            this.fields.set(name, field);
        }
    }

    querySelector(selector) {
        if (selector === 'button[type="submit"]') return this.button;
        if (selector === ".cf-turnstile") return this.widget;
        if (selector === '[name="cf-turnstile-response"]') return this.turnstileResponse;
        return null;
    }

    insertBefore(element) {
        this.children.push(element);
        if (element.tagName === "p") this.status = element;
        if (element.className === "cf-turnstile") this.widget = element;
    }

    prepend(wrapper) {
        this.children.unshift(wrapper);
        for (const field of wrapper.children) {
            if (field.name) this.fields.set(field.name, field);
        }
    }

    reset() {
        this.resetCount += 1;
    }
}

const form = new FakeForm();
Date.now = () => clock;
globalThis.SPCS_SECURITY_CONFIG = {
    supabaseUrl: "https://project.example.invalid",
    supabasePublishableKey: "test-publishable-key",
    turnstileSiteKey: "test-site-key"
};
globalThis.window = {
    turnstile: {
        render() {
            return "test-widget";
        },
        reset() {}
    }
};
globalThis.document = {
    head: { append() {} },
    createElement(tagName) {
        return new FakeElement(tagName);
    },
    querySelectorAll(selector) {
        return selector === "form#contactForm" ? [form] : [];
    }
};
globalThis.fetch = async (url, options) => {
    fetchCalls.push({ url: String(url), options });
    return nextResponse;
};

await import("../js/enquiry-form.mjs?form-test");
await new Promise((resolve) => setImmediate(resolve));
const submit = form.listeners.submit;

function submitForm() {
    let prevented = false;
    submit({ preventDefault() { prevented = true; } });
    assert.equal(prevented, true);
}

test("normalizes whitespace and accepts a valid enquiry", () => {
    const normalized = normalizeEnquiryValues(validValues);
    assert.equal(normalized.name, "Test Customer");
    assert.equal(isValidEnquiry(normalized), true);
});

test("populates the service selector with every service and Other", () => {
    const options = form.fields.get("service").children;
    assert.deepEqual(
        options.map((option) => option.textContent),
        [
            "Select Service",
            "Termite Treatment",
            "Wood Borer Control",
            "General Pest Control (GPC)",
            "Cockroach Control",
            "Rodent Management",
            "Vector Control & Fogging",
            "Bed Bug Eradication",
            "Commercial Fumigation",
            "Fly Management Systems",
            "Sanitization & Disinfection",
            "Commercial AMC (IPM)",
            "Scorpion Control",
            "Ant Control",
            "Pre-Construction Anti-Termite Treatment",
            "Termite Piping System",
            "Wasp & Hornet Nest Removal",
            "Other"
        ]
    );
});

test("rejects empty, oversized, and malformed fields", () => {
    assert.equal(isValidEnquiry({ ...validValues, name: "" }), false);
    assert.equal(isValidEnquiry({ ...validValues, name: "x".repeat(101) }), false);
    assert.equal(isValidEnquiry({ ...validValues, message: "x".repeat(1001) }), false);
    assert.equal(isValidEnquiry({ ...validValues, phone: "123" }), false);
    assert.equal(isValidEnquiry({ ...validValues, email: "not-an-email" }), false);
});

test("rejects a bot-like submission made before the minimum form time", () => {
    clock += 2999;
    submitForm();
    assert.equal(fetchCalls.length, 0);
    assert.match(form.status.textContent, /could not submit/i);
});

test("submits valid data and treats script markup as text, not HTML", async () => {
    const hostileMessage = "<script>window.pwned=true</script>";
    form.fields.get("message").value = hostileMessage;
    clock += 1;
    submitForm();
    await new Promise((resolve) => setImmediate(resolve));

    assert.equal(fetchCalls.length, 1);
    const payload = JSON.parse(fetchCalls[0].options.body);
    assert.equal(payload.message, hostileMessage);
    assert.equal(form.status.textContent, "Thank you. Your enquiry has been submitted.");
    assert.equal(form.status.innerHTML, undefined);
    assert.equal(form.resetCount, 1);
});

test("does not submit oversized text through the form handler", () => {
    form.fields.get("message").value = "x".repeat(1001);
    clock += 5000;
    submitForm();
    assert.equal(fetchCalls.length, 1);
    assert.match(form.status.textContent, /could not submit/i);
});

test("clearly reports when the enquiry is stored but its email alert fails", async () => {
    const resetCountBefore = form.resetCount;
    form.fields.get("message").value = validValues.message;
    nextResponse = {
        ok: true,
        status: 202,
        async json() {
            return { notification: "failed" };
        }
    };
    clock += 5000;
    submitForm();
    await new Promise((resolve) => setImmediate(resolve));

    assert.equal(fetchCalls.length, 2);
    assert.match(form.status.textContent, /enquiry was received/i);
    assert.match(form.status.textContent, /email alert could not be sent/i);
    assert.equal(form.resetCount, resetCountBefore + 1);
    nextResponse = { ok: true, status: 204 };
});
