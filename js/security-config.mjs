// Only public publishable and site keys belong in this browser configuration.
// Never place server-only credentials or private secrets here.
const defaults = Object.freeze({
    supabaseUrl: "https://yrxymyoegbxjssrcvjwr.supabase.co",
    supabasePublishableKey: "sb_publishable_g_Gi-0zj6XXOUrxt5pYrPA_uR-Pchu0",
    turnstileSiteKey: "0x4AAAAAAFgUEYZ4Bjg5Jmh4"
});

export const securityConfig = globalThis.SPCS_SECURITY_CONFIG || defaults;
