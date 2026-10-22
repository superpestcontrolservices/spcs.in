-- Review the project/table inventory below before running this file.
-- This script is intentionally not executed by the repository changes.
-- It changes access policies and grants; it does not delete customer rows or drop existing tables.

BEGIN;

CREATE TABLE IF NOT EXISTS public.enquiry_rate_limits (
    ip_hash text PRIMARY KEY
        CHECK (ip_hash ~ '^[a-f0-9]{64}$'),
    window_started_at timestamptz NOT NULL,
    request_count integer NOT NULL CHECK (request_count > 0)
);

CREATE INDEX IF NOT EXISTS enquiry_rate_limits_window_started_at_idx
    ON public.enquiry_rate_limits (window_started_at);

ALTER TABLE public.enquiry_rate_limits ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON TABLE public.enquiry_rate_limits FROM PUBLIC, anon, authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE public.enquiry_rate_limits TO service_role;

-- Apply RLS to every ordinary or partitioned table in the public schema.
DO $$
DECLARE
    table_record record;
    policy_record record;
    owner_policy_name text;
BEGIN
    FOR table_record IN
        SELECT c.relname AS table_name
        FROM pg_class AS c
        JOIN pg_namespace AS n ON n.oid = c.relnamespace
        WHERE n.nspname = 'public'
          AND c.relkind IN ('r', 'p')
    LOOP
        EXECUTE format(
            'ALTER TABLE public.%I ENABLE ROW LEVEL SECURITY',
            table_record.table_name
        );

        IF table_record.table_name IN ('enquiries', 'enquiry_rate_limits') THEN
            CONTINUE;
        END IF;

        EXECUTE format(
            'REVOKE ALL ON TABLE public.%I FROM PUBLIC, anon, authenticated',
            table_record.table_name
        );

        -- Existing policies can be broader than the owner-only rule below.
        FOR policy_record IN
            SELECT policyname
            FROM pg_policies
            WHERE schemaname = 'public'
              AND tablename = table_record.table_name
        LOOP
            EXECUTE format(
                'DROP POLICY %I ON public.%I',
                policy_record.policyname,
                table_record.table_name
            );
        END LOOP;

        IF EXISTS (
            SELECT 1
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND table_name = table_record.table_name
              AND column_name = 'owner_id'
        ) THEN
            owner_policy_name := 'owner_access_' || left(table_record.table_name, 40);
            EXECUTE format(
                'GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE public.%I TO authenticated',
                table_record.table_name
            );
            EXECUTE format(
                'CREATE POLICY %I ON public.%I FOR ALL TO authenticated '
                'USING (owner_id::text = (SELECT auth.uid()::text)) '
                'WITH CHECK (owner_id::text = (SELECT auth.uid()::text))',
                owner_policy_name,
                table_record.table_name
            );
        ELSE
            RAISE NOTICE
                'Table public.% has no owner_id column; it remains inaccessible to anon/authenticated. Review whether it belongs in public.',
                table_record.table_name;
        END IF;
    END LOOP;
END
$$;

-- The public enquiry table accepts anonymous inserts only. Remove existing policies
-- so a former permissive policy cannot accidentally restore public reads or writes.
REVOKE ALL ON TABLE public.enquiries FROM PUBLIC, anon, authenticated;
DO $$
DECLARE
    policy_record record;
    sequence_record record;
BEGIN
    FOR policy_record IN
        SELECT policyname
        FROM pg_policies
        WHERE schemaname = 'public'
          AND tablename = 'enquiries'
    LOOP
        EXECUTE format('DROP POLICY %I ON public.enquiries', policy_record.policyname);
    END LOOP;

    -- Allow anonymous inserts to use only a sequence owned by enquiries, if one exists.
    FOR sequence_record IN
        SELECT sequence_ns.nspname AS schema_name, sequence.relname AS sequence_name
        FROM pg_class AS sequence
        JOIN pg_namespace AS sequence_ns ON sequence_ns.oid = sequence.relnamespace
        JOIN pg_depend AS dependency ON dependency.objid = sequence.oid
        WHERE sequence.relkind = 'S'
          AND dependency.refobjid = 'public.enquiries'::regclass
    LOOP
        EXECUTE format(
            'GRANT USAGE, SELECT ON SEQUENCE %I.%I TO anon',
            sequence_record.schema_name,
            sequence_record.sequence_name
        );
    END LOOP;
END
$$;

GRANT INSERT (name, phone, email, service, message, status)
    ON TABLE public.enquiries TO anon;
GRANT SELECT ON TABLE public.enquiries TO authenticated;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conrelid = 'public.enquiries'::regclass
          AND conname = 'enquiries_name_valid'
    ) THEN
        ALTER TABLE public.enquiries
            ADD CONSTRAINT enquiries_name_valid
            CHECK (name IS NOT NULL AND char_length(btrim(name)) BETWEEN 1 AND 100)
            NOT VALID;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conrelid = 'public.enquiries'::regclass
          AND conname = 'enquiries_phone_valid'
    ) THEN
        ALTER TABLE public.enquiries
            ADD CONSTRAINT enquiries_phone_valid
            CHECK (phone IS NOT NULL AND phone ~ '^[0-9]{10}$')
            NOT VALID;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conrelid = 'public.enquiries'::regclass
          AND conname = 'enquiries_email_valid'
    ) THEN
        ALTER TABLE public.enquiries
            ADD CONSTRAINT enquiries_email_valid
            CHECK (
                email IS NOT NULL
                AND char_length(email) <= 254
                AND email ~ '^[^[:space:]@]+@[^[:space:]@]+\.[^[:space:]@]+$'
            )
            NOT VALID;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conrelid = 'public.enquiries'::regclass
          AND conname = 'enquiries_service_valid'
    ) THEN
        ALTER TABLE public.enquiries
            ADD CONSTRAINT enquiries_service_valid
            CHECK (
                service IS NOT NULL
                AND char_length(btrim(service)) BETWEEN 1 AND 100
            )
            NOT VALID;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conrelid = 'public.enquiries'::regclass
          AND conname = 'enquiries_message_valid'
    ) THEN
        ALTER TABLE public.enquiries
            ADD CONSTRAINT enquiries_message_valid
            CHECK (message IS NULL OR char_length(message) <= 1000)
            NOT VALID;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conrelid = 'public.enquiries'::regclass
          AND conname = 'enquiries_status_valid'
    ) THEN
        ALTER TABLE public.enquiries
            ADD CONSTRAINT enquiries_status_valid
            CHECK (status IS NULL OR char_length(status) <= 30)
            NOT VALID;
    END IF;
END
$$;

CREATE POLICY enquiries_anon_insert
    ON public.enquiries
    FOR INSERT
    TO anon
    WITH CHECK (
        name IS NOT NULL
        AND char_length(btrim(name)) BETWEEN 1 AND 100
        AND phone IS NOT NULL
        AND phone ~ '^[0-9]{10}$'
        AND email IS NOT NULL
        AND char_length(email) <= 254
        AND email ~ '^[^[:space:]@]+@[^[:space:]@]+\.[^[:space:]@]+$'
        AND service IS NOT NULL
        AND char_length(btrim(service)) BETWEEN 1 AND 100
        AND (message IS NULL OR char_length(message) <= 1000)
        AND status = 'New'
    );

-- Replace YOUR-USER-UUID with the administrator's authenticated Supabase user UUID.
-- This grants that user SELECT only; it does not grant authenticated updates/deletes.
CREATE POLICY enquiries_owner_select
    ON public.enquiries
    FOR SELECT
    TO authenticated
    USING (auth.uid()::text = 'YOUR-USER-UUID');

-- This RPC is callable only by the Edge Function using the service-role secret.
CREATE OR REPLACE FUNCTION public.check_enquiry_rate_limit(p_ip_hash text)
RETURNS boolean
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, public
AS $$
DECLARE
    is_allowed boolean;
BEGIN
    IF coalesce(current_setting('request.jwt.claim.role', true), '') <> 'service_role' THEN
        RAISE EXCEPTION 'forbidden' USING ERRCODE = '42501';
    END IF;

    IF p_ip_hash IS NULL OR p_ip_hash !~ '^[a-f0-9]{64}$' THEN
        RAISE EXCEPTION 'invalid rate-limit key' USING ERRCODE = '22023';
    END IF;

    INSERT INTO public.enquiry_rate_limits (ip_hash, window_started_at, request_count)
    VALUES (p_ip_hash, now(), 1)
    ON CONFLICT (ip_hash) DO UPDATE
    SET window_started_at = CASE
            WHEN public.enquiry_rate_limits.window_started_at <= now() - interval '10 minutes'
                THEN now()
            ELSE public.enquiry_rate_limits.window_started_at
        END,
        request_count = CASE
            WHEN public.enquiry_rate_limits.window_started_at <= now() - interval '10 minutes'
                THEN 1
            ELSE public.enquiry_rate_limits.request_count + 1
        END
    RETURNING request_count <= 5 INTO is_allowed;

    DELETE FROM public.enquiry_rate_limits
    WHERE window_started_at < now() - interval '24 hours';

    RETURN is_allowed;
END;
$$;

REVOKE ALL ON FUNCTION public.check_enquiry_rate_limit(text) FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.check_enquiry_rate_limit(text) TO service_role;

COMMIT;

-- Inspection queries to run separately in the SQL Editor:
-- 1. First inventory every table, its columns, and current RLS state using the
--    queries below. Resolve unexpected tables and confirm enquiries column names.
-- 2. Replace YOUR-USER-UUID with the administrator's authenticated user UUID.
-- 3. Review the policy/grant changes in this file, then run the executable section
--    as one script in Supabase Dashboard -> SQL Editor. Do not run against an
--    unconfirmed project. A SQL error should roll back the transaction.
-- 4. Re-run the table, policy, storage, and SECURITY DEFINER queries below. Confirm
--    every public table has rowsecurity enabled and no anon SELECT/UPDATE/DELETE grant.
-- 5. In Supabase Dashboard -> Security Advisor, re-check and resolve or document
--    every applicable warning before considering the hardening complete.
--
-- SELECT schemaname, tablename, rowsecurity FROM pg_tables
-- WHERE schemaname = 'public' ORDER BY tablename;
--
-- SELECT table_name, column_name, data_type
-- FROM information_schema.columns
-- WHERE table_schema = 'public' ORDER BY table_name, ordinal_position;
--
-- SELECT schemaname, tablename, policyname, roles, cmd, qual, with_check
-- FROM pg_policies WHERE schemaname IN ('public', 'storage')
-- ORDER BY schemaname, tablename, policyname;
--
-- SELECT n.nspname AS schema_name, p.proname AS function_name,
--        pg_get_function_identity_arguments(p.oid) AS arguments
-- FROM pg_proc AS p JOIN pg_namespace AS n ON n.oid = p.pronamespace
-- WHERE p.prosecdef ORDER BY n.nspname, p.proname;
--
-- SELECT id, name, public FROM storage.buckets ORDER BY name;
--
-- IMPORTANT: Review storage.buckets and storage policies from the queries above.
-- Make buckets private by default; create narrowly scoped policies only for assets
-- that are intentionally public. This script does not change storage policies.
--
-- ROLLBACK / recovery notes:
-- 1. Review Security Advisor and application impact before undoing access controls.
-- 2. To roll back an individual policy, use DROP POLICY <policy_name> ON <table>;
--    then restore only the reviewed grants/policies recorded before this script.
-- 3. To disable the RPC without dropping a table, revoke service_role execution:
--    REVOKE EXECUTE ON FUNCTION public.check_enquiry_rate_limit(text) FROM service_role;
-- 4. Remove or disable the Edge Function separately if required. Keep the rate-limit
--    table and its hashed IP metadata for review; do not drop tables or enquiry data.
-- 5. Constraints added NOT VALID still enforce new writes. Validate them only after
--    existing rows have been reviewed and corrected through an approved process.
