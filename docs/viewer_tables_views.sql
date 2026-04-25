--
-- PostgreSQL database dump
--

\restrict lEkn5aFhOUPIWaBUwjr3I1w54Ml3hMPsjvaKByOdXewX9SAeruT0ru5xNraohBb

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
-- Name: annotation; Type: TABLE; Schema: viewer; Owner: sascs
--

CREATE TABLE viewer.annotation (
    annotation_id integer NOT NULL,
    content_id integer NOT NULL,
    case_id integer NOT NULL,
    user_id integer,
    text text,
    created timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


ALTER TABLE viewer.annotation OWNER TO sascs;

--
-- Name: annotation_annotation_id_seq; Type: SEQUENCE; Schema: viewer; Owner: sascs
--

CREATE SEQUENCE viewer.annotation_annotation_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE viewer.annotation_annotation_id_seq OWNER TO sascs;

--
-- Name: annotation_annotation_id_seq; Type: SEQUENCE OWNED BY; Schema: viewer; Owner: sascs
--

ALTER SEQUENCE viewer.annotation_annotation_id_seq OWNED BY viewer.annotation.annotation_id;


--
-- Name: category; Type: TABLE; Schema: viewer; Owner: sascs
--

CREATE TABLE viewer.category (
    concept_id integer NOT NULL,
    section character varying(30),
    category character varying(30),
    question character varying(255)
);


ALTER TABLE viewer.category OWNER TO sascs;

--
-- Name: flag; Type: TABLE; Schema: viewer; Owner: sascs
--

CREATE TABLE viewer.flag (
    content_id integer NOT NULL,
    flag character varying(20),
    case_id integer NOT NULL,
    created timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


ALTER TABLE viewer.flag OWNER TO sascs;

--
-- Name: metadata; Type: TABLE; Schema: viewer; Owner: sascs
--

CREATE TABLE viewer.metadata (
    metadata_id integer NOT NULL,
    name character varying NOT NULL,
    description character varying,
    tag character varying NOT NULL,
    viewer_config json
);


ALTER TABLE viewer.metadata OWNER TO sascs;

--
-- Name: metadata_metadata_id_seq; Type: SEQUENCE; Schema: viewer; Owner: sascs
--

CREATE SEQUENCE viewer.metadata_metadata_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE viewer.metadata_metadata_id_seq OWNER TO sascs;

--
-- Name: metadata_metadata_id_seq; Type: SEQUENCE OWNED BY; Schema: viewer; Owner: sascs
--

ALTER SEQUENCE viewer.metadata_metadata_id_seq OWNED BY viewer.metadata.metadata_id;


--
-- Name: user; Type: TABLE; Schema: viewer; Owner: sascs
--

CREATE TABLE viewer."user" (
    user_id integer NOT NULL
);


ALTER TABLE viewer."user" OWNER TO sascs;

--
-- Name: user_user_id_seq; Type: SEQUENCE; Schema: viewer; Owner: sascs
--

CREATE SEQUENCE viewer.user_user_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE viewer.user_user_id_seq OWNER TO sascs;

--
-- Name: user_user_id_seq; Type: SEQUENCE OWNED BY; Schema: viewer; Owner: sascs
--

ALTER SEQUENCE viewer.user_user_id_seq OWNED BY viewer."user".user_id;


--
-- Name: annotation annotation_id; Type: DEFAULT; Schema: viewer; Owner: sascs
--

ALTER TABLE ONLY viewer.annotation ALTER COLUMN annotation_id SET DEFAULT nextval('viewer.annotation_annotation_id_seq'::regclass);


--
-- Name: metadata metadata_id; Type: DEFAULT; Schema: viewer; Owner: sascs
--

ALTER TABLE ONLY viewer.metadata ALTER COLUMN metadata_id SET DEFAULT nextval('viewer.metadata_metadata_id_seq'::regclass);


--
-- Name: user user_id; Type: DEFAULT; Schema: viewer; Owner: sascs
--

ALTER TABLE ONLY viewer."user" ALTER COLUMN user_id SET DEFAULT nextval('viewer.user_user_id_seq'::regclass);


--
-- Name: annotation annotation_pk; Type: CONSTRAINT; Schema: viewer; Owner: sascs
--

ALTER TABLE ONLY viewer.annotation
    ADD CONSTRAINT annotation_pk PRIMARY KEY (annotation_id);


--
-- Name: category category_pk; Type: CONSTRAINT; Schema: viewer; Owner: sascs
--

ALTER TABLE ONLY viewer.category
    ADD CONSTRAINT category_pk PRIMARY KEY (concept_id);


--
-- Name: metadata metadata_pk; Type: CONSTRAINT; Schema: viewer; Owner: sascs
--

ALTER TABLE ONLY viewer.metadata
    ADD CONSTRAINT metadata_pk PRIMARY KEY (metadata_id);


--
-- Name: metadata metadata_un; Type: CONSTRAINT; Schema: viewer; Owner: sascs
--

ALTER TABLE ONLY viewer.metadata
    ADD CONSTRAINT metadata_un UNIQUE (tag);


--
-- Name: user user_pk; Type: CONSTRAINT; Schema: viewer; Owner: sascs
--

ALTER TABLE ONLY viewer."user"
    ADD CONSTRAINT user_pk PRIMARY KEY (user_id);


--
-- Name: flag viewer_data_pk; Type: CONSTRAINT; Schema: viewer; Owner: sascs
--

ALTER TABLE ONLY viewer.flag
    ADD CONSTRAINT viewer_data_pk PRIMARY KEY (content_id);


--
-- Name: annotation_annotation_id_uindex; Type: INDEX; Schema: viewer; Owner: sascs
--

CREATE UNIQUE INDEX annotation_annotation_id_uindex ON viewer.annotation USING btree (annotation_id);


--
-- Name: category_concept_code_uindex; Type: INDEX; Schema: viewer; Owner: sascs
--

CREATE UNIQUE INDEX category_concept_code_uindex ON viewer.category USING btree (concept_id);


--
-- Name: user_user_id_uindex; Type: INDEX; Schema: viewer; Owner: sascs
--

CREATE UNIQUE INDEX user_user_id_uindex ON viewer."user" USING btree (user_id);


--
-- Name: viewer_data_observation_id_uindex; Type: INDEX; Schema: viewer; Owner: sascs
--

CREATE UNIQUE INDEX viewer_data_observation_id_uindex ON viewer.flag USING btree (content_id);


--
-- PostgreSQL database dump complete
--

\unrestrict lEkn5aFhOUPIWaBUwjr3I1w54Ml3hMPsjvaKByOdXewX9SAeruT0ru5xNraohBb

