import os
import sqlite3
from datetime import datetime, timedelta

import pandas as pd
import streamlit as st

st.write("# Аналитика работы веб-сервиса")

st.sidebar.header('Ввод данных')

DB_FILE = 'logs/log.db'

if not os.path.exists(DB_FILE):
    st.error(f"База данных не найдена: `{DB_FILE}`\n"
             "Запусти XML-RPC сервер, чтобы создать БД и добавить логи.")
    st.stop()

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


event_types = get_event_types()

# Доска параметров
def user_input_features():
    # Тип события 
    selected_type = st.sidebar.selectbox("Тип события", options=["Все"] + event_types)

    # КАЛЕНДАРЬ: Дата от / до 
    col_from, col_to = st.sidebar.columns(2)

    with col_from:
        start_date = st.date_input(
            "С даты",
            value=datetime.now() - timedelta(days=7),
            min_value=datetime(2000, 1, 1),
            max_value=datetime.now()
        )
    with col_to:
        end_date = st.date_input(
            "По дату",
            value=datetime.now(),
            min_value=datetime(2000, 1, 1),
            max_value=datetime.now()
        )

    # Проверка дат
    if end_date < start_date:
        st.sidebar.error("Дата 'По дату' должна быть не раньше 'С даты'")
        end_date = start_date
    if (end_date - start_date).days < 1:
        st.sidebar.error("Минимальный интервал — 1 день")
        end_date = start_date + timedelta(days=1)

    # к datetime
    start_datetime = datetime.combine(start_date, datetime.min.time())
    end_datetime = datetime.combine(end_date, datetime.max.time())

    group_hours = st.sidebar.select_slider(
        "Интервал группировки, часы",
        # min_value=1, max_value=24, value=4, step=1
        options=[1, 4, 24], value=4
    )

    min_duration = st.sidebar.number_input("Мин. длительность (сек)", min_value=0.0, value=0.0, step=0.1)
    max_duration = st.sidebar.number_input("Макс. длительность (сек)", min_value=0.0, value=100.0, step=0.1)
    limit = st.sidebar.slider("Макс. записей", 10, 1000, 100)

    return {
        'event_type': None if selected_type == "Все" else selected_type,
        'start_datetime': start_datetime,
        'end_datetime': end_datetime,
        'group_hours': group_hours,
        'min_duration': min_duration if min_duration > 0 else None,
        'max_duration': max_duration if max_duration < 100 else None,
        'limit': limit
    }


params = user_input_features()


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


log_data = load_logs(params)

# Вывод фильтров 
st.subheader("Фильтры")
st.json({
    "Тип операции": params['event_type'] or "Все",
    "Период": f"{params['start_datetime'].strftime('%Y-%m-%d')} — {params['end_datetime'].strftime('%Y-%m-%d')}",
    "Группировка": f"{params['group_hours']} ч",
    "Длительность": f"{params['min_duration'] or 0} – {params['max_duration'] or '∞'} сек",
    "Лимит записей": params['limit']
})

# col1, col2 = st.columns([3, 2])

# with col1:
# ГИСТОГРАММА: Количество вызовов по типу 
if not log_data.empty:
    st.subheader("Гистограмма: Количество вызовов по типу операции")

    # Группировка по типу
    count_by_type = log_data['event_type'].value_counts().sort_values(ascending=True)

    chart = st.bar_chart(
        count_by_type,
        use_container_width=True,
        height=400
    )

    st.write("**Тип операции → Количество вызовов**")

else:
    st.info("Нет данных для построения гистограммы.")

# ГИСТОГРАММА: по времени 
if not log_data.empty:
    st.subheader("Гистограмма: Количество вызовов по времени суток")

    df = log_data.copy()
    df['ts'] = pd.to_datetime(df['timestamp'])

    # Группировка по интервалу
    df['time_bin'] = df['ts'].dt.floor(f'{params["group_hours"]}H')

    # Считаем количество в каждом интервале
    counts = df['time_bin'].value_counts().sort_index()

    full_range = pd.date_range(
        start=params['start_datetime'],
        end=params['end_datetime'],
        freq=f'{params["group_hours"]}H'
    )
    counts = counts.reindex(full_range, fill_value=0)

    labels = counts.index.strftime('%H:%M')

    # Если выбрано 24ч, то даты
    if params['group_hours'] == 24:
        labels = counts.index.strftime('%Y-%m-%d')

    # Строим гистограмму
    chart_data = pd.DataFrame({
        'Время': labels,
        'Вызовы': counts.values
    }).set_index('Время')

    st.bar_chart(chart_data, use_container_width=True, height=500)

    title = f"Все типы" if not params['event_type'] else f"Тип: `{params['event_type']}`"
    st.caption(f"Группировка: каждые **{params['group_hours']} ч** | {title}")

else:
    st.info("Нет данных для гистограммы.")

# КРУГОВАЯ ДИАГРАММА по типпм
if not log_data.empty:
    st.subheader("Круговая диаграмма: Распределение по типам операций")

    type_counts = log_data['event_type'].value_counts()

    pie_data = pd.DataFrame({
        'event_type': type_counts.index,
        'count': type_counts.values
    })

    # Диаграмма
    fig = {
        "data": [
            {
                "values": pie_data['count'],
                "labels": pie_data['event_type'],
                "type": "pie",
                "textinfo": "label+percent",
                "insidetextorientation": "radial",
                "hole": 0.3
            }
        ],
        "layout": {
            "title": {
                "text": f"Всего вызовов: {len(log_data)}",
                "x": 0.5,
                "xanchor": "center"
            },
            "showlegend": True,
            "height": 500
        }
    }

    st.plotly_chart(fig, use_container_width=True)

    with st.expander("Таблица распределения"):
        st.dataframe(pie_data.sort_values('count', ascending=False))

else:
    st.info("Нет данных для круговой диаграммы.")

# КРУГОВАЯ ДИАГРАММА: по суммарному времени выполнения 
if not log_data.empty and 'duration' in log_data.columns:
    st.subheader("Круговая диаграмма: Суммарное время выполнения по типам")

    df_time = log_data.dropna(subset=['duration'])

    if df_time.empty:
        st.info("Нет данных с длительностью (duration) для построения диаграммы.")
    else:
        # Сумма по типам
        time_by_type = df_time.groupby('event_type')['duration'].sum().sort_values(ascending=False).round(6)

        # Создаём pie chart
        fig = {
            "data": [{
                "values": time_by_type.values,
                "labels": time_by_type.index,
                "type": "pie",
                "textinfo": "label+value+percent",
                "textposition": "inside",
                "insidetextorientation": "radial",
                "hole": 0.3,
                "marker": {
                    "line": {"width": 2, "color": "white"}
                }
            }],
            "layout": {
                "title": {
                    "text": f"Общее время: {time_by_type.sum():.2f} сек",
                    "x": 0.5,
                    "xanchor": "center"
                },
                "showlegend": True,
                "height": 520,
                "font": {"size": 12}
            }
        }

        st.plotly_chart(fig, use_container_width=True)

        with st.expander("Таблица: суммарное время по типам"):
            detail_df = pd.DataFrame({
                'Тип операции': time_by_type.index,
                'Суммарное время (сек)': time_by_type.values,
                'Доля (%)': (time_by_type / time_by_type.sum() * 100).round(6)
            })
            st.dataframe(detail_df.reset_index(drop=True))
else:
    st.info("Нет данных или отсутствует столбец `duration`.")

# ТЕПЛОВАЯ КАРТА: активность по часам и дням недели 
if not log_data.empty:
    st.subheader("Тепловая карта: Активность по часам и дням недели")

    df = log_data.copy()
    df['ts'] = pd.to_datetime(df['timestamp'])

    # Фильтр по типу (если задан)
    if params.get('event_type'):
        title_suffix = f" (тип: `{params['event_type']}`)"
    else:
        title_suffix = " (все типы)"

    # Извлекаем: день недели и час
    df['weekday'] = df['ts'].dt.day_name(locale='ru_RU')
    df['hour'] = df['ts'].dt.hour

    # Порядок дней недели
    weekday_order = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье']
    df['weekday'] = pd.Categorical(df['weekday'], categories=weekday_order, ordered=True)

    # Группирока (день недели, час) → количество
    heatmap_data = df.groupby(['weekday', 'hour']).size().unstack(fill_value=0)

    for h in range(24):
        if h not in heatmap_data.columns:
            heatmap_data[h] = 0
    heatmap_data = heatmap_data[sorted(heatmap_data.columns)]

    fig = {
        "data": [{
            "type": "heatmap",
            "z": heatmap_data.values,
            "x": heatmap_data.columns,  # Часы
            "y": heatmap_data.index,  # Дни
            "colorscale": "Viridis",
            "colorbar": {"title": "Вызовов"},
            "text": heatmap_data.values,
            "texttemplate": "%{text}",
            "textfont": {"size": 10}
        }],
        "layout": {
            "title": {
                "text": f"Активность по часам и дням недели{title_suffix}",
                "x": 0.5,
                "xanchor": "center"
            },
            "xaxis": {
                "title": "Час суток",
                "tickmode": "linear",
                "dtick": 1
            },
            "yaxis": {
                "title": "День недели",
                "autorange": "reversed"  # Пн сверху
            },
            "height": 500,
            "margin": {"l": 100, "r": 50, "t": 80, "b": 60}
        }
    }

    st.plotly_chart(fig, use_container_width=True)

    with st.expander("Таблица данных"):
        st.dataframe(heatmap_data.style.background_gradient(cmap='viridis'))

else:
    st.info("Нет данных для тепловой карты.")

# Таблица логов 
st.subheader("Логи из SQLite")
if not log_data.empty:
    st.write(f"**Найдено записей: {len(log_data)}**")
    st.dataframe(
        log_data.style.format({
            'timestamp': lambda x: pd.to_datetime(x).strftime('%Y-%m-%d %H:%M:%S') if pd.notna(x) else "—",
            'duration': lambda x: f"{x:.3f}" if pd.notna(x) else "—"
        })
    )
else:
    st.info("Нет данных по заданным фильтрам.")

# Статистика 
if not log_data.empty:
    st.subheader("Статистика")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Всего событий", len(log_data))
    col2.metric("Уникальных типов", log_data['event_type'].nunique())
    durations = log_data['duration'].dropna()
    if len(durations) > 0:
        col3.metric("Средняя длительность", f"{durations.mean():.3f} сек")
        col4.metric("Медиана", f"{durations.median():.3f} сек")
