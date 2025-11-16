--
-- PostgreSQL database schema for QtRVSim Web Evaluation
-- Using UUID for user IDs to prevent user enumeration
--

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

--
-- Table: users
--
CREATE TABLE users (
    id uuid DEFAULT uuid_generate_v4() NOT NULL,
    email character varying(255) NOT NULL,
    password character varying(255) NOT NULL,
    salt character varying(255) NOT NULL,
    token character varying(255),
    verified boolean NOT NULL DEFAULT false,
    username character varying(255) NOT NULL,
    admin boolean NOT NULL DEFAULT false,
    display_name character varying(255),
    country character varying(255),
    organization character varying(255),
    "group" character varying(255),
    visibility integer NOT NULL DEFAULT 0,
    PRIMARY KEY (id),
    UNIQUE (email),
    UNIQUE (username)
);

--
-- Table: tasks
--
CREATE TABLE tasks (
    id integer NOT NULL,
    name character varying(255) NOT NULL,
    path character varying(255) NOT NULL,
    available boolean NOT NULL DEFAULT true,
    sequence integer NOT NULL,
    PRIMARY KEY (id),
    UNIQUE (name),
    UNIQUE (path)
);

CREATE SEQUENCE tasks_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE tasks_id_seq OWNED BY tasks.id;
ALTER TABLE ONLY tasks ALTER COLUMN id SET DEFAULT nextval('tasks_id_seq'::regclass);

--
-- Table: results
--
CREATE TABLE results (
    userid uuid NOT NULL,
    taskid integer NOT NULL,
    result_file text,
    last_source text,
    best_source text,
    score_last integer,
    score_best integer,
    "time" timestamp with time zone,
    result integer,
    PRIMARY KEY (userid, taskid),
    FOREIGN KEY (userid) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (taskid) REFERENCES tasks(id) ON DELETE CASCADE
);

CREATE INDEX idx_results_userid ON results(userid);
CREATE INDEX idx_results_taskid ON results(taskid);

--
-- Table: submissions
--
CREATE TABLE submissions (
    id integer NOT NULL,
    userid uuid NOT NULL,
    taskid integer NOT NULL,
    file text NOT NULL,
    evaluated boolean NOT NULL DEFAULT false,
    "time" timestamp with time zone NOT NULL DEFAULT NOW(),
    PRIMARY KEY (id),
    FOREIGN KEY (userid) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (taskid) REFERENCES tasks(id) ON DELETE CASCADE
);

CREATE SEQUENCE submissions_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE submissions_id_seq OWNED BY submissions.id;
ALTER TABLE ONLY submissions ALTER COLUMN id SET DEFAULT nextval('submissions_id_seq'::regclass);

CREATE INDEX idx_submissions_userid ON submissions(userid);
CREATE INDEX idx_submissions_taskid ON submissions(taskid);
CREATE INDEX idx_submissions_evaluated ON submissions(evaluated);

--
-- Trigger function to update best score
--
CREATE OR REPLACE FUNCTION update_best_score()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.score_last IS NOT NULL AND NEW.score_last > 0 THEN
        IF NEW.score_best IS NULL OR NEW.score_best < 0 OR NEW.score_last < NEW.score_best THEN
            NEW.score_best := NEW.score_last;
            NEW.best_source := NEW.last_source;
        END IF;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_best_score
    BEFORE INSERT OR UPDATE ON results
    FOR EACH ROW
    EXECUTE FUNCTION update_best_score();

--
-- Trigger function to update timestamp
--
CREATE OR REPLACE FUNCTION update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW."time" := NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_results_timestamp
    BEFORE UPDATE ON results
    FOR EACH ROW
    EXECUTE FUNCTION update_timestamp();

--
-- Permissions
--
ALTER TABLE users OWNER TO qtrvsim;
ALTER TABLE tasks OWNER TO qtrvsim;
ALTER TABLE results OWNER TO qtrvsim;
ALTER TABLE submissions OWNER TO qtrvsim;
