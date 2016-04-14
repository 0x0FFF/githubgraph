create table github_activity (
    user_unique_id bigint,
    login varchar,
    repo_id bigint,
    repo_name varchar,
    repo_url varchar
);

insert into repos (repo)
    select r.repo_name
        from (
                select repo_name, count(*)
                    from github_activity
                    group by 1
                    order by 2 desc
                    limit 100
            ) as r
            left join repos as r2
                on r.repo_name = r2.repo
        where r2.id is null;