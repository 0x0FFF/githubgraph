create table users_full (
    id serial,
    unique_id bigint,
    author_name varchar,
    author_email varchar
);

insert into users_full (id, unique_id, author_name, author_email)
    select id, unique_id, author_name, author_email
        from users;

insert into users_full(author_name, author_email)
    select n.author_name,
           n.author_email
         from (
             select  lower(author_name) as author_name,
                     lower(author_email) as author_email
                 from commits
                 group by 1, 2
             ) as n
             left join (
                 select author_name,
                        author_email
                     from users_full
                     group by 1, 2
                 ) as o
                 on n.author_name = o.author_name
                 and n.author_email = o.author_email
            where o.author_name is null and o.author_email is null;

update users_full
    set unique_id = id
    where unique_id is null;

-- Repeat until there is no more updates

update users_full as u
    set unique_id = least(u.unique_id, t.unique_id)
    from (
        select author_name,
               min(unique_id) as unique_id
            from users_full
            where length(author_name) > 3
            group by author_name
        ) as t
    where u.author_name = t.author_name
        and u.unique_id <> t.unique_id;

update users_full as u
    set unique_id = least(u.unique_id, t.unique_id)
    from (
        select author_email,
               min(unique_id) as unique_id
            from users_full
            where length(author_email) > 3
            group by author_email
        ) as t
    where length(t.author_email) > 3
        and u.author_email = t.author_email
        and u.unique_id <> t.unique_id;

create table author_commits (
    repo_id bigint,
    user_unique_id bigint,
    commit_date timestamp,
    files_changed int,
    insertions int,
    deletions int
);

insert into author_commits
    select  c.repo_id,
            u.unique_id,
            c.commit_date,
            c.files_changed,
            c.insertions,
            c.deletions
        from commits as c,
             users_full as u
        where lower(c.author_name) = u.author_name
            and lower(c.author_email) = u.author_email
            and commit_date >= '2006-01-01 00:00:00'::timestamp
            and commit_date < '2016-03-01 00:00:00'::timestamp;

copy author_commits to '/data/data/author_commits.csv' header csv delimiter '|';