create table github_users (
    user_unique_id bigint,
    id bigint,
    login varchar,
    url varchar,
    html_url varchar,
    repos_url varchar,
    type varchar,
    processed int default 0
);
