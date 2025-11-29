import os
import sqlite3

import pandas as pd
import streamlit as st

DB_FILE = '../logs/log.db'


# Проверка существования БД
def check_db():
    if not os.path.exists(DB_FILE):
        raise FileNotFoundError(f"База данных не найдена: {DB_FILE}")


# Получить все типы операций из БД
@st.cache_data(ttl=300)
def get_event_types():
    try:
        with sqlite3.connect(DB_FILE) as db:
            df = pd.read_sql_query("SELECT DISTINCT event_type FROM logs ORDER BY event_type", db)
            return df['event_type'].tolist()
    except Exception as e:
        st.error(f"Ошибка получения типов событий: {e}")
        return []


# Загрузка данных из БД
@st.cache_data(ttl=60)
def load_logs(params):
    try:
        with sqlite3.connect(DB_FILE) as db:
            query = "SELECT id, event_type, timestamp, duration FROM logs WHERE 1=1"
            args = []

            if params['event_type']:
                query += " AND event_type = ?"
                args.append(params['event_type'])

            query += " AND timestamp >= ?"
            args.append(params['start_datetime'].strftime('%Y-%m-%d %H:%M:%S'))

            query += " AND timestamp <= ?"
            args.append(params['end_datetime'].strftime('%Y-%m-%d %H:%M:%S'))

            if params['min_duration'] is not None:
                query += " AND (duration IS NOT NULL AND duration >= ?)"
                args.append(params['min_duration'])

            if params['max_duration'] is not None:
                query += " AND (duration IS NOT NULL AND duration <= ?)"
                args.append(params['max_duration'])

            query += " ORDER BY timestamp DESC"
            if params['limit']:
                query += " LIMIT ?"
                args.append(params['limit'])

            df = pd.read_sql_query(query, db, params=args)
        return df
    except Exception as e:
        st.error(f"Ошибка чтения БД: {e}")
        return pd.DataFrame()
