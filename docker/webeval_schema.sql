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
    can_submit boolean NOT NULL DEFAULT true,
    user_api_key character varying(64),
    user_api_key_expiry timestamp with time zone,
    settings jsonb DEFAULT '{}'::jsonb,
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
-- Table: submission_statistics
--
CREATE TABLE submission_statistics (
    userid uuid NOT NULL,
    taskid integer NOT NULL,
    submission_count integer NOT NULL DEFAULT 0,
    first_submission_time timestamp with time zone,
    last_submission_time timestamp with time zone,
    PRIMARY KEY (userid, taskid),
    FOREIGN KEY (userid) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (taskid) REFERENCES tasks(id) ON DELETE CASCADE
);

CREATE INDEX idx_submission_statistics_userid ON submission_statistics(userid);
CREATE INDEX idx_submission_statistics_taskid ON submission_statistics(taskid);

--
-- Trigger function to update submission statistics
--
CREATE OR REPLACE FUNCTION update_submission_statistics()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO submission_statistics (userid, taskid, submission_count, first_submission_time, last_submission_time)
    VALUES (NEW.userid, NEW.taskid, 1, NEW."time", NEW."time")
    ON CONFLICT (userid, taskid)
    DO UPDATE SET
        submission_count = submission_statistics.submission_count + 1,
        last_submission_time = NEW."time";
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_submission_statistics
    AFTER INSERT ON submissions
    FOR EACH ROW
    EXECUTE FUNCTION update_submission_statistics();

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
-- Table: api_keys
--
CREATE TABLE api_keys (
    id integer NOT NULL,
    key character varying(64) NOT NULL,
    created_by uuid NOT NULL,
    created_at timestamp with time zone NOT NULL DEFAULT NOW(),
    last_used timestamp with time zone,
    description character varying(255),
    active boolean NOT NULL DEFAULT true,
    PRIMARY KEY (id),
    UNIQUE (key),
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE CASCADE
);

CREATE SEQUENCE api_keys_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE api_keys_id_seq OWNED BY api_keys.id;
ALTER TABLE ONLY api_keys ALTER COLUMN id SET DEFAULT nextval('api_keys_id_seq'::regclass);

CREATE INDEX idx_api_keys_key ON api_keys(key);
CREATE INDEX idx_api_keys_active ON api_keys(active);

--
-- Permissions
--
ALTER TABLE users OWNER TO qtrvsim;
ALTER TABLE tasks OWNER TO qtrvsim;
ALTER TABLE results OWNER TO qtrvsim;
ALTER TABLE submissions OWNER TO qtrvsim;
ALTER TABLE submission_statistics OWNER TO qtrvsim;
ALTER TABLE api_keys OWNER TO qtrvsim;
