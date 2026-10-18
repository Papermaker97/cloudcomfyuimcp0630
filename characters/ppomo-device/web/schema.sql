-- Ppomo squeeze log on Supabase (free tier is enough). Paste into the SQL editor once.
-- One row per squeeze. (device_id, seq) is unique, so a device can safely resend after a dropped
-- connection: duplicates are ignored (the firmware posts with Prefer: resolution=ignore-duplicates).

create table if not exists public.squeezes (
  device_id   text        not null,
  seq         integer     not null,            -- 1, 2, 3 ... per device = running total
  ts          timestamptz,                     -- when it was squeezed (device clock); null if the device had no time yet
  received_at timestamptz not null default now(),
  source      text        not null default 'body' check (source in ('body', 'belly', 'butt')),
  peak_pa     integer,                         -- how hard: highest pressure rise in Pa
  boot        integer,
  primary key (device_id, seq)
);
create index if not exists squeezes_device_ts on public.squeezes (device_id, coalesce(ts, received_at) desc);

-- The anon key ships inside the toy and inside the web page, so it may only add and read rows.
alter table public.squeezes enable row level security;
create policy "toys can add squeezes" on public.squeezes for insert to anon with check (true);
create policy "anyone with the page can read" on public.squeezes for select to anon using (true);

-- Per-day totals in New York time, for the dashboard.
create or replace view public.squeezes_per_day with (security_invoker = true) as
select device_id,
       (coalesce(ts, received_at) at time zone 'America/New_York')::date as day,
       count(*) as squeezes
from public.squeezes
group by 1, 2;
