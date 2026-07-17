"""
model.py — Ensemble model (Logistic Regression + Gradient Boosting + Random Forest + Elo).
Trains on all available historical data, predicts today's games.
"""

import numpy as np
import pickle
import os
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
from config import ELO_K, ELO_HFA, MIN_PRIOR_GAMES

FEATURE_COLS = [
    'home_win_pct','away_win_pct','win_pct_diff',
    'home_avg_rs','away_avg_rs','home_avg_ra','away_avg_ra','run_diff_diff',
    'home_sp_era','away_sp_era','era_diff',
    'home_sp_fip','away_sp_fip','fip_diff',
    'home_sp_whip','away_sp_whip',
    'home_recent_era','away_recent_era','recent_era_diff',
    'home_bp_era','away_bp_era','bp_era_diff',
    'park_factor','ump_factor',
    'rest_diff','home_pitcher_rest','away_pitcher_rest','pitcher_rest_diff',
    'home_babip_signal','away_babip_signal','babip_diff',
    'series_game_num',
]

MODEL_PATH = 'model_state.pkl'


def train_models(feature_df, label_col='home_win'):
    """Train ensemble on all available data. Save to disk."""
    valid = feature_df[feature_df['home_games'] >= MIN_PRIOR_GAMES]
    if len(valid) < 50:
        print(f"Only {len(valid)} valid rows — skipping retrain, need 50+")
        return None

    X = valid[FEATURE_COLS].values
    y = valid[label_col].values

    scaler = StandardScaler().fit(X)
    Xs = scaler.transform(X)

    lr = LogisticRegression(max_iter=1000, random_state=42).fit(Xs, y)
    gb = GradientBoostingClassifier(n_estimators=100, max_depth=3,
                                     learning_rate=0.1, random_state=42).fit(X, y)
    rf = RandomForestClassifier(n_estimators=300, max_depth=6, random_state=42).fit(X, y)

    state = {'lr': lr, 'gb': gb, 'rf': rf, 'scaler': scaler, 'n_train': len(valid)}
    with open(MODEL_PATH, 'wb') as f:
        pickle.dump(state, f)
    print(f"Models trained on {len(valid)} games and saved.")
    return state


def load_models():
    """Load trained models from disk."""
    if not os.path.exists(MODEL_PATH):
        return None
    with open(MODEL_PATH, 'rb') as f:
        return pickle.load(f)


def predict_proba_ensemble(feature_dicts, state):
    """
    Predict P(home win) for a list of feature dicts.
    Returns list of probabilities.
    """
    import pandas as pd
    df = pd.DataFrame(feature_dicts)
    X = df[FEATURE_COLS].values
    Xs = state['scaler'].transform(X)
    p_lr = state['lr'].predict_proba(Xs)[:, 1]
    p_gb = state['gb'].predict_proba(X)[:, 1]
    p_rf = state['rf'].predict_proba(X)[:, 1]
    return (p_lr + p_gb + p_rf) / 3


class EloTracker:
    """Tracks Elo ratings across the season."""
    def __init__(self, k=ELO_K, hfa=ELO_HFA):
        self.k = k
        self.hfa = hfa
        self.ratings = {}

    def get_rating(self, team_id):
        return self.ratings.get(team_id, 1500)

    def predict(self, home_id, away_id):
        rh = self.get_rating(home_id) + self.hfa
        ra = self.get_rating(away_id)
        return 1 / (1 + 10 ** ((ra - rh) / 400))

    def update(self, home_id, away_id, home_win):
        p = self.predict(home_id, away_id)
        self.ratings[home_id] = self.get_rating(home_id) + self.k * (home_win - p)
        self.ratings[away_id] = self.get_rating(away_id) + self.k * ((1 - home_win) - (1 - p))

    def save(self, path='elo_state.pkl'):
        with open(path, 'wb') as f:
            pickle.dump(self.ratings, f)

    def load(self, path='elo_state.pkl'):
        if os.path.exists(path):
            with open(path, 'rb') as f:
                self.ratings = pickle.load(f)


def combined_probability(ens_prob, elo_prob, ens_weight=0.7, elo_weight=0.3):
    """Weighted combination of ensemble and Elo probabilities."""
    return ens_weight * ens_prob + elo_weight * elo_prob
