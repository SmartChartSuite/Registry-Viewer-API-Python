--
-- PostgreSQL database dump
--

\restrict iou0Dc8yRb8XF3r08p9Z4VDKWXpAyEnOpithDDSHty52LCWCYT0GrpYY29JHco1

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
-- Name: concept; Type: TABLE; Schema: vocab; Owner: sascs
--

CREATE TABLE vocab.concept (
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


ALTER TABLE vocab.concept OWNER TO sascs;

--
-- Name: concept_ancestor; Type: TABLE; Schema: vocab; Owner: sascs
--

CREATE TABLE vocab.concept_ancestor (
    ancestor_concept_id integer NOT NULL,
    descendant_concept_id integer NOT NULL,
    min_levels_of_separation integer NOT NULL,
    max_levels_of_separation integer NOT NULL
);


ALTER TABLE vocab.concept_ancestor OWNER TO sascs;

--
-- Name: concept_class; Type: TABLE; Schema: vocab; Owner: sascs
--

CREATE TABLE vocab.concept_class (
    concept_class_id character varying(20) NOT NULL,
    concept_class_name character varying(255) NOT NULL,
    concept_class_concept_id integer NOT NULL
);


ALTER TABLE vocab.concept_class OWNER TO sascs;

--
-- Name: concept_recommended; Type: TABLE; Schema: vocab; Owner: sascs
--

CREATE TABLE vocab.concept_recommended (
    concept_id_1 bigint,
    concept_id_2 bigint,
    relationship_id character varying(20)
);


ALTER TABLE vocab.concept_recommended OWNER TO sascs;

--
-- Name: concept_relationship; Type: TABLE; Schema: vocab; Owner: sascs
--

CREATE TABLE vocab.concept_relationship (
    concept_id_1 integer NOT NULL,
    concept_id_2 integer NOT NULL,
    relationship_id character varying(20) NOT NULL,
    valid_start_date date NOT NULL,
    valid_end_date date NOT NULL,
    invalid_reason character varying(1)
);


ALTER TABLE vocab.concept_relationship OWNER TO sascs;

--
-- Name: concept_synonym; Type: TABLE; Schema: vocab; Owner: sascs
--

CREATE TABLE vocab.concept_synonym (
    concept_id integer NOT NULL,
    concept_synonym_name character varying(1000) NOT NULL,
    language_concept_id integer NOT NULL
);


ALTER TABLE vocab.concept_synonym OWNER TO sascs;

--
-- Name: domain; Type: TABLE; Schema: vocab; Owner: sascs
--

CREATE TABLE vocab.domain (
    domain_id character varying(20) NOT NULL,
    domain_name character varying(255) NOT NULL,
    domain_concept_id integer NOT NULL
);


ALTER TABLE vocab.domain OWNER TO sascs;

--
-- Name: drug_strength; Type: TABLE; Schema: vocab; Owner: sascs
--

CREATE TABLE vocab.drug_strength (
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


ALTER TABLE vocab.drug_strength OWNER TO sascs;

--
-- Name: relationship; Type: TABLE; Schema: vocab; Owner: sascs
--

CREATE TABLE vocab.relationship (
    relationship_id character varying(20) NOT NULL,
    relationship_name character varying(255) NOT NULL,
    is_hierarchical character varying(1) NOT NULL,
    defines_ancestry character varying(1) NOT NULL,
    reverse_relationship_id character varying(20) NOT NULL,
    relationship_concept_id integer NOT NULL
);


ALTER TABLE vocab.relationship OWNER TO sascs;

--
-- Name: source_to_concept_map; Type: TABLE; Schema: vocab; Owner: sascs
--

CREATE TABLE vocab.source_to_concept_map (
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


ALTER TABLE vocab.source_to_concept_map OWNER TO sascs;

--
-- Name: vocabulary; Type: TABLE; Schema: vocab; Owner: sascs
--

CREATE TABLE vocab.vocabulary (
    vocabulary_id character varying(20) NOT NULL,
    vocabulary_name character varying(255) NOT NULL,
    vocabulary_reference character varying(255),
    vocabulary_version character varying(255),
    vocabulary_concept_id integer NOT NULL
);


ALTER TABLE vocab.vocabulary OWNER TO sascs;

--
-- Name: concept xpk_concept; Type: CONSTRAINT; Schema: vocab; Owner: sascs
--

ALTER TABLE ONLY vocab.concept
    ADD CONSTRAINT xpk_concept PRIMARY KEY (concept_id);


--
-- Name: concept_class xpk_concept_class; Type: CONSTRAINT; Schema: vocab; Owner: sascs
--

ALTER TABLE ONLY vocab.concept_class
    ADD CONSTRAINT xpk_concept_class PRIMARY KEY (concept_class_id);


--
-- Name: domain xpk_domain; Type: CONSTRAINT; Schema: vocab; Owner: sascs
--

ALTER TABLE ONLY vocab.domain
    ADD CONSTRAINT xpk_domain PRIMARY KEY (domain_id);


--
-- Name: relationship xpk_relationship; Type: CONSTRAINT; Schema: vocab; Owner: sascs
--

ALTER TABLE ONLY vocab.relationship
    ADD CONSTRAINT xpk_relationship PRIMARY KEY (relationship_id);


--
-- Name: vocabulary xpk_vocabulary; Type: CONSTRAINT; Schema: vocab; Owner: sascs
--

ALTER TABLE ONLY vocab.vocabulary
    ADD CONSTRAINT xpk_vocabulary PRIMARY KEY (vocabulary_id);


--
-- Name: idx_concept_ancestor_id_1; Type: INDEX; Schema: vocab; Owner: sascs
--

CREATE INDEX idx_concept_ancestor_id_1 ON vocab.concept_ancestor USING btree (ancestor_concept_id);

ALTER TABLE vocab.concept_ancestor CLUSTER ON idx_concept_ancestor_id_1;


--
-- Name: idx_concept_ancestor_id_2; Type: INDEX; Schema: vocab; Owner: sascs
--

CREATE INDEX idx_concept_ancestor_id_2 ON vocab.concept_ancestor USING btree (descendant_concept_id);


--
-- Name: idx_concept_class_class_id; Type: INDEX; Schema: vocab; Owner: sascs
--

CREATE INDEX idx_concept_class_class_id ON vocab.concept_class USING btree (concept_class_id);

ALTER TABLE vocab.concept_class CLUSTER ON idx_concept_class_class_id;


--
-- Name: idx_concept_class_id; Type: INDEX; Schema: vocab; Owner: sascs
--

CREATE INDEX idx_concept_class_id ON vocab.concept USING btree (concept_class_id);


--
-- Name: idx_concept_code; Type: INDEX; Schema: vocab; Owner: sascs
--

CREATE INDEX idx_concept_code ON vocab.concept USING btree (concept_code);


--
-- Name: idx_concept_concept_id; Type: INDEX; Schema: vocab; Owner: sascs
--

CREATE INDEX idx_concept_concept_id ON vocab.concept USING btree (concept_id);

ALTER TABLE vocab.concept CLUSTER ON idx_concept_concept_id;


--
-- Name: idx_concept_domain_id; Type: INDEX; Schema: vocab; Owner: sascs
--

CREATE INDEX idx_concept_domain_id ON vocab.concept USING btree (domain_id);


--
-- Name: idx_concept_relationship_id_1; Type: INDEX; Schema: vocab; Owner: sascs
--

CREATE INDEX idx_concept_relationship_id_1 ON vocab.concept_relationship USING btree (concept_id_1);

ALTER TABLE vocab.concept_relationship CLUSTER ON idx_concept_relationship_id_1;


--
-- Name: idx_concept_relationship_id_2; Type: INDEX; Schema: vocab; Owner: sascs
--

CREATE INDEX idx_concept_relationship_id_2 ON vocab.concept_relationship USING btree (concept_id_2);


--
-- Name: idx_concept_relationship_id_3; Type: INDEX; Schema: vocab; Owner: sascs
--

CREATE INDEX idx_concept_relationship_id_3 ON vocab.concept_relationship USING btree (relationship_id);


--
-- Name: idx_concept_synonym_id; Type: INDEX; Schema: vocab; Owner: sascs
--

CREATE INDEX idx_concept_synonym_id ON vocab.concept_synonym USING btree (concept_id);

ALTER TABLE vocab.concept_synonym CLUSTER ON idx_concept_synonym_id;


--
-- Name: idx_concept_vocabluary_id; Type: INDEX; Schema: vocab; Owner: sascs
--

CREATE INDEX idx_concept_vocabluary_id ON vocab.concept USING btree (vocabulary_id);


--
-- Name: idx_domain_domain_id; Type: INDEX; Schema: vocab; Owner: sascs
--

CREATE INDEX idx_domain_domain_id ON vocab.domain USING btree (domain_id);

ALTER TABLE vocab.domain CLUSTER ON idx_domain_domain_id;


--
-- Name: idx_drug_strength_id_1; Type: INDEX; Schema: vocab; Owner: sascs
--

CREATE INDEX idx_drug_strength_id_1 ON vocab.drug_strength USING btree (drug_concept_id);

ALTER TABLE vocab.drug_strength CLUSTER ON idx_drug_strength_id_1;


--
-- Name: idx_drug_strength_id_2; Type: INDEX; Schema: vocab; Owner: sascs
--

CREATE INDEX idx_drug_strength_id_2 ON vocab.drug_strength USING btree (ingredient_concept_id);


--
-- Name: idx_relationship_rel_id; Type: INDEX; Schema: vocab; Owner: sascs
--

CREATE INDEX idx_relationship_rel_id ON vocab.relationship USING btree (relationship_id);

ALTER TABLE vocab.relationship CLUSTER ON idx_relationship_rel_id;


--
-- Name: idx_source_to_concept_map_1; Type: INDEX; Schema: vocab; Owner: sascs
--

CREATE INDEX idx_source_to_concept_map_1 ON vocab.source_to_concept_map USING btree (source_vocabulary_id);


--
-- Name: idx_source_to_concept_map_2; Type: INDEX; Schema: vocab; Owner: sascs
--

CREATE INDEX idx_source_to_concept_map_2 ON vocab.source_to_concept_map USING btree (target_vocabulary_id);


--
-- Name: idx_source_to_concept_map_3; Type: INDEX; Schema: vocab; Owner: sascs
--

CREATE INDEX idx_source_to_concept_map_3 ON vocab.source_to_concept_map USING btree (target_concept_id);

ALTER TABLE vocab.source_to_concept_map CLUSTER ON idx_source_to_concept_map_3;


--
-- Name: idx_source_to_concept_map_c; Type: INDEX; Schema: vocab; Owner: sascs
--

CREATE INDEX idx_source_to_concept_map_c ON vocab.source_to_concept_map USING btree (source_code);


--
-- Name: idx_vocabulary_vocabulary_id; Type: INDEX; Schema: vocab; Owner: sascs
--

CREATE INDEX idx_vocabulary_vocabulary_id ON vocab.vocabulary USING btree (vocabulary_id);

ALTER TABLE vocab.vocabulary CLUSTER ON idx_vocabulary_vocabulary_id;


--
-- PostgreSQL database dump complete
--

\unrestrict iou0Dc8yRb8XF3r08p9Z4VDKWXpAyEnOpithDDSHty52LCWCYT0GrpYY29JHco1

