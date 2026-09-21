-- RIPPLE PostgreSQL Migration 002: Fine-Grained Row-Level Security (RLS) Policies
-- Enforces tenant isolation, bank officer access, and strict SME isolation (Rule 4.8)

-- =============================================================================
-- 1. AUTH & ROLE HELPER FUNCTIONS
-- =============================================================================

CREATE OR REPLACE FUNCTION public.get_auth_role()
RETURNS TEXT AS $$
    SELECT role FROM public.app_user WHERE id = auth.uid();
$$ LANGUAGE sql STABLE SECURITY DEFINER;

CREATE OR REPLACE FUNCTION public.is_bank_officer()
RETURNS BOOLEAN AS $$
    SELECT COALESCE((SELECT role = 'bank_officer' FROM public.app_user WHERE id = auth.uid()), FALSE);
$$ LANGUAGE sql STABLE SECURITY DEFINER;

CREATE OR REPLACE FUNCTION public.is_admin()
RETURNS BOOLEAN AS $$
    SELECT COALESCE((SELECT role = 'admin' FROM public.app_user WHERE id = auth.uid()), FALSE);
$$ LANGUAGE sql STABLE SECURITY DEFINER;

-- =============================================================================
-- 2. APP USER POLICIES
-- =============================================================================
DROP POLICY IF EXISTS user_read_own ON app_user;
CREATE POLICY user_read_own ON app_user
    FOR SELECT TO authenticated
    USING (id = auth.uid() OR is_admin());

DROP POLICY IF EXISTS user_update_own ON app_user;
CREATE POLICY user_update_own ON app_user
    FOR UPDATE TO authenticated
    USING (id = auth.uid() OR is_admin())
    WITH CHECK (id = auth.uid() OR is_admin());

-- =============================================================================
-- 3. SME POLICIES (Tenant Isolation)
-- =============================================================================
DROP POLICY IF EXISTS sme_bank_read ON sme;
CREATE POLICY sme_bank_read ON sme
    FOR SELECT TO authenticated
    USING (is_bank_officer() OR is_admin());

DROP POLICY IF EXISTS sme_user_read ON sme;
CREATE POLICY sme_user_read ON sme
    FOR SELECT TO authenticated
    USING (user_id = auth.uid());

DROP POLICY IF EXISTS sme_bank_write ON sme;
CREATE POLICY sme_bank_write ON sme
    FOR ALL TO authenticated
    USING (is_bank_officer() OR is_admin())
    WITH CHECK (is_bank_officer() OR is_admin());

-- =============================================================================
-- 4. FINANCIAL RECORD POLICIES
-- =============================================================================
DROP POLICY IF EXISTS fin_bank_all ON financial_record;
CREATE POLICY fin_bank_all ON financial_record
    FOR ALL TO authenticated
    USING (is_bank_officer() OR is_admin())
    WITH CHECK (is_bank_officer() OR is_admin());

DROP POLICY IF EXISTS fin_sme_select ON financial_record;
CREATE POLICY fin_sme_select ON financial_record
    FOR SELECT TO authenticated
    USING (EXISTS (
        SELECT 1 FROM public.sme 
        WHERE sme.id = financial_record.sme_id AND sme.user_id = auth.uid()
    ));

DROP POLICY IF EXISTS fin_sme_insert ON financial_record;
CREATE POLICY fin_sme_insert ON financial_record
    FOR INSERT TO authenticated
    WITH CHECK (EXISTS (
        SELECT 1 FROM public.sme 
        WHERE sme.id = financial_record.sme_id AND sme.user_id = auth.uid()
    ));

-- =============================================================================
-- 5. ASSESSMENT & PREDICTION POLICIES (Bank-Side Internal Data Protection)
-- =============================================================================
-- Bank officers and admins can view and manage all assessments
DROP POLICY IF EXISTS ass_bank_all ON assessment;
CREATE POLICY ass_bank_all ON assessment
    FOR ALL TO authenticated
    USING (is_bank_officer() OR is_admin())
    WITH CHECK (is_bank_officer() OR is_admin());

-- SME users CANNOT view internal bank assessments (SME isolation Rule 4.8)
-- Bank officers and admins only for predictions & explanations
DROP POLICY IF EXISTS pred_bank_all ON prediction;
CREATE POLICY pred_bank_all ON prediction
    FOR ALL TO authenticated
    USING (is_bank_officer() OR is_admin())
    WITH CHECK (is_bank_officer() OR is_admin());

DROP POLICY IF EXISTS exp_bank_all ON explanation;
CREATE POLICY exp_bank_all ON explanation
    FOR ALL TO authenticated
    USING (is_bank_officer() OR is_admin())
    WITH CHECK (is_bank_officer() OR is_admin());

DROP POLICY IF EXISTS scen_bank_all ON scenario_result;
CREATE POLICY scen_bank_all ON scenario_result
    FOR ALL TO authenticated
    USING (is_bank_officer() OR is_admin())
    WITH CHECK (is_bank_officer() OR is_admin());

-- =============================================================================
-- 6. RELATIONSHIPS & DATA QUALITY FLAGS
-- =============================================================================
DROP POLICY IF EXISTS rel_bank_all ON relationship;
CREATE POLICY rel_bank_all ON relationship
    FOR ALL TO authenticated
    USING (is_bank_officer() OR is_admin())
    WITH CHECK (is_bank_officer() OR is_admin());

DROP POLICY IF EXISTS dq_bank_all ON data_quality_flag;
CREATE POLICY dq_bank_all ON data_quality_flag
    FOR ALL TO authenticated
    USING (is_bank_officer() OR is_admin())
    WITH CHECK (is_bank_officer() OR is_admin());

DROP POLICY IF EXISTS dq_sme_select ON data_quality_flag;
CREATE POLICY dq_sme_select ON data_quality_flag
    FOR SELECT TO authenticated
    USING (EXISTS (
        SELECT 1 FROM public.sme 
        WHERE sme.id = data_quality_flag.sme_id AND sme.user_id = auth.uid()
    ));
