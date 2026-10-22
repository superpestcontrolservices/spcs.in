-- Restrict access only to the enquiry data and its rate-limit table.
-- Review the current Supabase project before running this in its SQL Editor.
BEGIN;

ALTER TABLE public.enquiries ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON TABLE public.enquiries FROM PUBLIC, anon, authenticated;
GRANT ALL ON TABLE public.enquiries TO service_role;

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

    FOR sequence_record IN
        SELECT sequence_ns.nspname AS schema_name, sequence.relname AS sequence_name
        FROM pg_class AS sequence
        JOIN pg_namespace AS sequence_ns ON sequence_ns.oid = sequence.relnamespace
        JOIN pg_depend AS dependency ON dependency.objid = sequence.oid
        WHERE sequence.relkind = 'S'
          AND dependency.refobjid = 'public.enquiries'::regclass
    LOOP
        EXECUTE format(
            'GRANT USAGE, SELECT ON SEQUENCE %I.%I TO service_role',
            sequence_record.schema_name,
            sequence_record.sequence_name
        );
    END LOOP;
END
$$;

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
GRANT ALL ON TABLE public.enquiry_rate_limits TO service_role;

DO $$
DECLARE
    policy_record record;
BEGIN
    FOR policy_record IN
        SELECT policyname
        FROM pg_policies
        WHERE schemaname = 'public'
          AND tablename = 'enquiry_rate_limits'
    LOOP
        EXECUTE format(
            'DROP POLICY %I ON public.enquiry_rate_limits',
            policy_record.policyname
        );
    END LOOP;
END
$$;

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
