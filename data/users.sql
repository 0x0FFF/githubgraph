create table users (
    id serial,
    unique_id bigint,
    author_name varchar,
    author_email varchar
);

insert into users(author_name, author_email)
    select  lower(author_name) as author_name,
            lower(author_email) as author_email
        from commits
        group by 1, 2;

update users set unique_id = id;

-- Repeat until there is no more updates

update users as u
    set unique_id = least(u.unique_id, t.unique_id)
    from users as t
    where length(t.author_name) > 3
        and u.author_name = t.author_name
        and u.unique_id <> t.unique_id;

update users as u
    set unique_id = least(u.unique_id, t.unique_id)
    from users as t
    where length(t.author_email) > 3
        and u.author_email = t.author_email
        and u.unique_id <> t.unique_id;
