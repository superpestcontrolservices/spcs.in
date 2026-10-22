import { securityConfig } from "./security-config.mjs";
import { isValidEnquiry, MAX_LENGTHS, normalizeEnquiryValues } from "./enquiry-validation.mjs";

const MINIMUM_FORM_TIME_MS = 3000;
const GENERIC_ERROR = "We could not submit your enquiry. Please check your details and try again.";
const GENERIC_SUCCESS = "Thank you. Your enquiry has been submitted.";
const NOTIFICATION_WARNING = "Your enquiry was received, but its email alert could not be sent. Please call +91 79765 72984 to ensure we see it.";
const SERVICE_OPTIONS = Object.freeze([
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
    "Wasp & Hornet Nest Removal"
]);

function getField(form, name) {
    return form.elements.namedItem(name);
}

function normalizeFormData(form) {
    const values = {};
    for (const fieldName of Object.keys(MAX_LENGTHS)) {
        const field = getField(form, fieldName);
        values[fieldName] = field?.value;
    }
    return normalizeEnquiryValues(values);
}

function populateServiceOptions(form) {
    const serviceField = getField(form, "service");
    if (serviceField?.tagName !== "SELECT") return;

    const selectedService = serviceField.value;
    const options = ["", ...SERVICE_OPTIONS, "Other"].map((service) => {
        const option = document.createElement("option");
        option.value = service;
        option.textContent = service || "Select Service";
        return option;
    });
    serviceField.replaceChildren(...options);
    if (options.some((option) => option.value === selectedService)) {
        serviceField.value = selectedService;
    }
}

function setStatus(status, message, isError) {
    status.textContent = message;
    status.classList.toggle("form-status-error", isError);
}

function createStatus(form) {
    const status = document.createElement("p");
    status.className = "form-status";
    status.setAttribute("role", "status");
    status.setAttribute("aria-live", "polite");
    const submitButton = form.querySelector('button[type="submit"]');
    if (submitButton) {
        form.insertBefore(status, submitButton);
    } else {
        form.append(status);
    }
    return status;
}

function addHoneypot(form) {
    if (getField(form, "website")) return;

    const wrapper = document.createElement("div");
    wrapper.className = "form-honeypot";
    wrapper.setAttribute("aria-hidden", "true");

    const label = document.createElement("label");
    label.htmlFor = "enquiry-website";
    label.textContent = "Leave this field empty";

    const field = document.createElement("input");
    field.type = "text";
    field.name = "website";
    field.id = "enquiry-website";
    field.tabIndex = -1;
    field.autocomplete = "off";

    wrapper.append(label, field);
    form.prepend(wrapper);
}

function ensureTurnstileContainer(form) {
    let container = form.querySelector(".cf-turnstile");
    if (!container) {
        container = document.createElement("div");
        container.className = "cf-turnstile";
        container.dataset.sitekey = securityConfig.turnstileSiteKey;
        container.dataset.action = "enquiry";
        const submitButton = form.querySelector('button[type="submit"]');
        if (submitButton) {
            form.insertBefore(container, submitButton);
        } else {
            form.append(container);
        }
    }
    return container;
}

function loadTurnstile() {
    if (window.turnstile) return Promise.resolve(window.turnstile);
    if (window.spcsTurnstilePromise) return window.spcsTurnstilePromise;

    window.spcsTurnstilePromise = new Promise((resolve, reject) => {
        const script = document.createElement("script");
        script.src = "https://challenges.cloudflare.com/turnstile/v0/api.js?render=explicit";
        script.async = true;
        script.defer = true;
        script.referrerPolicy = "no-referrer";
        script.onload = () => {
            if (window.turnstile) {
                resolve(window.turnstile);
            } else {
                reject(new Error("Turnstile did not initialize."));
            }
        };
        script.onerror = () => reject(new Error("Turnstile could not be loaded."));
        document.head.append(script);
    });

    return window.spcsTurnstilePromise;
}

function configureForm(form) {
    populateServiceOptions(form);
    const status = createStatus(form);
    addHoneypot(form);

    for (const [fieldName, maxLength] of Object.entries(MAX_LENGTHS)) {
        const field = getField(form, fieldName);
        if (!field) continue;
        field.maxLength = maxLength;
        if (["name", "phone", "email", "service"].includes(fieldName)) {
            field.required = true;
        }
        if (fieldName === "phone") {
            field.inputMode = "numeric";
            field.pattern = "[0-9]{10}";
            field.addEventListener("input", () => {
                field.value = field.value.replace(/[^0-9]/g, "").slice(0, MAX_LENGTHS.phone);
            });
        }
    }

    const turnstileContainer = ensureTurnstileContainer(form);
    let startedAt = Date.now();
    let widgetId;
    let submitting = false;

    const configurationAvailable =
        !securityConfig.supabasePublishableKey.startsWith("REPLACE_") &&
        !securityConfig.turnstileSiteKey.startsWith("REPLACE_");
    if (configurationAvailable) {
        loadTurnstile()
            .then((turnstile) => {
                widgetId = turnstile.render(turnstileContainer, {
                    sitekey: securityConfig.turnstileSiteKey,
                    action: "enquiry"
                });
            })
            .catch(() => setStatus(status, GENERIC_ERROR, true));
    }

    form.addEventListener("submit", async (event) => {
        event.preventDefault();
        if (submitting) return;

        if (getField(form, "website")?.value) {
            setStatus(status, GENERIC_SUCCESS, false);
            form.reset();
            return;
        }

        const values = normalizeFormData(form);
        const token = form.querySelector('[name="cf-turnstile-response"]')?.value || "";
        if (
            Date.now() - startedAt < MINIMUM_FORM_TIME_MS ||
            !isValidEnquiry(values) ||
            token.length === 0 ||
            securityConfig.supabasePublishableKey.startsWith("REPLACE_") ||
            securityConfig.turnstileSiteKey.startsWith("REPLACE_")
        ) {
            setStatus(status, GENERIC_ERROR, true);
            return;
        }

        const submitButton = form.querySelector('button[type="submit"]');
        submitting = true;
        if (submitButton) submitButton.disabled = true;
        setStatus(status, "", false);

        try {
            const endpoint = new URL("/functions/v1/submit-enquiry", securityConfig.supabaseUrl);
            const response = await fetch(endpoint, {
                method: "POST",
                headers: {
                    apikey: securityConfig.supabasePublishableKey,
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    ...values,
                    turnstileToken: token,
                    website: ""
                })
            });

            if (!response.ok) throw new Error("Enquiry submission failed.");

            if (response.status === 202) {
                const result = await response.json();
                if (result.notification !== "failed") {
                    throw new Error("Enquiry notification status was invalid.");
                }
                setStatus(status, NOTIFICATION_WARNING, true);
            } else {
                setStatus(status, GENERIC_SUCCESS, false);
            }
            form.reset();
            startedAt = Date.now();
            if (widgetId !== undefined && window.turnstile) {
                window.turnstile.reset(widgetId);
            }
        } catch {
            setStatus(status, GENERIC_ERROR, true);
            if (widgetId !== undefined && window.turnstile) {
                window.turnstile.reset(widgetId);
            }
        } finally {
            submitting = false;
            if (submitButton) submitButton.disabled = false;
        }
    });
}

function initializeForms() {
    document.querySelectorAll("form#contactForm").forEach(configureForm);
}

const securityStyles = document.createElement("link");
securityStyles.rel = "stylesheet";
securityStyles.href = "/css/security.css";
document.head.append(securityStyles);
initializeForms();
