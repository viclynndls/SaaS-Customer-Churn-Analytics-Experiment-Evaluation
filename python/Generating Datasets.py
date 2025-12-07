# -*- coding: utf-8 -*-
"""
Created on Fri Nov 28 07:57:04 2025

@author: books
"""

import numpy as np
import pandas as pd
from faker import Faker
import random
import uuid
from datetime import datetime, timedelta

# Reproducibility
RANDOM_SEED = 42
np.random.seed(RANDOM_SEED)
random.seed(RANDOM_SEED)

fake = Faker()

# Global settings
N_USERS = 5000
AVG_EVENTS_PER_USER = 40
AVG_SURVEYS_PER_USER = 0.4
EXPERIMENT_PROPORTION = 0.6  

START_DATE = datetime(2023, 1, 1)
END_DATE = datetime(2024, 12, 31)

PLAN_TYPES = ["free", "basic", "premium"]
ACQ_CHANNELS = ["facebook_ads", "google_ads", "referral", "organic", "email"]
DEVICES = ["ios", "android", "web"]


def random_date(start, end):
    """Random date between start and end."""
    delta = end - start
    rand_days = random.randint(0, delta.days)
    return start + timedelta(days=rand_days)


# -----------------------
# USERS
# -----------------------

def generate_users(n=N_USERS):
    rows = []
    for i in range(n):
        user_id = str(uuid.uuid4())
        signup = random_date(START_DATE, END_DATE - timedelta(days=90))
        age = np.random.normal(32, 10)
        age = int(max(16, age))  
        gender = random.choice(["female", "male", "nonbinary", "prefer_not_to_say"])
        plan = random.choices(PLAN_TYPES, weights=[0.5, 0.3, 0.2])[0]
        channel = random.choices(ACQ_CHANNELS, weights=[0.3, 0.3, 0.15, 0.2, 0.05])[0]
        device = random.choices(DEVICES, weights=[0.4, 0.4, 0.2])[0]
        country = random.choice(["USA", "Canada", "Mexico", "UK"])
        rows.append(
            {
                "user_id": user_id,
                "signup_date": signup,  
                "country": country,
                "age": age,
                "gender": gender,
                "plan_type": plan,
                "acquisition_channel": channel,
                "primary_device": device,
            }
        )
    df = pd.DataFrame(rows)
    df = inject_user_messiness(df)
    return df


def inject_user_messiness(df: pd.DataFrame) -> pd.DataFrame:
    n = len(df)

    # --- signup_date format inconsistencies ---
    date_formats = ["%Y-%m-%d", "%d-%m-%Y", "%m/%d/%Y", "%b %d %Y"]
    string_dates = []
    for d in df["signup_date"]:
        fmt = random.choice(date_formats)
        string_dates.append(d.strftime(fmt))
    df["signup_date"] = string_dates

    # --- country casing issues ---
    df.loc[df.sample(frac=0.3, random_state=RANDOM_SEED).index, "country"] = (
        df["country"].str.lower()
    )
    df.loc[df.sample(frac=0.15, random_state=RANDOM_SEED + 1).index, "country"] = (
        df["country"].str.upper()
    )

    # --- missing age (10%) ---
    df.loc[df.sample(frac=0.10, random_state=RANDOM_SEED + 2).index, "age"] = np.nan

    # --- out-of-range ages ---
    bad_age_idx = df.sample(frac=0.03, random_state=RANDOM_SEED + 3).index
    for i in bad_age_idx:
        df.at[i, "age"] = random.choice([-5, -10, 120, 150])

    # --- missing acquisition_channel (5%) ---
    df.loc[df.sample(frac=0.05, random_state=RANDOM_SEED + 4).index, "acquisition_channel"] = np.nan

    # --- dirty acquisition_channel spellings ---
    dirty_map = {
        "facebook_ads": ["facebook", "FB", "Fbook", "meta_ads"],
        "google_ads": ["google", "Adwords", "ggl"],
        "referral": ["referal", "friend_ref"],
        "organic": ["Organic", "org", "ORG"],
        "email": ["Email ", "e-mail", "MAIL"],
    }
    idx = df.sample(frac=0.25, random_state=RANDOM_SEED + 5).index
    for i in idx:
        ch = df.at[i, "acquisition_channel"]
        if pd.isna(ch) or ch not in dirty_map:
            continue
        df.at[i, "acquisition_channel"] = random.choice(dirty_map[ch])

    # --- gender typos ---
    gender_typos = {
        "female": ["Fmale", "Femal", "f"],
        "male": ["Mle", "Ml", "m"],
    }
    idx = df.sample(frac=0.15, random_state=RANDOM_SEED + 6).index
    for i in idx:
        g = df.at[i, "gender"]
        if g in gender_typos:
            df.at[i, "gender"] = random.choice(gender_typos[g])

    # --- missing primary_device (7%) ---
    df.loc[df.sample(frac=0.07, random_state=RANDOM_SEED + 7).index, "primary_device"] = np.nan

    # --- duplicate some users (2%) with slight differences ---
    dup_df = df.sample(frac=0.02, random_state=RANDOM_SEED + 8).copy()
    dup_df["plan_type"] = dup_df["plan_type"].replace({"free": "freemium"})
    df = pd.concat([df, dup_df], ignore_index=True)

    return df


# -----------------------
# SUBSCRIPTIONS
# -----------------------

def generate_subscriptions(users: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, row in users.iterrows():
        user_id = row["user_id"]
        # 70% have a subscription (rest free only)
        if random.random() < 0.3:
            continue
        
        n_subs = 1 if random.random() < 0.8 else 2
        start_dt = random_date(START_DATE, END_DATE - timedelta(days=365))
        for s in range(n_subs):
            sub_id = str(uuid.uuid4())
            start_date = start_dt + timedelta(days=random.randint(0, 30))
            # some weird durations
            length_days = random.choice([30, 30, 30, 365, -10, 0, 365 * 10])
            end_date = start_date + timedelta(days=length_days)
            billing = random.choice(
                ["monthly", "mth", "Monthly", "mo", "annual", "yr", "yearly", "annual "]
            )
            price = random.choice([0, 9.99, 14.99, 29.99, -5.00, 9999.99])
            is_active = length_days in [30, 365] and random.random() < 0.7
            rows.append(
                {
                    "subscription_id": sub_id,
                    "user_id": user_id,
                    "start_date": start_date.strftime("%Y-%m-%d"),
                    "end_date": end_date.strftime("%Y-%m-%d"),
                    "billing_period": billing,
                    "price_usd": price,
                    "is_active": is_active,
                }
            )
    return pd.DataFrame(rows)


# -----------------------
# EVENTS
# -----------------------

def generate_events(users: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, row in users.iterrows():
        user_id = row["user_id"]
        # average events per user, Poisson distributed
        n_events = np.random.poisson(AVG_EVENTS_PER_USER)
        if n_events == 0:
            continue
        session_ids = [str(uuid.uuid4()) for _ in range(max(1, n_events // 5))]
        for i in range(n_events):
            event_id = str(uuid.uuid4())
            
            event_time = random_date(
                START_DATE - timedelta(days=30),
                END_DATE + timedelta(days=30),
            )
            event_type = random.choice(
                ["app_open", "app_open", "complete_session", "view_paywall", "start_trial", "cancel"]
            )
            # inject typos
            if random.random() < 0.15:
                typo_map = {
                    "app_open": ["ap_open", "open", "appOpen"],
                    "complete_session": ["complete", "finish_session"],
                    "view_paywall": ["view_pay", "paywall_view"],
                }
                if event_type in typo_map:
                    event_type = random.choice(typo_map[event_type])
            session_id = random.choice(session_ids)
            device_type = random.choice(["ios", "android", "web", "Windows Phone", "PlayStation"])
            platform = random.choice(["ios", "android", "web", "PlayStation"])
            # occasionally null session/device
            if random.random() < 0.03:
                session_id = None
            if random.random() < 0.04:
                device_type = None
            rows.append(
                {
                    "event_id": event_id,
                    "user_id": user_id,
                    "event_time": event_time.isoformat(),
                    "event_type": event_type,
                    "session_id": session_id,
                    "device_type": device_type,
                    "platform": platform,
                }
            )

    # add events with unknown users (3% of events)
    base_events = len(rows)
    extra_events = int(base_events * 0.03)
    for _ in range(extra_events):
        rows.append(
            {
                "event_id": str(uuid.uuid4()),
                "user_id": str(uuid.uuid4()),  # not in users
                "event_time": random_date(START_DATE, END_DATE).isoformat(),
                "event_type": random.choice(["app_open", "complete_session"]),
                "session_id": str(uuid.uuid4()),
                "device_type": random.choice(["ios", "android", "web"]),
                "platform": random.choice(["ios", "android", "web"]),
            }
        )
    return pd.DataFrame(rows)


# -----------------------
# SURVEY RESPONSES
# -----------------------

def generate_surveys(users: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, row in users.iterrows():
        if random.random() > AVG_SURVEYS_PER_USER:
            continue
        user_id = row["user_id"]
        response_id = str(uuid.uuid4())
        response_date = random_date(START_DATE, END_DATE)
        nps = random.randint(-2, 12)  
        csat = random.choice([0, 1, 2, 3, 4, 5, 6])  
        ease = random.choice(
            ["very_easy", "easy", "neutral", "hard", "very_difficult", "vry_easy"]
        )
        comment = fake.sentence(nb_words=15)
        
        if random.random() < 0.2:
            comment += " 😊 <br> https://example.com"
        rows.append(
            {
                "response_id": response_id,
                "user_id": user_id,
                "response_date": response_date.strftime("%d-%m-%Y"),
                "nps_score": nps,
                "csat_score": csat,
                "ease_of_use": ease,
                "comment_text": comment,
            }
        )
    return pd.DataFrame(rows)


# -----------------------
# EXPERIMENT ASSIGNMENTS
# -----------------------

def generate_experiments(users: pd.DataFrame) -> pd.DataFrame:
    rows = []
    exp_users = users.sample(frac=EXPERIMENT_PROPORTION, random_state=RANDOM_SEED)
    for _, row in exp_users.iterrows():
        user_id = row["user_id"]
        exp_assignment_id = str(uuid.uuid4())
        experiment_name = "onboarding_v2"
        variant = random.choice(["control", "treatment", "cntrl", "cotnrol", "TreatmentT"])
        assignment_date = random_date(START_DATE - timedelta(days=60), END_DATE)
        rows.append(
            {
                "exp_assignment_id": exp_assignment_id,
                "user_id": user_id,
                "experiment_name": experiment_name,
                "variant": variant,
                "assignment_date": assignment_date.strftime("%m/%d/%Y"),
            }
        )

    # some users assigned twice (duplicates)
    dup = pd.DataFrame(rows).sample(frac=0.1, random_state=RANDOM_SEED + 9)
    rows.extend(dup.to_dict(orient="records"))

    # some experiment rows for non-existent users
    for _ in range(50):
        rows.append(
            {
                "exp_assignment_id": str(uuid.uuid4()),
                "user_id": str(uuid.uuid4()),
                "experiment_name": "onboarding_v2",
                "variant": random.choice(["control", "treatment"]),
                "assignment_date": random_date(START_DATE, END_DATE).strftime("%Y-%m-%d"),
            }
        )

    return pd.DataFrame(rows)


# -----------------------
# MAIN
# -----------------------

def main(output_dir: str = "data"):
    import os
    os.makedirs(output_dir, exist_ok=True)

    users = generate_users()
    subs = generate_subscriptions(users)
    events = generate_events(users)
    surveys = generate_surveys(users)
    exps = generate_experiments(users)

    users.to_csv(os.path.join(output_dir, "users.csv"), index=False)
    subs.to_csv(os.path.join(output_dir, "subscriptions.csv"), index=False)
    events.to_csv(os.path.join(output_dir, "events.csv"), index=False)
    surveys.to_csv(os.path.join(output_dir, "survey_responses.csv"), index=False)
    exps.to_csv(os.path.join(output_dir, "experiment_assignments.csv"), index=False)

    print("Generated:")
    print(f" users: {len(users)}")
    print(f" subscriptions: {len(subs)}")
    print(f" events: {len(events)}")
    print(f" surveys: {len(surveys)}")
    print(f" experiments: {len(exps)}")


if __name__ == "__main__":
    main()
