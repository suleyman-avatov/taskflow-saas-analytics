import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os

DB_PATH = "data/taskflow_real.db"
SEED = 42
N_USERS = 500
START_DATE = datetime(2024, 1, 1)
END_DATE = datetime(2024, 6, 30)
ANALYSIS_CUTOFF = datetime(2024, 7, 1)

def generate_users(n: int) -> pd.DataFrame:
    rng = np.random.default_rng(SEED)

    channels = rng.choice(
        ['organic', 'paid_ads', 'referral'],
        size=n,
        p=[0.4, 0.4, 0.2]
    )

    days_range = (END_DATE - START_DATE).days
    reg_dates = [
        START_DATE + timedelta(days=int(d))
        for d in rng.uniform(0, days_range, n)
    ]

    countries = rng.choice(['US', 'UK', 'DE', 'FR', 'RU'], n, p=[0.4, 0.2, 0.15, 0.15, 0.1])

    return pd.DataFrame({
        'user_id': range(1, n + 1),
        'reg_date': reg_dates,
        'channel': channels,
        'country': countries
    })

def generate_subscriptions(users_df: pd.DataFrame) -> pd.DataFrame:
    rng = np.random.default_rng(SEED + 1)
    subs = []

    for _, user in users_df.iterrows():
        pro_prob = 0.3 if user['channel'] == 'organic' else 0.15
        plan = 'pro' if rng.random() < pro_prob else 'basic'

        start_sub = user['reg_date'] + timedelta(hours=int(rng.integers(0, 48)))

        mean_duration = {
            'organic': 120,
            'paid_ads': 45,
            'referral': 90
        }[user['channel']]

        duration_days = max(7, int(rng.exponential(mean_duration)))
        end_sub = start_sub + timedelta(days=duration_days)

        is_active = rng.random() < 0.3
        final_end = None if is_active else end_sub

        subs.append((
            len(subs) + 1,
            int(user['user_id']), 
            plan,
            start_sub.strftime("%Y-%m-%d"),
            final_end.strftime("%Y-%m-%d") if final_end else None
        ))

    return pd.DataFrame(
        subs,
        columns=['sub_id', 'user_id', 'plan_id', 'start_date', 'end_date']
    )

def generate_events(users_df: pd.DataFrame, n_events: int = 8000) -> pd.DataFrame:
    rng = np.random.default_rng(SEED + 2)
    event_types = ['login', 'create_task', 'view_dashboard', 'export_report']
    events = []

    for _ in range(n_events):
        user = users_df.sample(1, random_state=rng.integers(0, 10000)).iloc[0]
        
        days_since_reg = int(rng.integers(0, 150))
        
        if user['channel'] == 'paid_ads' and days_since_reg > 30:
            continue

        evt_date = user['reg_date'] + timedelta(days=days_since_reg)
        evt_type = rng.choice(event_types, p=[0.4, 0.3, 0.2, 0.1])

        events.append((
            int(user['user_id']),
            evt_date.strftime('%Y-%m-%d %H:%M:%S'),
            evt_type
        ))

    return pd.DataFrame(events, columns=['user_id', 'event_time', 'event_type'])

def generate_marketing_spend() -> pd.DataFrame:
    months = pd.date_range('2024-01-01', '2024-06-01', freq='MS')
    spend_data = []

    base_spend = {'organic': 500, 'paid_ads': 3000, 'referral': 200}

    for m in months:
        for channel, base in base_spend.items():
            multiplier = 1 + (m.month - 1) * 0.2 if channel == 'paid_ads' else 1
            spend = round(base * multiplier * (0.9 + 0.2 * np.random.default_rng().random()), 2)
            spend_data.append((m.strftime('%Y-%m'), channel, spend))

    return pd.DataFrame(spend_data, columns=['month', 'channel', 'spend'])

def create_database():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    conn = sqlite3.connect(DB_PATH)

    pd.DataFrame([
        ('basic', 'Basic', 29.0),
        ('pro', 'Pro', 99.0)
    ], columns=['plan_id', 'name', 'price']).to_sql('plans', conn, index=False)

    users = generate_users(N_USERS)
    users.to_sql('users', conn, index=False)

    subs = generate_subscriptions(users)
    subs.to_sql('subscriptions', conn, index=False)

    events = generate_events(users)
    events.to_sql('events', conn, index=False)

    spend = generate_marketing_spend()
    spend.to_sql('marketing_spend', conn, index=False)

    print(f" База создана: {DB_PATH}")
    print(" Статистика:")
    for table in ['users', 'plans', 'subscriptions', 'events', 'marketing_spend']:
        count = pd.read_sql(f"SELECT COUNT(*) FROM {table}", conn).iloc[0, 0]
        print(f"   {table}: {count:,} строк")

    conn.close()

if __name__ == "__main__":
    create_database()