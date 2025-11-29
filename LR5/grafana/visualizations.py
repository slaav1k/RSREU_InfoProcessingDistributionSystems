import pandas as pd
import streamlit as st
import plotly.express as px


# ГИСТОГРАММА: Количество вызовов по типу
def bar_chart_by_type(log_data):
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
        return


# ГИСТОГРАММА: По средней длительности операций
def bar_chart_by_avg_time(log_data):
    if not log_data.empty:
        st.subheader("Гистограмма: Количество вызовов по типу операции")
        # Группировка по типу
        count_by_type = log_data['event_type'].value_counts().sort_values(ascending=True)
        df_time = log_data.dropna(subset=['duration'])
        time_by_type = ((df_time.groupby('event_type')['duration'].sum()
                        / df_time.groupby('event_type')['duration'].count())
                        .sort_values(ascending=False).round(6))
        chart = st.bar_chart(
            time_by_type,
            use_container_width=True,
            height=400
        )
        st.write("**Тип операции → Количество вызовов**")
    else:
        st.info("Нет данных для построения гистограммы.")
        return


def bar_chart_by_time(log_data, params):
    if log_data.empty:
        st.info("Нет данных для гистограммы.")
        return

    st.subheader("Гистограмма: Количество вызовов по времени суток")

    df = log_data.copy()
    df['ts'] = pd.to_datetime(df['timestamp'])  # преобразуем timestamp

    hours = params["group_hours"]

    # === Правильно: извлекаем час из даты и группируем ===
    df['hour'] = df['ts'].dt.hour
    df['group_hours'] = (df['hour'] // hours) * hours

    # Считаем количество в каждой группе
    counts = (
        df['group_hours']
        .value_counts()
        .reindex(range(0, 24, hours), fill_value=0)  # заполняем пустые интервалы нулями
        .sort_index()
        .reset_index()
    )
    counts.columns = ['group_hours', 'count']
    counts['label'] = counts['group_hours'].apply(lambda x: f"{x:02d}:00 – {x + hours:02d}:00")

    # Если интервал 24 часа — сделаем подпись "Весь день"
    if hours == 24:
        counts['label'] = "00:00 – 23:59 (весь день)"

    # Plotly гистограмма
    fig = px.bar(
        counts,
        x='label',
        y='count',
        title=f"Вызовы по времени суток (группировка каждые {hours} ч)",
        text='count',
        color_discrete_sequence=['#636EFA']
    )
    fig.update_layout(xaxis_title="Время суток", yaxis_title="Количество вызовов")
    fig.update_traces(textposition='outside')

    st.plotly_chart(fig, use_container_width=True)

    # Дополнительно: простой st.bar_chart (если хочешь)
    chart_data = pd.DataFrame({
        'Вызовы': counts['count']
    }, index=counts['label'])

    # st.bar_chart(chart_data, use_container_width=True, height=400)

    # Подпись
    event_title = "Все типы" if not params.get('event_type') else f"Тип: `{params['event_type']}`"
    period = f"{params['start_datetime'].strftime('%d.%m.%Y')} — {params['end_datetime'].strftime('%d.%m.%Y')}"
    st.caption(f"Группировка: каждые **{hours} ч** • {event_title} • Период: {period}")

# КРУГОВАЯ ДИАГРАММА по типам
def pie_chart_by_count(log_data):
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
        return


# КРУГОВАЯ ДИАГРАММА: по суммарному времени выполнения
def pie_chart_by_duration(log_data):
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
        return


# ТЕПЛОВАЯ КАРТА: активность по часам и дням недели
def heatmap_by_weekday_hour(log_data, params):
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
        return


def show_logs_table(log_data):
    st.subheader("Логи из БД")
    if not log_data.empty:
        st.write(f"**Найдено записей: {len(log_data)}**")
        st.dataframe(log_data.style.format({
            'timestamp': lambda x: pd.to_datetime(x).strftime('%Y-%m-%d %H:%M:%S') if pd.notna(x) else "—",
            'duration': lambda x: f"{x:.3f}" if pd.notna(x) else "—"
        }))
    else:
        st.info("Нет данных.")


def show_stats(log_data):
    if log_data.empty:
        return
    st.subheader("Статистика")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Всего событий", len(log_data))
    col2.metric("Уникальных типов", log_data['event_type'].nunique())
    durations = log_data['duration'].dropna()
    if len(durations) > 0:
        col3.metric("Средняя длительность", f"{durations.mean():.3f} сек")
        col4.metric("Медиана", f"{durations.median():.3f} сек")
