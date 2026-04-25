--
-- PostgreSQL database dump
--

\restrict u9ny21fuboi1BufdeH72acIK6tYReP9O8Dvk0ihu8ezXsW8eOz5UcLWiS01XNGu

-- Dumped from database version 13.23
-- Dumped by pg_dump version 14.20 (Homebrew)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: care_site; Type: TABLE; Schema: scd; Owner: sascs
--

CREATE TABLE scd.care_site (
    care_site_id integer NOT NULL,
    care_site_name character varying(255),
    place_of_service_concept_id integer,
    location_id integer,
    care_site_source_value character varying(50),
    place_of_service_source_value character varying(50)
);


ALTER TABLE scd.care_site OWNER TO sascs;

--
-- Name: case_info; Type: TABLE; Schema: scd; Owner: sascs
--

CREATE TABLE scd.case_info (
    case_info_id bigint NOT NULL,
    patient_identifier character varying(510) NOT NULL,
    person_id integer NOT NULL,
    activated_datetime timestamp without time zone,
    created_datetime timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    job_id character varying(50),
    status character varying(50) NOT NULL,
    status_url character varying(255),
    server_url character varying(255) NOT NULL,
    trigger_at_datetime timestamp without time zone,
    last_updated_datetime timestamp without time zone,
    server_host character varying(255) NOT NULL,
    tries_left integer DEFAULT 3,
    last_successful_datetime timestamp without time zone,
    case_started_running_datetime timestamp without time zone
);


ALTER TABLE scd.case_info OWNER TO sascs;

--
-- Name: TABLE case_info; Type: COMMENT; Schema: scd; Owner: sascs
--

COMMENT ON TABLE scd.case_info IS 'Syphilis Registry Case Management';


--
-- Name: case_log; Type: TABLE; Schema: scd; Owner: sascs
--

CREATE TABLE scd.case_log (
    case_log_id bigint NOT NULL,
    case_info_id bigint NOT NULL,
    log_datetime timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    text text
);


ALTER TABLE scd.case_log OWNER TO sascs;

--
-- Name: TABLE case_log; Type: COMMENT; Schema: scd; Owner: sascs
--

COMMENT ON TABLE scd.case_log IS 'Logging all session operations';


--
-- Name: cdm_source; Type: TABLE; Schema: scd; Owner: sascs
--

CREATE TABLE scd.cdm_source (
    cdm_source_name character varying(255) NOT NULL,
    cdm_source_abbreviation character varying(25) NOT NULL,
    cdm_holder character varying(255) NOT NULL,
    source_description text,
    source_documentation_reference character varying(255),
    cdm_etl_reference character varying(255),
    source_release_date date NOT NULL,
    cdm_release_date date NOT NULL,
    cdm_version character varying(10),
    cdm_version_concept_id integer NOT NULL,
    vocabulary_version character varying(20) NOT NULL
);


ALTER TABLE scd.cdm_source OWNER TO sascs;

--
-- Name: cohort; Type: TABLE; Schema: scd; Owner: sascs
--

CREATE TABLE scd.cohort (
    cohort_definition_id integer NOT NULL,
    subject_id integer NOT NULL,
    cohort_start_date date NOT NULL,
    cohort_end_date date NOT NULL
);


ALTER TABLE scd.cohort OWNER TO sascs;

--
-- Name: cohort_definition; Type: TABLE; Schema: scd; Owner: sascs
--

CREATE TABLE scd.cohort_definition (
    cohort_definition_id integer NOT NULL,
    cohort_definition_name character varying(255) NOT NULL,
    cohort_definition_description text,
    definition_type_concept_id integer NOT NULL,
    cohort_definition_syntax text,
    subject_concept_id integer NOT NULL,
    cohort_initiation_date date
);


ALTER TABLE scd.cohort_definition OWNER TO sascs;

--
-- Name: concept; Type: TABLE; Schema: scd; Owner: sascs
--

CREATE TABLE scd.concept (
    concept_id integer NOT NULL,
    concept_name character varying(255) NOT NULL,
    domain_id character varying(20) NOT NULL,
    vocabulary_id character varying(20) NOT NULL,
    concept_class_id character varying(20) NOT NULL,
    standard_concept character varying(1),
    concept_code character varying(50) NOT NULL,
    valid_start_date date NOT NULL,
    valid_end_date date NOT NULL,
    invalid_reason character varying(1)
);


ALTER TABLE scd.concept OWNER TO sascs;

--
-- Name: concept_ancestor; Type: TABLE; Schema: scd; Owner: sascs
--

CREATE TABLE scd.concept_ancestor (
    ancestor_concept_id integer NOT NULL,
    descendant_concept_id integer NOT NULL,
    min_levels_of_separation integer NOT NULL,
    max_levels_of_separation integer NOT NULL
);


ALTER TABLE scd.concept_ancestor OWNER TO sascs;

--
-- Name: concept_class; Type: TABLE; Schema: scd; Owner: sascs
--

CREATE TABLE scd.concept_class (
    concept_class_id character varying(20) NOT NULL,
    concept_class_name character varying(255) NOT NULL,
    concept_class_concept_id integer NOT NULL
);


ALTER TABLE scd.concept_class OWNER TO sascs;

--
-- Name: concept_relationship; Type: TABLE; Schema: scd; Owner: sascs
--

CREATE TABLE scd.concept_relationship (
    concept_id_1 integer NOT NULL,
    concept_id_2 integer NOT NULL,
    relationship_id character varying(20) NOT NULL,
    valid_start_date date NOT NULL,
    valid_end_date date NOT NULL,
    invalid_reason character varying(1)
);


ALTER TABLE scd.concept_relationship OWNER TO sascs;

--
-- Name: concept_synonym; Type: TABLE; Schema: scd; Owner: sascs
--

CREATE TABLE scd.concept_synonym (
    concept_id integer NOT NULL,
    concept_synonym_name character varying(1000) NOT NULL,
    language_concept_id integer NOT NULL
);


ALTER TABLE scd.concept_synonym OWNER TO sascs;

--
-- Name: condition_era; Type: TABLE; Schema: scd; Owner: sascs
--

CREATE TABLE scd.condition_era (
    condition_era_id integer NOT NULL,
    person_id integer NOT NULL,
    condition_concept_id integer NOT NULL,
    condition_era_start_date timestamp without time zone NOT NULL,
    condition_era_end_date timestamp without time zone NOT NULL,
    condition_occurrence_count integer
);


ALTER TABLE scd.condition_era OWNER TO sascs;

--
-- Name: condition_occurrence; Type: TABLE; Schema: scd; Owner: sascs
--

CREATE TABLE scd.condition_occurrence (
    condition_occurrence_id integer NOT NULL,
    person_id integer NOT NULL,
    condition_concept_id integer NOT NULL,
    condition_start_date date NOT NULL,
    condition_start_datetime timestamp without time zone,
    condition_end_date date,
    condition_end_datetime timestamp without time zone,
    condition_type_concept_id integer NOT NULL,
    condition_status_concept_id integer,
    stop_reason character varying(20),
    provider_id integer,
    visit_occurrence_id integer,
    visit_detail_id integer,
    condition_source_value character varying(50),
    condition_source_concept_id integer,
    condition_status_source_value character varying(50)
);


ALTER TABLE scd.condition_occurrence OWNER TO sascs;

--
-- Name: cost; Type: TABLE; Schema: scd; Owner: sascs
--

CREATE TABLE scd.cost (
    cost_id integer NOT NULL,
    cost_event_id integer NOT NULL,
    cost_domain_id character varying(20) NOT NULL,
    cost_type_concept_id integer NOT NULL,
    currency_concept_id integer,
    total_charge numeric,
    total_cost numeric,
    total_paid numeric,
    paid_by_payer numeric,
    paid_by_patient numeric,
    paid_patient_copay numeric,
    paid_patient_coinsurance numeric,
    paid_patient_deductible numeric,
    paid_by_primary numeric,
    paid_ingredient_cost numeric,
    paid_dispensing_fee numeric,
    payer_plan_period_id integer,
    amount_allowed numeric,
    revenue_code_concept_id integer,
    revenue_code_source_value character varying(50),
    drg_concept_id integer,
    drg_source_value character varying(3)
);


ALTER TABLE scd.cost OWNER TO sascs;

--
-- Name: death; Type: TABLE; Schema: scd; Owner: sascs
--

CREATE TABLE scd.death (
    person_id integer NOT NULL,
    death_date date NOT NULL,
    death_datetime timestamp without time zone,
    death_type_concept_id integer,
    cause_concept_id integer,
    cause_source_value character varying(50),
    cause_source_concept_id integer
);


ALTER TABLE scd.death OWNER TO sascs;

--
-- Name: device_exposure; Type: TABLE; Schema: scd; Owner: sascs
--

CREATE TABLE scd.device_exposure (
    device_exposure_id integer NOT NULL,
    person_id integer NOT NULL,
    device_concept_id integer NOT NULL,
    device_exposure_start_date date NOT NULL,
    device_exposure_start_datetime timestamp without time zone,
    device_exposure_end_date date,
    device_exposure_end_datetime timestamp without time zone,
    device_type_concept_id integer NOT NULL,
    unique_device_id character varying(255),
    production_id character varying(255),
    quantity integer,
    provider_id integer,
    visit_occurrence_id integer,
    visit_detail_id integer,
    device_source_value character varying(50),
    device_source_concept_id integer,
    unit_concept_id integer,
    unit_source_value character varying(50),
    unit_source_concept_id integer
);


ALTER TABLE scd.device_exposure OWNER TO sascs;

--
-- Name: domain; Type: TABLE; Schema: scd; Owner: sascs
--

CREATE TABLE scd.domain (
    domain_id character varying(20) NOT NULL,
    domain_name character varying(255) NOT NULL,
    domain_concept_id integer NOT NULL
);


ALTER TABLE scd.domain OWNER TO sascs;

--
-- Name: dose_era; Type: TABLE; Schema: scd; Owner: sascs
--

CREATE TABLE scd.dose_era (
    dose_era_id integer NOT NULL,
    person_id integer NOT NULL,
    drug_concept_id integer NOT NULL,
    unit_concept_id integer NOT NULL,
    dose_value numeric NOT NULL,
    dose_era_start_date timestamp without time zone NOT NULL,
    dose_era_end_date timestamp without time zone NOT NULL
);


ALTER TABLE scd.dose_era OWNER TO sascs;

--
-- Name: drug_era; Type: TABLE; Schema: scd; Owner: sascs
--

CREATE TABLE scd.drug_era (
    drug_era_id integer NOT NULL,
    person_id integer NOT NULL,
    drug_concept_id integer NOT NULL,
    drug_era_start_date timestamp without time zone NOT NULL,
    drug_era_end_date timestamp without time zone NOT NULL,
    drug_exposure_count integer,
    gap_days integer
);


ALTER TABLE scd.drug_era OWNER TO sascs;

--
-- Name: drug_exposure; Type: TABLE; Schema: scd; Owner: sascs
--

CREATE TABLE scd.drug_exposure (
    drug_exposure_id integer NOT NULL,
    person_id integer NOT NULL,
    drug_concept_id integer NOT NULL,
    drug_exposure_start_date date NOT NULL,
    drug_exposure_start_datetime timestamp without time zone,
    drug_exposure_end_date date NOT NULL,
    drug_exposure_end_datetime timestamp without time zone,
    verbatim_end_date date,
    drug_type_concept_id integer NOT NULL,
    stop_reason character varying(20),
    refills integer,
    quantity numeric,
    days_supply integer,
    sig text,
    route_concept_id integer,
    lot_number character varying(50),
    provider_id integer,
    visit_occurrence_id integer,
    visit_detail_id integer,
    drug_source_value character varying(50),
    drug_source_concept_id integer,
    route_source_value character varying(50),
    dose_unit_source_value character varying(50)
);


ALTER TABLE scd.drug_exposure OWNER TO sascs;

--
-- Name: drug_strength; Type: TABLE; Schema: scd; Owner: sascs
--

CREATE TABLE scd.drug_strength (
    drug_concept_id integer NOT NULL,
    ingredient_concept_id integer NOT NULL,
    amount_value numeric,
    amount_unit_concept_id integer,
    numerator_value numeric,
    numerator_unit_concept_id integer,
    denominator_value numeric,
    denominator_unit_concept_id integer,
    box_size integer,
    valid_start_date date NOT NULL,
    valid_end_date date NOT NULL,
    invalid_reason character varying(1)
);


ALTER TABLE scd.drug_strength OWNER TO sascs;

--
-- Name: episode; Type: TABLE; Schema: scd; Owner: sascs
--

CREATE TABLE scd.episode (
    episode_id bigint NOT NULL,
    person_id bigint NOT NULL,
    episode_concept_id integer NOT NULL,
    episode_start_date date NOT NULL,
    episode_start_datetime timestamp without time zone,
    episode_end_date date,
    episode_end_datetime timestamp without time zone,
    episode_parent_id bigint,
    episode_number integer,
    episode_object_concept_id integer NOT NULL,
    episode_type_concept_id integer NOT NULL,
    episode_source_value character varying(50),
    episode_source_concept_id integer
);


ALTER TABLE scd.episode OWNER TO sascs;

--
-- Name: episode_event; Type: TABLE; Schema: scd; Owner: sascs
--

CREATE TABLE scd.episode_event (
    episode_id bigint NOT NULL,
    event_id bigint NOT NULL,
    episode_event_field_concept_id integer NOT NULL
);


ALTER TABLE scd.episode_event OWNER TO sascs;

--
-- Name: f_cache; Type: TABLE; Schema: scd; Owner: sascs
--

CREATE TABLE scd.f_cache (
    cache_id integer NOT NULL,
    key_text text NOT NULL,
    value_text text,
    value_int integer,
    status integer DEFAULT '-1'::integer
);


ALTER TABLE scd.f_cache OWNER TO sascs;

--
-- Name: procedure_occurrence; Type: TABLE; Schema: scd; Owner: sascs
--

CREATE TABLE scd.procedure_occurrence (
    procedure_occurrence_id integer NOT NULL,
    person_id integer NOT NULL,
    procedure_concept_id integer NOT NULL,
    procedure_date date NOT NULL,
    procedure_datetime timestamp without time zone,
    procedure_end_date date,
    procedure_end_datetime timestamp without time zone,
    procedure_type_concept_id integer NOT NULL,
    modifier_concept_id integer,
    quantity integer,
    provider_id integer,
    visit_occurrence_id integer,
    visit_detail_id integer,
    procedure_source_value character varying(50),
    procedure_source_concept_id integer,
    modifier_source_value character varying(50)
);


ALTER TABLE scd.procedure_occurrence OWNER TO sascs;

--
-- Name: f_immunization_view; Type: VIEW; Schema: scd; Owner: sascs
--

CREATE VIEW scd.f_immunization_view AS
 SELECT d.drug_exposure_id AS immunization_id,
    d.person_id,
    d.drug_concept_id AS immunization_concept_id,
    d.drug_exposure_start_date AS immunization_date,
    d.drug_exposure_start_datetime AS immunization_datetime,
    d.drug_type_concept_id AS immunization_type_concept_id,
    d.stop_reason AS immunization_status,
    d.provider_id,
    d.visit_occurrence_id,
    d.lot_number,
    d.route_concept_id,
    d.quantity,
    d.sig AS immunization_note
   FROM (scd.drug_exposure d
     JOIN scd.concept c ON ((d.drug_concept_id = c.concept_id)))
  WHERE ((((c.vocabulary_id)::text = ANY ((ARRAY['NDC'::character varying, 'RxNorm'::character varying, 'CPT4'::character varying, 'HCPCS'::character varying])::text[])) AND ((c.concept_class_id)::text <> ALL ((ARRAY['CPT4 Modifier'::character varying, 'CPT4 Hierarchy'::character varying, 'HCPCS Class'::character varying, 'HCPCS Modifier'::character varying, 'Place of Service'::character varying])::text[])) AND ((lower((c.concept_name)::text) ~~ '%vacc%'::text) OR (lower((c.concept_name)::text) ~~ '%immuniz%'::text) OR (lower((c.concept_name)::text) ~~ '%toxoid%'::text)) AND ((c.domain_id)::text = 'Drug'::text)) OR ((c.vocabulary_id)::text = 'CVX'::text))
UNION ALL
 SELECT (- p.procedure_occurrence_id) AS immunization_id,
    p.person_id,
    p.procedure_concept_id AS immunization_concept_id,
    p.procedure_date AS immunization_date,
    p.procedure_datetime AS immunization_datetime,
    p.procedure_type_concept_id AS immunization_type_concept_id,
    NULL::character varying AS immunization_status,
    p.provider_id,
    p.visit_occurrence_id,
    NULL::character varying AS lot_number,
    NULL::integer AS route_concept_id,
    p.quantity,
    NULL::text AS immunization_note
   FROM (scd.procedure_occurrence p
     JOIN scd.concept c ON ((p.procedure_concept_id = c.concept_id)))
  WHERE ((((c.vocabulary_id)::text = ANY ((ARRAY['NDC'::character varying, 'RxNorm'::character varying, 'CPT4'::character varying, 'HCPCS'::character varying])::text[])) AND ((c.concept_class_id)::text <> ALL ((ARRAY['CPT4 Modifier'::character varying, 'CPT4 Hierarchy'::character varying, 'HCPCS Class'::character varying, 'HCPCS Modifier'::character varying, 'Place of Service'::character varying])::text[])) AND ((lower((c.concept_name)::text) ~~ '%vacc%'::text) OR (lower((c.concept_name)::text) ~~ '%immuniz%'::text) OR (lower((c.concept_name)::text) ~~ '%toxoid%'::text)) AND ((c.domain_id)::text = 'Drug'::text)) OR ((c.vocabulary_id)::text = 'CVX'::text));


ALTER TABLE scd.f_immunization_view OWNER TO sascs;

--
-- Name: measurement; Type: TABLE; Schema: scd; Owner: sascs
--

CREATE TABLE scd.measurement (
    measurement_id integer NOT NULL,
    person_id integer NOT NULL,
    measurement_concept_id integer NOT NULL,
    measurement_date date NOT NULL,
    measurement_datetime timestamp without time zone,
    measurement_time character varying(10),
    measurement_type_concept_id integer NOT NULL,
    operator_concept_id integer,
    value_as_number numeric,
    value_as_concept_id integer,
    unit_concept_id integer,
    range_low numeric,
    range_high numeric,
    provider_id integer,
    visit_occurrence_id integer,
    visit_detail_id integer,
    measurement_source_value character varying(50),
    measurement_source_concept_id integer,
    unit_source_value character varying(50),
    unit_source_concept_id integer,
    value_source_value character varying(500),
    measurement_event_id bigint,
    meas_event_field_concept_id integer
);


ALTER TABLE scd.measurement OWNER TO sascs;

--
-- Name: observation; Type: TABLE; Schema: scd; Owner: sascs
--

CREATE TABLE scd.observation (
    observation_id integer NOT NULL,
    person_id integer NOT NULL,
    observation_concept_id integer NOT NULL,
    observation_date date NOT NULL,
    observation_datetime timestamp without time zone,
    observation_type_concept_id integer NOT NULL,
    value_as_number numeric,
    value_as_string character varying(500),
    value_as_concept_id integer,
    qualifier_concept_id integer,
    unit_concept_id integer,
    provider_id integer,
    visit_occurrence_id integer,
    visit_detail_id integer,
    observation_source_value character varying(500),
    observation_source_concept_id integer,
    unit_source_value character varying(50),
    qualifier_source_value character varying(50),
    value_source_value character varying(50),
    observation_event_id bigint,
    obs_event_field_concept_id integer
);


ALTER TABLE scd.observation OWNER TO sascs;

--
-- Name: f_observation_view; Type: VIEW; Schema: scd; Owner: sascs
--

CREATE VIEW scd.f_observation_view AS
 SELECT measurement.measurement_id AS observation_id,
    measurement.person_id,
    measurement.measurement_concept_id AS observation_concept_id,
    measurement.measurement_date AS observation_date,
    measurement.measurement_datetime AS observation_datetime,
    measurement.measurement_time AS observation_time,
    measurement.measurement_type_concept_id AS observation_type_concept_id,
    measurement.operator_concept_id AS observation_operator_concept_id,
    measurement.value_as_number,
    NULL::character varying AS value_as_string,
    measurement.value_as_concept_id,
    NULL::integer AS qualifier_concept_id,
    measurement.unit_concept_id,
    measurement.range_low,
    measurement.range_high,
    measurement.provider_id,
    measurement.visit_occurrence_id,
    measurement.visit_detail_id,
    measurement.measurement_source_value AS observation_source_value,
    measurement.measurement_source_concept_id AS observation_source_concept_id,
    measurement.unit_source_value,
    NULL::character varying AS qualifier_source_value,
    measurement.unit_source_concept_id,
    measurement.value_source_value,
    measurement.measurement_event_id AS observation_event_id,
    measurement.meas_event_field_concept_id AS obs_event_field_concept_id
   FROM scd.measurement
UNION ALL
 SELECT (- observation.observation_id) AS observation_id,
    observation.person_id,
    observation.observation_concept_id,
    observation.observation_date,
    observation.observation_datetime,
    NULL::character varying AS observation_time,
    observation.observation_type_concept_id,
    NULL::integer AS observation_operator_concept_id,
    observation.value_as_number,
    observation.value_as_string,
    observation.value_as_concept_id,
    observation.qualifier_concept_id,
    observation.unit_concept_id,
    NULL::numeric AS range_low,
    NULL::numeric AS range_high,
    observation.provider_id,
    observation.visit_occurrence_id,
    observation.visit_detail_id,
    observation.observation_source_value,
    observation.observation_source_concept_id,
    observation.unit_source_value,
    observation.qualifier_source_value,
    NULL::integer AS unit_source_concept_id,
    observation.value_source_value,
    observation.observation_event_id,
    observation.obs_event_field_concept_id
   FROM scd.observation;


ALTER TABLE scd.f_observation_view OWNER TO sascs;

--
-- Name: f_person; Type: TABLE; Schema: scd; Owner: sascs
--

CREATE TABLE scd.f_person (
    person_id integer NOT NULL,
    family_name character varying(255),
    given1_name character varying(255),
    given2_name character varying(255),
    prefix_name character varying(255),
    suffix_name character varying(255),
    preferred_language character varying(255),
    ssn character varying(12),
    active smallint,
    contact_point1 character varying(255),
    contact_point2 character varying(255),
    contact_point3 character varying(255),
    maritalstatus character varying(255)
);


ALTER TABLE scd.f_person OWNER TO sascs;

--
-- Name: f_resource_deduplicate; Type: TABLE; Schema: scd; Owner: sascs
--

CREATE TABLE scd.f_resource_deduplicate (
    id integer NOT NULL,
    domain_id character varying(20) NOT NULL,
    omop_id bigint NOT NULL,
    fhir_resource_type character varying NOT NULL,
    fhir_identifier_system character varying NOT NULL,
    fhir_identifier_value character varying NOT NULL
);


ALTER TABLE scd.f_resource_deduplicate OWNER TO sascs;

--
-- Name: fact_relationship; Type: TABLE; Schema: scd; Owner: sascs
--

CREATE TABLE scd.fact_relationship (
    domain_concept_id_1 integer NOT NULL,
    fact_id_1 integer NOT NULL,
    domain_concept_id_2 integer NOT NULL,
    fact_id_2 integer NOT NULL,
    relationship_concept_id integer NOT NULL
);


ALTER TABLE scd.fact_relationship OWNER TO sascs;

--
-- Name: flag_info; Type: TABLE; Schema: scd; Owner: sascs
--

CREATE TABLE scd.flag_info (
    flag_info_id bigint NOT NULL,
    case_info_id bigint NOT NULL,
    person_id integer NOT NULL,
    domain character varying,
    flag_type character varying NOT NULL,
    last_updated timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    annotation text,
    domain_data_id integer
);


ALTER TABLE scd.flag_info OWNER TO sascs;

--
-- Name: location; Type: TABLE; Schema: scd; Owner: sascs
--

CREATE TABLE scd.location (
    location_id integer NOT NULL,
    address_1 character varying(50),
    address_2 character varying(50),
    city character varying(50),
    state character varying(2),
    zip character varying(10),
    county character varying(20),
    location_source_value character varying(50),
    country_concept_id integer,
    country_source_value character varying(80),
    latitude numeric,
    longitude numeric
);


ALTER TABLE scd.location OWNER TO sascs;

--
-- Name: metadata; Type: TABLE; Schema: scd; Owner: sascs
--

CREATE TABLE scd.metadata (
    metadata_id integer NOT NULL,
    metadata_concept_id integer NOT NULL,
    metadata_type_concept_id integer NOT NULL,
    name character varying(250) NOT NULL,
    value_as_string character varying(250),
    value_as_concept_id integer,
    value_as_number numeric,
    metadata_date date,
    metadata_datetime timestamp without time zone
);


ALTER TABLE scd.metadata OWNER TO sascs;

--
-- Name: note; Type: TABLE; Schema: scd; Owner: sascs
--

CREATE TABLE scd.note (
    note_id integer NOT NULL,
    person_id integer NOT NULL,
    note_date date NOT NULL,
    note_datetime timestamp without time zone,
    note_type_concept_id integer NOT NULL,
    note_class_concept_id integer NOT NULL,
    note_title character varying(250),
    note_text text NOT NULL,
    encoding_concept_id integer NOT NULL,
    language_concept_id integer NOT NULL,
    provider_id integer,
    visit_occurrence_id integer,
    visit_detail_id integer,
    note_source_value character varying(50),
    note_event_id bigint,
    note_event_field_concept_id integer
);


ALTER TABLE scd.note OWNER TO sascs;

--
-- Name: note_nlp; Type: TABLE; Schema: scd; Owner: sascs
--

CREATE TABLE scd.note_nlp (
    note_nlp_id integer NOT NULL,
    note_id integer NOT NULL,
    section_concept_id integer,
    snippet character varying(250),
    "offset" character varying(50),
    lexical_variant character varying(250) NOT NULL,
    note_nlp_concept_id integer,
    note_nlp_source_concept_id integer,
    nlp_system character varying(250),
    nlp_date date NOT NULL,
    nlp_datetime timestamp without time zone,
    term_exists character varying(1),
    term_temporal character varying(50),
    term_modifiers character varying(2000)
);


ALTER TABLE scd.note_nlp OWNER TO sascs;

--
-- Name: observation_period; Type: TABLE; Schema: scd; Owner: sascs
--

CREATE TABLE scd.observation_period (
    observation_period_id integer NOT NULL,
    person_id integer NOT NULL,
    observation_period_start_date date NOT NULL,
    observation_period_end_date date NOT NULL,
    period_type_concept_id integer NOT NULL
);


ALTER TABLE scd.observation_period OWNER TO sascs;

--
-- Name: payer_plan_period; Type: TABLE; Schema: scd; Owner: sascs
--

CREATE TABLE scd.payer_plan_period (
    payer_plan_period_id integer NOT NULL,
    person_id integer NOT NULL,
    payer_plan_period_start_date date NOT NULL,
    payer_plan_period_end_date date NOT NULL,
    payer_concept_id integer,
    payer_source_value character varying(50),
    payer_source_concept_id integer,
    plan_concept_id integer,
    plan_source_value character varying(50),
    plan_source_concept_id integer,
    sponsor_concept_id integer,
    sponsor_source_value character varying(50),
    sponsor_source_concept_id integer,
    family_source_value character varying(50),
    stop_reason_concept_id integer,
    stop_reason_source_value character varying(50),
    stop_reason_source_concept_id integer
);


ALTER TABLE scd.payer_plan_period OWNER TO sascs;

--
-- Name: person; Type: TABLE; Schema: scd; Owner: sascs
--

CREATE TABLE scd.person (
    person_id integer NOT NULL,
    gender_concept_id integer NOT NULL,
    year_of_birth integer NOT NULL,
    month_of_birth integer,
    day_of_birth integer,
    birth_datetime timestamp without time zone,
    race_concept_id integer NOT NULL,
    ethnicity_concept_id integer NOT NULL,
    location_id integer,
    provider_id integer,
    care_site_id integer,
    person_source_value character varying(50),
    gender_source_value character varying(50),
    gender_source_concept_id integer,
    race_source_value character varying(50),
    race_source_concept_id integer,
    ethnicity_source_value character varying(50),
    ethnicity_source_concept_id integer
);


ALTER TABLE scd.person OWNER TO sascs;

--
-- Name: provider; Type: TABLE; Schema: scd; Owner: sascs
--

CREATE TABLE scd.provider (
    provider_id integer NOT NULL,
    provider_name character varying(255),
    npi character varying(20),
    dea character varying(20),
    specialty_concept_id integer,
    care_site_id integer,
    year_of_birth integer,
    gender_concept_id integer,
    provider_source_value character varying(50),
    specialty_source_value character varying(50),
    specialty_source_concept_id integer,
    gender_source_value character varying(50),
    gender_source_concept_id integer
);


ALTER TABLE scd.provider OWNER TO sascs;

--
-- Name: relationship; Type: TABLE; Schema: scd; Owner: sascs
--

CREATE TABLE scd.relationship (
    relationship_id character varying(20) NOT NULL,
    relationship_name character varying(255) NOT NULL,
    is_hierarchical character varying(1) NOT NULL,
    defines_ancestry character varying(1) NOT NULL,
    reverse_relationship_id character varying(20) NOT NULL,
    relationship_concept_id integer NOT NULL
);


ALTER TABLE scd.relationship OWNER TO sascs;

--
-- Name: source_to_concept_map; Type: TABLE; Schema: scd; Owner: sascs
--

CREATE TABLE scd.source_to_concept_map (
    source_code character varying(50) NOT NULL,
    source_concept_id integer NOT NULL,
    source_vocabulary_id character varying(20) NOT NULL,
    source_code_description character varying(255),
    target_concept_id integer NOT NULL,
    target_vocabulary_id character varying(20) NOT NULL,
    valid_start_date date NOT NULL,
    valid_end_date date NOT NULL,
    invalid_reason character varying(1)
);


ALTER TABLE scd.source_to_concept_map OWNER TO sascs;

--
-- Name: specimen; Type: TABLE; Schema: scd; Owner: sascs
--

CREATE TABLE scd.specimen (
    specimen_id integer NOT NULL,
    person_id integer NOT NULL,
    specimen_concept_id integer NOT NULL,
    specimen_type_concept_id integer NOT NULL,
    specimen_date date NOT NULL,
    specimen_datetime timestamp without time zone,
    quantity numeric,
    unit_concept_id integer,
    anatomic_site_concept_id integer,
    disease_status_concept_id integer,
    specimen_source_id character varying(50),
    specimen_source_value character varying(50),
    unit_source_value character varying(50),
    anatomic_site_source_value character varying(50),
    disease_status_source_value character varying(50)
);


ALTER TABLE scd.specimen OWNER TO sascs;

--
-- Name: visit_detail; Type: TABLE; Schema: scd; Owner: sascs
--

CREATE TABLE scd.visit_detail (
    visit_detail_id integer NOT NULL,
    person_id integer NOT NULL,
    visit_detail_concept_id integer NOT NULL,
    visit_detail_start_date date NOT NULL,
    visit_detail_start_datetime timestamp without time zone,
    visit_detail_end_date date NOT NULL,
    visit_detail_end_datetime timestamp without time zone,
    visit_detail_type_concept_id integer NOT NULL,
    provider_id integer,
    care_site_id integer,
    visit_detail_source_value character varying(50),
    visit_detail_source_concept_id integer,
    admitted_from_concept_id integer,
    admitted_from_source_value character varying(50),
    discharged_to_source_value character varying(50),
    discharged_to_concept_id integer,
    preceding_visit_detail_id integer,
    parent_visit_detail_id integer,
    visit_occurrence_id integer NOT NULL
);


ALTER TABLE scd.visit_detail OWNER TO sascs;

--
-- Name: visit_occurrence; Type: TABLE; Schema: scd; Owner: sascs
--

CREATE TABLE scd.visit_occurrence (
    visit_occurrence_id integer NOT NULL,
    person_id integer NOT NULL,
    visit_concept_id integer NOT NULL,
    visit_start_date date NOT NULL,
    visit_start_datetime timestamp without time zone,
    visit_end_date date NOT NULL,
    visit_end_datetime timestamp without time zone,
    visit_type_concept_id integer NOT NULL,
    provider_id integer,
    care_site_id integer,
    visit_source_value character varying(50),
    visit_source_concept_id integer,
    admitted_from_concept_id integer,
    admitted_from_source_value character varying(50),
    discharged_to_concept_id integer,
    discharged_to_source_value character varying(50),
    preceding_visit_occurrence_id integer
);


ALTER TABLE scd.visit_occurrence OWNER TO sascs;

--
-- Name: vocabulary; Type: TABLE; Schema: scd; Owner: sascs
--

CREATE TABLE scd.vocabulary (
    vocabulary_id character varying(20) NOT NULL,
    vocabulary_name character varying(255) NOT NULL,
    vocabulary_reference character varying(255),
    vocabulary_version character varying(255),
    vocabulary_concept_id integer NOT NULL
);


ALTER TABLE scd.vocabulary OWNER TO sascs;

--
-- Name: case_info case_info_pk; Type: CONSTRAINT; Schema: scd; Owner: sascs
--

ALTER TABLE ONLY scd.case_info
    ADD CONSTRAINT case_info_pk PRIMARY KEY (case_info_id);


--
-- Name: case_log case_logs_pk; Type: CONSTRAINT; Schema: scd; Owner: sascs
--

ALTER TABLE ONLY scd.case_log
    ADD CONSTRAINT case_logs_pk PRIMARY KEY (case_log_id);


--
-- Name: f_cache f_cache_pk; Type: CONSTRAINT; Schema: scd; Owner: sascs
--

ALTER TABLE ONLY scd.f_cache
    ADD CONSTRAINT f_cache_pk PRIMARY KEY (cache_id);


--
-- Name: f_person f_person_pk; Type: CONSTRAINT; Schema: scd; Owner: sascs
--

ALTER TABLE ONLY scd.f_person
    ADD CONSTRAINT f_person_pk PRIMARY KEY (person_id);


--
-- Name: f_resource_deduplicate f_resource_deduplicate_pk; Type: CONSTRAINT; Schema: scd; Owner: sascs
--

ALTER TABLE ONLY scd.f_resource_deduplicate
    ADD CONSTRAINT f_resource_deduplicate_pk PRIMARY KEY (id);


--
-- Name: flag_info flag_info_pk; Type: CONSTRAINT; Schema: scd; Owner: sascs
--

ALTER TABLE ONLY scd.flag_info
    ADD CONSTRAINT flag_info_pk PRIMARY KEY (flag_info_id);


--
-- Name: care_site xpk_care_site; Type: CONSTRAINT; Schema: scd; Owner: sascs
--

ALTER TABLE ONLY scd.care_site
    ADD CONSTRAINT xpk_care_site PRIMARY KEY (care_site_id);


--
-- Name: concept xpk_concept; Type: CONSTRAINT; Schema: scd; Owner: sascs
--

ALTER TABLE ONLY scd.concept
    ADD CONSTRAINT xpk_concept PRIMARY KEY (concept_id);


--
-- Name: concept_class xpk_concept_class; Type: CONSTRAINT; Schema: scd; Owner: sascs
--

ALTER TABLE ONLY scd.concept_class
    ADD CONSTRAINT xpk_concept_class PRIMARY KEY (concept_class_id);


--
-- Name: condition_era xpk_condition_era; Type: CONSTRAINT; Schema: scd; Owner: sascs
--

ALTER TABLE ONLY scd.condition_era
    ADD CONSTRAINT xpk_condition_era PRIMARY KEY (condition_era_id);


--
-- Name: condition_occurrence xpk_condition_occurrence; Type: CONSTRAINT; Schema: scd; Owner: sascs
--

ALTER TABLE ONLY scd.condition_occurrence
    ADD CONSTRAINT xpk_condition_occurrence PRIMARY KEY (condition_occurrence_id);


--
-- Name: cost xpk_cost; Type: CONSTRAINT; Schema: scd; Owner: sascs
--

ALTER TABLE ONLY scd.cost
    ADD CONSTRAINT xpk_cost PRIMARY KEY (cost_id);


--
-- Name: device_exposure xpk_device_exposure; Type: CONSTRAINT; Schema: scd; Owner: sascs
--

ALTER TABLE ONLY scd.device_exposure
    ADD CONSTRAINT xpk_device_exposure PRIMARY KEY (device_exposure_id);


--
-- Name: domain xpk_domain; Type: CONSTRAINT; Schema: scd; Owner: sascs
--

ALTER TABLE ONLY scd.domain
    ADD CONSTRAINT xpk_domain PRIMARY KEY (domain_id);


--
-- Name: dose_era xpk_dose_era; Type: CONSTRAINT; Schema: scd; Owner: sascs
--

ALTER TABLE ONLY scd.dose_era
    ADD CONSTRAINT xpk_dose_era PRIMARY KEY (dose_era_id);


--
-- Name: drug_era xpk_drug_era; Type: CONSTRAINT; Schema: scd; Owner: sascs
--

ALTER TABLE ONLY scd.drug_era
    ADD CONSTRAINT xpk_drug_era PRIMARY KEY (drug_era_id);


--
-- Name: drug_exposure xpk_drug_exposure; Type: CONSTRAINT; Schema: scd; Owner: sascs
--

ALTER TABLE ONLY scd.drug_exposure
    ADD CONSTRAINT xpk_drug_exposure PRIMARY KEY (drug_exposure_id);


--
-- Name: episode xpk_episode; Type: CONSTRAINT; Schema: scd; Owner: sascs
--

ALTER TABLE ONLY scd.episode
    ADD CONSTRAINT xpk_episode PRIMARY KEY (episode_id);


--
-- Name: location xpk_location; Type: CONSTRAINT; Schema: scd; Owner: sascs
--

ALTER TABLE ONLY scd.location
    ADD CONSTRAINT xpk_location PRIMARY KEY (location_id);


--
-- Name: measurement xpk_measurement; Type: CONSTRAINT; Schema: scd; Owner: sascs
--

ALTER TABLE ONLY scd.measurement
    ADD CONSTRAINT xpk_measurement PRIMARY KEY (measurement_id);


--
-- Name: metadata xpk_metadata; Type: CONSTRAINT; Schema: scd; Owner: sascs
--

ALTER TABLE ONLY scd.metadata
    ADD CONSTRAINT xpk_metadata PRIMARY KEY (metadata_id);


--
-- Name: note xpk_note; Type: CONSTRAINT; Schema: scd; Owner: sascs
--

ALTER TABLE ONLY scd.note
    ADD CONSTRAINT xpk_note PRIMARY KEY (note_id);


--
-- Name: note_nlp xpk_note_nlp; Type: CONSTRAINT; Schema: scd; Owner: sascs
--

ALTER TABLE ONLY scd.note_nlp
    ADD CONSTRAINT xpk_note_nlp PRIMARY KEY (note_nlp_id);


--
-- Name: observation xpk_observation; Type: CONSTRAINT; Schema: scd; Owner: sascs
--

ALTER TABLE ONLY scd.observation
    ADD CONSTRAINT xpk_observation PRIMARY KEY (observation_id);


--
-- Name: observation_period xpk_observation_period; Type: CONSTRAINT; Schema: scd; Owner: sascs
--

ALTER TABLE ONLY scd.observation_period
    ADD CONSTRAINT xpk_observation_period PRIMARY KEY (observation_period_id);


--
-- Name: payer_plan_period xpk_payer_plan_period; Type: CONSTRAINT; Schema: scd; Owner: sascs
--

ALTER TABLE ONLY scd.payer_plan_period
    ADD CONSTRAINT xpk_payer_plan_period PRIMARY KEY (payer_plan_period_id);


--
-- Name: person xpk_person; Type: CONSTRAINT; Schema: scd; Owner: sascs
--

ALTER TABLE ONLY scd.person
    ADD CONSTRAINT xpk_person PRIMARY KEY (person_id);


--
-- Name: procedure_occurrence xpk_procedure_occurrence; Type: CONSTRAINT; Schema: scd; Owner: sascs
--

ALTER TABLE ONLY scd.procedure_occurrence
    ADD CONSTRAINT xpk_procedure_occurrence PRIMARY KEY (procedure_occurrence_id);


--
-- Name: provider xpk_provider; Type: CONSTRAINT; Schema: scd; Owner: sascs
--

ALTER TABLE ONLY scd.provider
    ADD CONSTRAINT xpk_provider PRIMARY KEY (provider_id);


--
-- Name: relationship xpk_relationship; Type: CONSTRAINT; Schema: scd; Owner: sascs
--

ALTER TABLE ONLY scd.relationship
    ADD CONSTRAINT xpk_relationship PRIMARY KEY (relationship_id);


--
-- Name: specimen xpk_specimen; Type: CONSTRAINT; Schema: scd; Owner: sascs
--

ALTER TABLE ONLY scd.specimen
    ADD CONSTRAINT xpk_specimen PRIMARY KEY (specimen_id);


--
-- Name: visit_detail xpk_visit_detail; Type: CONSTRAINT; Schema: scd; Owner: sascs
--

ALTER TABLE ONLY scd.visit_detail
    ADD CONSTRAINT xpk_visit_detail PRIMARY KEY (visit_detail_id);


--
-- Name: visit_occurrence xpk_visit_occurrence; Type: CONSTRAINT; Schema: scd; Owner: sascs
--

ALTER TABLE ONLY scd.visit_occurrence
    ADD CONSTRAINT xpk_visit_occurrence PRIMARY KEY (visit_occurrence_id);


--
-- Name: vocabulary xpk_vocabulary; Type: CONSTRAINT; Schema: scd; Owner: sascs
--

ALTER TABLE ONLY scd.vocabulary
    ADD CONSTRAINT xpk_vocabulary PRIMARY KEY (vocabulary_id);


--
-- Name: case_case_info_id_uindex; Type: INDEX; Schema: scd; Owner: sascs
--

CREATE UNIQUE INDEX case_case_info_id_uindex ON scd.case_info USING btree (case_info_id);


--
-- Name: case_person_id_job_id_status_trigger_at_index; Type: INDEX; Schema: scd; Owner: sascs
--

CREATE INDEX case_person_id_job_id_status_trigger_at_index ON scd.case_info USING btree (person_id, job_id, status, trigger_at_datetime);


--
-- Name: f_resource_deduplicate_id_uindex; Type: INDEX; Schema: scd; Owner: sascs
--

CREATE UNIQUE INDEX f_resource_deduplicate_id_uindex ON scd.f_resource_deduplicate USING btree (id);


--
-- Name: idx_care_site_id_1; Type: INDEX; Schema: scd; Owner: sascs
--

CREATE INDEX idx_care_site_id_1 ON scd.care_site USING btree (care_site_id);

ALTER TABLE scd.care_site CLUSTER ON idx_care_site_id_1;


--
-- Name: idx_concept_ancestor_id_1; Type: INDEX; Schema: scd; Owner: sascs
--

CREATE INDEX idx_concept_ancestor_id_1 ON scd.concept_ancestor USING btree (ancestor_concept_id);

ALTER TABLE scd.concept_ancestor CLUSTER ON idx_concept_ancestor_id_1;


--
-- Name: idx_concept_ancestor_id_2; Type: INDEX; Schema: scd; Owner: sascs
--

CREATE INDEX idx_concept_ancestor_id_2 ON scd.concept_ancestor USING btree (descendant_concept_id);


--
-- Name: idx_concept_class_class_id; Type: INDEX; Schema: scd; Owner: sascs
--

CREATE INDEX idx_concept_class_class_id ON scd.concept_class USING btree (concept_class_id);

ALTER TABLE scd.concept_class CLUSTER ON idx_concept_class_class_id;


--
-- Name: idx_concept_class_id; Type: INDEX; Schema: scd; Owner: sascs
--

CREATE INDEX idx_concept_class_id ON scd.concept USING btree (concept_class_id);


--
-- Name: idx_concept_code; Type: INDEX; Schema: scd; Owner: sascs
--

CREATE INDEX idx_concept_code ON scd.concept USING btree (concept_code);


--
-- Name: idx_concept_concept_id; Type: INDEX; Schema: scd; Owner: sascs
--

CREATE INDEX idx_concept_concept_id ON scd.concept USING btree (concept_id);

ALTER TABLE scd.concept CLUSTER ON idx_concept_concept_id;


--
-- Name: idx_concept_domain_id; Type: INDEX; Schema: scd; Owner: sascs
--

CREATE INDEX idx_concept_domain_id ON scd.concept USING btree (domain_id);


--
-- Name: idx_concept_relationship_id_1; Type: INDEX; Schema: scd; Owner: sascs
--

CREATE INDEX idx_concept_relationship_id_1 ON scd.concept_relationship USING btree (concept_id_1);

ALTER TABLE scd.concept_relationship CLUSTER ON idx_concept_relationship_id_1;


--
-- Name: idx_concept_relationship_id_2; Type: INDEX; Schema: scd; Owner: sascs
--

CREATE INDEX idx_concept_relationship_id_2 ON scd.concept_relationship USING btree (concept_id_2);


--
-- Name: idx_concept_relationship_id_3; Type: INDEX; Schema: scd; Owner: sascs
--

CREATE INDEX idx_concept_relationship_id_3 ON scd.concept_relationship USING btree (relationship_id);


--
-- Name: idx_concept_synonym_id; Type: INDEX; Schema: scd; Owner: sascs
--

CREATE INDEX idx_concept_synonym_id ON scd.concept_synonym USING btree (concept_id);

ALTER TABLE scd.concept_synonym CLUSTER ON idx_concept_synonym_id;


--
-- Name: idx_concept_vocabluary_id; Type: INDEX; Schema: scd; Owner: sascs
--

CREATE INDEX idx_concept_vocabluary_id ON scd.concept USING btree (vocabulary_id);


--
-- Name: idx_condition_concept_id_1; Type: INDEX; Schema: scd; Owner: sascs
--

CREATE INDEX idx_condition_concept_id_1 ON scd.condition_occurrence USING btree (condition_concept_id);


--
-- Name: idx_condition_era_concept_id_1; Type: INDEX; Schema: scd; Owner: sascs
--

CREATE INDEX idx_condition_era_concept_id_1 ON scd.condition_era USING btree (condition_concept_id);


--
-- Name: idx_condition_era_person_id_1; Type: INDEX; Schema: scd; Owner: sascs
--

CREATE INDEX idx_condition_era_person_id_1 ON scd.condition_era USING btree (person_id);

ALTER TABLE scd.condition_era CLUSTER ON idx_condition_era_person_id_1;


--
-- Name: idx_condition_person_id_1; Type: INDEX; Schema: scd; Owner: sascs
--

CREATE INDEX idx_condition_person_id_1 ON scd.condition_occurrence USING btree (person_id);

ALTER TABLE scd.condition_occurrence CLUSTER ON idx_condition_person_id_1;


--
-- Name: idx_condition_visit_id_1; Type: INDEX; Schema: scd; Owner: sascs
--

CREATE INDEX idx_condition_visit_id_1 ON scd.condition_occurrence USING btree (visit_occurrence_id);


--
-- Name: idx_cost_event_id; Type: INDEX; Schema: scd; Owner: sascs
--

CREATE INDEX idx_cost_event_id ON scd.cost USING btree (cost_event_id);


--
-- Name: idx_death_person_id_1; Type: INDEX; Schema: scd; Owner: sascs
--

CREATE INDEX idx_death_person_id_1 ON scd.death USING btree (person_id);

ALTER TABLE scd.death CLUSTER ON idx_death_person_id_1;


--
-- Name: idx_device_concept_id_1; Type: INDEX; Schema: scd; Owner: sascs
--

CREATE INDEX idx_device_concept_id_1 ON scd.device_exposure USING btree (device_concept_id);


--
-- Name: idx_device_person_id_1; Type: INDEX; Schema: scd; Owner: sascs
--

CREATE INDEX idx_device_person_id_1 ON scd.device_exposure USING btree (person_id);

ALTER TABLE scd.device_exposure CLUSTER ON idx_device_person_id_1;


--
-- Name: idx_device_visit_id_1; Type: INDEX; Schema: scd; Owner: sascs
--

CREATE INDEX idx_device_visit_id_1 ON scd.device_exposure USING btree (visit_occurrence_id);


--
-- Name: idx_domain_domain_id; Type: INDEX; Schema: scd; Owner: sascs
--

CREATE INDEX idx_domain_domain_id ON scd.domain USING btree (domain_id);

ALTER TABLE scd.domain CLUSTER ON idx_domain_domain_id;


--
-- Name: idx_dose_era_concept_id_1; Type: INDEX; Schema: scd; Owner: sascs
--

CREATE INDEX idx_dose_era_concept_id_1 ON scd.dose_era USING btree (drug_concept_id);


--
-- Name: idx_dose_era_person_id_1; Type: INDEX; Schema: scd; Owner: sascs
--

CREATE INDEX idx_dose_era_person_id_1 ON scd.dose_era USING btree (person_id);

ALTER TABLE scd.dose_era CLUSTER ON idx_dose_era_person_id_1;


--
-- Name: idx_drug_concept_id_1; Type: INDEX; Schema: scd; Owner: sascs
--

CREATE INDEX idx_drug_concept_id_1 ON scd.drug_exposure USING btree (drug_concept_id);


--
-- Name: idx_drug_era_concept_id_1; Type: INDEX; Schema: scd; Owner: sascs
--

CREATE INDEX idx_drug_era_concept_id_1 ON scd.drug_era USING btree (drug_concept_id);


--
-- Name: idx_drug_era_person_id_1; Type: INDEX; Schema: scd; Owner: sascs
--

CREATE INDEX idx_drug_era_person_id_1 ON scd.drug_era USING btree (person_id);

ALTER TABLE scd.drug_era CLUSTER ON idx_drug_era_person_id_1;


--
-- Name: idx_drug_person_id_1; Type: INDEX; Schema: scd; Owner: sascs
--

CREATE INDEX idx_drug_person_id_1 ON scd.drug_exposure USING btree (person_id);

ALTER TABLE scd.drug_exposure CLUSTER ON idx_drug_person_id_1;


--
-- Name: idx_drug_strength_id_1; Type: INDEX; Schema: scd; Owner: sascs
--

CREATE INDEX idx_drug_strength_id_1 ON scd.drug_strength USING btree (drug_concept_id);

ALTER TABLE scd.drug_strength CLUSTER ON idx_drug_strength_id_1;


--
-- Name: idx_drug_strength_id_2; Type: INDEX; Schema: scd; Owner: sascs
--

CREATE INDEX idx_drug_strength_id_2 ON scd.drug_strength USING btree (ingredient_concept_id);


--
-- Name: idx_drug_visit_id_1; Type: INDEX; Schema: scd; Owner: sascs
--

CREATE INDEX idx_drug_visit_id_1 ON scd.drug_exposure USING btree (visit_occurrence_id);


--
-- Name: idx_fact_relationship_id1; Type: INDEX; Schema: scd; Owner: sascs
--

CREATE INDEX idx_fact_relationship_id1 ON scd.fact_relationship USING btree (domain_concept_id_1);


--
-- Name: idx_fact_relationship_id2; Type: INDEX; Schema: scd; Owner: sascs
--

CREATE INDEX idx_fact_relationship_id2 ON scd.fact_relationship USING btree (domain_concept_id_2);


--
-- Name: idx_fact_relationship_id3; Type: INDEX; Schema: scd; Owner: sascs
--

CREATE INDEX idx_fact_relationship_id3 ON scd.fact_relationship USING btree (relationship_concept_id);


--
-- Name: idx_gender; Type: INDEX; Schema: scd; Owner: sascs
--

CREATE INDEX idx_gender ON scd.person USING btree (gender_concept_id);


--
-- Name: idx_location_id_1; Type: INDEX; Schema: scd; Owner: sascs
--

CREATE INDEX idx_location_id_1 ON scd.location USING btree (location_id);

ALTER TABLE scd.location CLUSTER ON idx_location_id_1;


--
-- Name: idx_measurement_concept_id_1; Type: INDEX; Schema: scd; Owner: sascs
--

CREATE INDEX idx_measurement_concept_id_1 ON scd.measurement USING btree (measurement_concept_id);


--
-- Name: idx_measurement_person_id_1; Type: INDEX; Schema: scd; Owner: sascs
--

CREATE INDEX idx_measurement_person_id_1 ON scd.measurement USING btree (person_id);

ALTER TABLE scd.measurement CLUSTER ON idx_measurement_person_id_1;


--
-- Name: idx_measurement_visit_id_1; Type: INDEX; Schema: scd; Owner: sascs
--

CREATE INDEX idx_measurement_visit_id_1 ON scd.measurement USING btree (visit_occurrence_id);


--
-- Name: idx_metadata_concept_id_1; Type: INDEX; Schema: scd; Owner: sascs
--

CREATE INDEX idx_metadata_concept_id_1 ON scd.metadata USING btree (metadata_concept_id);

ALTER TABLE scd.metadata CLUSTER ON idx_metadata_concept_id_1;


--
-- Name: idx_note_concept_id_1; Type: INDEX; Schema: scd; Owner: sascs
--

CREATE INDEX idx_note_concept_id_1 ON scd.note USING btree (note_type_concept_id);


--
-- Name: idx_note_nlp_concept_id_1; Type: INDEX; Schema: scd; Owner: sascs
--

CREATE INDEX idx_note_nlp_concept_id_1 ON scd.note_nlp USING btree (note_nlp_concept_id);


--
-- Name: idx_note_nlp_note_id_1; Type: INDEX; Schema: scd; Owner: sascs
--

CREATE INDEX idx_note_nlp_note_id_1 ON scd.note_nlp USING btree (note_id);

ALTER TABLE scd.note_nlp CLUSTER ON idx_note_nlp_note_id_1;


--
-- Name: idx_note_person_id_1; Type: INDEX; Schema: scd; Owner: sascs
--

CREATE INDEX idx_note_person_id_1 ON scd.note USING btree (person_id);

ALTER TABLE scd.note CLUSTER ON idx_note_person_id_1;


--
-- Name: idx_note_visit_id_1; Type: INDEX; Schema: scd; Owner: sascs
--

CREATE INDEX idx_note_visit_id_1 ON scd.note USING btree (visit_occurrence_id);


--
-- Name: idx_observation_concept_id_1; Type: INDEX; Schema: scd; Owner: sascs
--

CREATE INDEX idx_observation_concept_id_1 ON scd.observation USING btree (observation_concept_id);


--
-- Name: idx_observation_period_id_1; Type: INDEX; Schema: scd; Owner: sascs
--

CREATE INDEX idx_observation_period_id_1 ON scd.observation_period USING btree (person_id);

ALTER TABLE scd.observation_period CLUSTER ON idx_observation_period_id_1;


--
-- Name: idx_observation_person_id_1; Type: INDEX; Schema: scd; Owner: sascs
--

CREATE INDEX idx_observation_person_id_1 ON scd.observation USING btree (person_id);

ALTER TABLE scd.observation CLUSTER ON idx_observation_person_id_1;


--
-- Name: idx_observation_visit_id_1; Type: INDEX; Schema: scd; Owner: sascs
--

CREATE INDEX idx_observation_visit_id_1 ON scd.observation USING btree (visit_occurrence_id);


--
-- Name: idx_period_person_id_1; Type: INDEX; Schema: scd; Owner: sascs
--

CREATE INDEX idx_period_person_id_1 ON scd.payer_plan_period USING btree (person_id);

ALTER TABLE scd.payer_plan_period CLUSTER ON idx_period_person_id_1;


--
-- Name: idx_person_id; Type: INDEX; Schema: scd; Owner: sascs
--

CREATE INDEX idx_person_id ON scd.person USING btree (person_id);

ALTER TABLE scd.person CLUSTER ON idx_person_id;


--
-- Name: idx_procedure_concept_id_1; Type: INDEX; Schema: scd; Owner: sascs
--

CREATE INDEX idx_procedure_concept_id_1 ON scd.procedure_occurrence USING btree (procedure_concept_id);


--
-- Name: idx_procedure_person_id_1; Type: INDEX; Schema: scd; Owner: sascs
--

CREATE INDEX idx_procedure_person_id_1 ON scd.procedure_occurrence USING btree (person_id);

ALTER TABLE scd.procedure_occurrence CLUSTER ON idx_procedure_person_id_1;


--
-- Name: idx_procedure_visit_id_1; Type: INDEX; Schema: scd; Owner: sascs
--

CREATE INDEX idx_procedure_visit_id_1 ON scd.procedure_occurrence USING btree (visit_occurrence_id);


--
-- Name: idx_provider_id_1; Type: INDEX; Schema: scd; Owner: sascs
--

CREATE INDEX idx_provider_id_1 ON scd.provider USING btree (provider_id);

ALTER TABLE scd.provider CLUSTER ON idx_provider_id_1;


--
-- Name: idx_relationship_rel_id; Type: INDEX; Schema: scd; Owner: sascs
--

CREATE INDEX idx_relationship_rel_id ON scd.relationship USING btree (relationship_id);

ALTER TABLE scd.relationship CLUSTER ON idx_relationship_rel_id;


--
-- Name: idx_source_to_concept_map_1; Type: INDEX; Schema: scd; Owner: sascs
--

CREATE INDEX idx_source_to_concept_map_1 ON scd.source_to_concept_map USING btree (source_vocabulary_id);


--
-- Name: idx_source_to_concept_map_2; Type: INDEX; Schema: scd; Owner: sascs
--

CREATE INDEX idx_source_to_concept_map_2 ON scd.source_to_concept_map USING btree (target_vocabulary_id);


--
-- Name: idx_source_to_concept_map_3; Type: INDEX; Schema: scd; Owner: sascs
--

CREATE INDEX idx_source_to_concept_map_3 ON scd.source_to_concept_map USING btree (target_concept_id);

ALTER TABLE scd.source_to_concept_map CLUSTER ON idx_source_to_concept_map_3;


--
-- Name: idx_source_to_concept_map_c; Type: INDEX; Schema: scd; Owner: sascs
--

CREATE INDEX idx_source_to_concept_map_c ON scd.source_to_concept_map USING btree (source_code);


--
-- Name: idx_specimen_concept_id_1; Type: INDEX; Schema: scd; Owner: sascs
--

CREATE INDEX idx_specimen_concept_id_1 ON scd.specimen USING btree (specimen_concept_id);


--
-- Name: idx_specimen_person_id_1; Type: INDEX; Schema: scd; Owner: sascs
--

CREATE INDEX idx_specimen_person_id_1 ON scd.specimen USING btree (person_id);

ALTER TABLE scd.specimen CLUSTER ON idx_specimen_person_id_1;


--
-- Name: idx_visit_concept_id_1; Type: INDEX; Schema: scd; Owner: sascs
--

CREATE INDEX idx_visit_concept_id_1 ON scd.visit_occurrence USING btree (visit_concept_id);


--
-- Name: idx_visit_det_concept_id_1; Type: INDEX; Schema: scd; Owner: sascs
--

CREATE INDEX idx_visit_det_concept_id_1 ON scd.visit_detail USING btree (visit_detail_concept_id);


--
-- Name: idx_visit_det_occ_id; Type: INDEX; Schema: scd; Owner: sascs
--

CREATE INDEX idx_visit_det_occ_id ON scd.visit_detail USING btree (visit_occurrence_id);


--
-- Name: idx_visit_det_person_id_1; Type: INDEX; Schema: scd; Owner: sascs
--

CREATE INDEX idx_visit_det_person_id_1 ON scd.visit_detail USING btree (person_id);

ALTER TABLE scd.visit_detail CLUSTER ON idx_visit_det_person_id_1;


--
-- Name: idx_visit_person_id_1; Type: INDEX; Schema: scd; Owner: sascs
--

CREATE INDEX idx_visit_person_id_1 ON scd.visit_occurrence USING btree (person_id);

ALTER TABLE scd.visit_occurrence CLUSTER ON idx_visit_person_id_1;


--
-- Name: idx_vocabulary_vocabulary_id; Type: INDEX; Schema: scd; Owner: sascs
--

CREATE INDEX idx_vocabulary_vocabulary_id ON scd.vocabulary USING btree (vocabulary_id);

ALTER TABLE scd.vocabulary CLUSTER ON idx_vocabulary_vocabulary_id;


--
-- PostgreSQL database dump complete
--

\unrestrict u9ny21fuboi1BufdeH72acIK6tYReP9O8Dvk0ihu8ezXsW8eOz5UcLWiS01XNGu

