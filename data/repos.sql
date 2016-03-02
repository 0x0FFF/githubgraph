create table repos (
    id serial,
    repo varchar,
    status varchar
);

copy repos(repo) from '/data/data/initial_repos.csv' csv;
