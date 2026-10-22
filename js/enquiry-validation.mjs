export const MAX_LENGTHS = Object.freeze({
    name: 100,
    phone: 10,
    email: 254,
    service: 100,
    message: 1000
});

export function normalizeEnquiryValues(values) {
    return Object.fromEntries(
        Object.keys(MAX_LENGTHS).map((fieldName) => [
            fieldName,
            typeof values[fieldName] === "string" ? values[fieldName].trim() : ""
        ])
    );
}

export function isValidEnquiry(values) {
    return (
        typeof values.name === "string" &&
        values.name.length > 0 &&
        values.name.length <= MAX_LENGTHS.name &&
        typeof values.phone === "string" &&
        /^[0-9]{10}$/.test(values.phone) &&
        typeof values.email === "string" &&
        values.email.length <= MAX_LENGTHS.email &&
        /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(values.email) &&
        typeof values.service === "string" &&
        values.service.length > 0 &&
        values.service.length <= MAX_LENGTHS.service &&
        typeof values.message === "string" &&
        values.message.length <= MAX_LENGTHS.message
    );
}
