from datetime import datetime, timedelta

import streamlit as st


# Доска параметров
def user_input_features(event_types):
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


# Вывод фильтров
def show_filters(params):
    st.subheader("Фильтры")
    st.json({
        "Тип операции": params['event_type'] or "Все",
        "Период": f"{params['start_datetime'].strftime('%Y-%m-%d')} — {params['end_datetime'].strftime('%Y-%m-%d')}",
        "Группировка": f"{params['group_hours']} ч",
        "Длительность": f"{params['min_duration'] or 0} – {params['max_duration'] or '∞'} сек",
        "Лимит записей": params['limit']
    })
