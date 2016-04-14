create table commits (
    id serial,
    repo_id bigint,
    commit_hash varchar,
    author_name varchar,
    author_email varchar,
    commit_date timestamp,
    files_changed int,
    insertions int,
    deletions int
);
