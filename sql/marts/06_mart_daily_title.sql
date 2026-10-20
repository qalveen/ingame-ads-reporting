-- mart_daily_title
-- Grain: title x day (paid, in-flight) for the reporting month — trend chart source.
with p as (select * from params)
select
    title_id,
    event_date,
    count(*)                            as paid_impressions,
    count(*) filter (where is_viewable) as viewable_impressions,
    count(distinct player_id)           as daily_unique_reach,
    avg(count(*)) over (partition by title_id order by event_date
                        rows between 6 preceding and current row) as paid_impressions_7d_avg
from int_impressions_classified, p
where impression_class = 'paid_in_flight'
  and event_date between p.month_start and p.month_end
group by 1, 2
order by 1, 2
