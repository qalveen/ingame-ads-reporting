-- mart_frequency_distribution
-- Grain: title x frequency bucket for the reporting month (paid, in-flight, known players).
with p as (select * from params),
per_player as (
    select title_id, player_id, count(*) as exposures
    from int_impressions_classified, p
    where impression_class = 'paid_in_flight'
      and player_id is not null
      and event_date between p.month_start and p.month_end
    group by 1, 2
),
bucketed as (
    select
        title_id,
        case
            when exposures = 1          then '01'
            when exposures = 2          then '02'
            when exposures = 3          then '03'
            when exposures between 4 and 5   then '04-05'
            when exposures between 6 and 10  then '06-10'
            when exposures between 11 and 20 then '11-20'
            else '21+'
        end as frequency_bucket,
        exposures
    from per_player
)
select
    title_id,
    frequency_bucket,
    count(*)                                                          as players,
    sum(exposures)                                                    as impressions,
    count(*) * 1.0 / sum(count(*)) over (partition by title_id)       as share_of_reach,
    sum(exposures) * 1.0 / sum(sum(exposures)) over (partition by title_id) as share_of_impressions,
    -- cumulative reach share, highest-frequency bucket last
    sum(count(*)) over (partition by title_id order by frequency_bucket
                        rows between unbounded preceding and current row) * 1.0
      / sum(count(*)) over (partition by title_id)                    as cumulative_share_of_reach
from bucketed
group by 1, 2
order by 1, 2
