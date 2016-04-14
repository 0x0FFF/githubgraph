delete from repos where id in (59, 90);

﻿create table all_weeks (dt date);
insert into all_weeks (dt)
    select date_trunc('week', dt)::date
        from (
            select '2006-01-01'::date + interval '1 day' * i as dt
                from generate_series(1,5000) as i
            ) as q
        where dt < '2016-03-01'::date
        group by 1
        order by 1;

drop table if exists repo_changes;

create table repo_changes (
    repo_id bigint,
    week    date,
    changes bigint,
    changed bigint,
    uniques bigint,
    size    float8
);

insert into repo_changes (repo_id, week, changes, changed)
    select  r.repo_id,
            r.week,
            sum(changes) over (partition by r.repo_id order by r.week rows between 10 preceding and current row),
            sum(changed) over (partition by r.repo_id order by r.week rows between 10 preceding and current row)
        from (
                select  id as repo_id,
                        dt as week
                    from repos,
                         all_weeks
            ) as r
            left join (
                select  repo_id,
                        date_trunc('week', commit_date)::date as week,
                        sum(change) as changes,
                        sum(changed) as changed
                    from (
                        select  repo_id,
                                insertions + deletions as changed,
                                1 as change,
                                commit_date
                            from author_commits
                            --where insertions + deletions < 10000
                        ) as c
                    group by 1, 2
            ) as c2
            on r.repo_id = c2.repo_id and r.week = c2.week
        order by 1, 2;

update repo_changes as rc
    set uniques = t.uniques
    from (
        select  repo_id,
                week,
                count(distinct user_unique_id) as uniques
            from (
                select  r.repo_id,
                        r.week,
                        c.user_unique_id
                    from (
                            select  id as repo_id,
                                    dt as week
                                from repos,
                                     all_weeks
                        ) as r
                        left join
                        (
                            select  repo_id,
                                    date_trunc('week', commit_date)::date as week,
                                    user_unique_id
                                from author_commits
                        ) as c
                        on r.repo_id = c.repo_id
                            and c.week <= r.week
                            and c.week >= r.week - interval '1 week' * 10
                ) as q
            group by repo_id, week
        ) as t
    where t.repo_id = rc.repo_id
        and t.week = rc.week;

update repo_changes
    set size = least(coalesce(uniques,0)::float8 / (select max(uniques) from repo_changes), 1.0);

drop table if exists edges;

create table edges (
    first_id bigint,
    second_id bigint,
    week date
);

insert into edges (first_id, second_id, week)
    select  c1.repo_id as first_id,
            c2.repo_id as second_id,
            date_trunc('week', c1.commit_date)::date as week
        from author_commits as c1
            inner join author_commits as c2
            on c1.user_unique_id = c2.user_unique_id
                and c1.repo_id < c2.repo_id
                and c1.commit_date < c2.commit_date
                and c2.commit_date - c1.commit_date <= interval '1 week' * 10
        group by 1, 2, 3
        order by 1, 2, 3;




