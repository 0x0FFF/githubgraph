create table last_commit (
    id serial,
    repo_id bigint,
    user_unique_id bigint,
    repo varchar,
    commit_hash varchar,
    status varchar
);

insert into last_commit (repo_id, user_unique_id, repo, commit_hash)
    select  repo_id,
            user_unique_id,
            repo,
            commit_hash
        from (
            select  repo_id,
                    user_unique_id,
                    repo,
                    first_value(commit_hash) over (partition by repo_id, user_unique_id order by commit_date desc) as commit_hash
                from (
                    select  r.id as repo_id,
                            c.id as commit_id,
                            u.unique_id as user_unique_id,
                            r.repo,
                            c.commit_hash,
                            c.commit_date
                        from repos as r,
                             commits as c,
                             users as u
                        where r.id = c.repo_id
                            and lower(c.author_name) = u.author_name
                            and lower(c.author_email) = u.author_email
                    ) as q
            ) as q2
        group by 1,2,3,4;
