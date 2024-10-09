--
-- PostgreSQL database dump
--

-- Dumped from database version 16.2 (Debian 16.2-1.pgdg120+1)
-- Dumped by pg_dump version 16.2 (Debian 16.2-1.pgdg120+1)

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

--
-- Name: delete_evaluated_submission(); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.delete_evaluated_submission() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
  IF NEW.evaluated = TRUE THEN
    DELETE FROM submissions WHERE id = NEW.id;
    RETURN NULL;
  ELSE
    RETURN NEW;
  END IF;
END;
$$;


ALTER FUNCTION public.delete_evaluated_submission() OWNER TO postgres;

--
-- Name: update_best_score(); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.update_best_score() RETURNS trigger
    LANGUAGE plpgsql
    AS $$BEGIN
  IF NEW.score_best = -1 OR NEW.score_best = 0 OR (NEW.score_last <= NEW.score_best AND NEW.result = 0) THEN
    NEW.score_best := NEW.score_last;
    NEW.best_source := NEW.last_source;
    RETURN NEW;
  END IF;
  RETURN NEW;
END;
$$;


ALTER FUNCTION public.update_best_score() OWNER TO postgres;

--
-- Name: update_results_timestamp(); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.update_results_timestamp() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
  UPDATE results
  SET time = CURRENT_TIMESTAMP AT TIME ZONE 'Europe/Prague'
  WHERE userid = NEW.userid AND taskid = NEW.taskid;
  RETURN NEW;
END;
$$;


ALTER FUNCTION public.update_results_timestamp() OWNER TO postgres;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: results; Type: TABLE; Schema: public; Owner: qtrvsim
--

CREATE TABLE public.results (
    userid bigint NOT NULL,
    taskid bigint NOT NULL,
    result_file text,
    last_source text,
    best_source text,
    score_last integer DEFAULT '-1'::integer,
    score_best integer DEFAULT '-1'::integer,
    "time" timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    result smallint DEFAULT '-1'::integer
);


ALTER TABLE public.results OWNER TO qtrvsim;

--
-- Name: submissions; Type: TABLE; Schema: public; Owner: qtrvsim
--

CREATE TABLE public.submissions (
    id integer NOT NULL,
    userid integer NOT NULL,
    taskid integer NOT NULL,
    file text,
    evaluated boolean DEFAULT false,
    "time" timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.submissions OWNER TO qtrvsim;

--
-- Name: submissions_id_seq; Type: SEQUENCE; Schema: public; Owner: qtrvsim
--

ALTER TABLE public.submissions ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.submissions_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: tasks; Type: TABLE; Schema: public; Owner: qtrvsim
--

CREATE TABLE public.tasks (
    id integer NOT NULL,
    name character varying(64) NOT NULL,
    path character varying(256) NOT NULL,
    available boolean DEFAULT true,
    sequence integer DEFAULT 0
);


ALTER TABLE public.tasks OWNER TO qtrvsim;

--
-- Name: tasks_id_seq; Type: SEQUENCE; Schema: public; Owner: qtrvsim
--

ALTER TABLE public.tasks ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.tasks_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: users; Type: TABLE; Schema: public; Owner: qtrvsim
--

CREATE TABLE public.users (
    id integer NOT NULL,
    email character varying(128) NOT NULL,
    password character varying(128) NOT NULL,
    salt character varying(128) NOT NULL,
    token character varying(128) DEFAULT NULL::character varying,
    verified boolean DEFAULT false,
    username character varying(128) NOT NULL,
    admin boolean DEFAULT false,
    display_name character varying(64),
    country character varying(128),
    organization character varying(256),
    "group" character varying(128),
    visibility integer DEFAULT 0
);


ALTER TABLE public.users OWNER TO qtrvsim;

--
-- Name: users_id_seq; Type: SEQUENCE; Schema: public; Owner: qtrvsim
--

ALTER TABLE public.users ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.users_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: results results_pkey; Type: CONSTRAINT; Schema: public; Owner: qtrvsim
--

ALTER TABLE ONLY public.results
    ADD CONSTRAINT results_pkey PRIMARY KEY (userid, taskid);


--
-- Name: submissions submissions_pkey; Type: CONSTRAINT; Schema: public; Owner: qtrvsim
--

ALTER TABLE ONLY public.submissions
    ADD CONSTRAINT submissions_pkey PRIMARY KEY (id);


--
-- Name: tasks tasks_pkey; Type: CONSTRAINT; Schema: public; Owner: qtrvsim
--

ALTER TABLE ONLY public.tasks
    ADD CONSTRAINT tasks_pkey PRIMARY KEY (id);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: qtrvsim
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: submissions after_submission_update; Type: TRIGGER; Schema: public; Owner: qtrvsim
--

CREATE TRIGGER after_submission_update AFTER UPDATE ON public.submissions FOR EACH ROW WHEN (((old.evaluated IS DISTINCT FROM new.evaluated) AND (new.evaluated = true))) EXECUTE FUNCTION public.delete_evaluated_submission();


--
-- Name: results update_best_score_trigger; Type: TRIGGER; Schema: public; Owner: qtrvsim
--

CREATE TRIGGER update_best_score_trigger BEFORE INSERT OR UPDATE ON public.results FOR EACH ROW EXECUTE FUNCTION public.update_best_score();


--
-- Name: submissions update_results_after_insert; Type: TRIGGER; Schema: public; Owner: qtrvsim
--

CREATE TRIGGER update_results_after_insert AFTER INSERT ON public.submissions FOR EACH ROW EXECUTE FUNCTION public.update_results_timestamp();


--
-- PostgreSQL database dump complete
--