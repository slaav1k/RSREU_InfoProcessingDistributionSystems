from database import check_db, get_event_types, load_logs
from ui import user_input_features, show_filters
from visualizations import *

st.set_page_config(
    page_title="Аналитика XML-RPC, @slaav1k",
    page_icon="bar_chart"
)

try:
    check_db()
except FileNotFoundError as e:
    st.error(e)
    st.stop()

st.write("# Аналитика работы веб-сервиса")
st.sidebar.header('Ввод данных')

event_types = get_event_types()
params = user_input_features(event_types)
log_data = load_logs(params)

show_logs_table(log_data)
st.markdown("---")
show_stats(log_data)
st.markdown("---")
show_filters(params)
st.markdown("---")
bar_chart_by_type(log_data)
st.markdown("---")
bar_chart_by_time(log_data, params)
st.markdown("---")
pie_chart_by_count(log_data)
st.markdown("---")
pie_chart_by_duration(log_data)
st.markdown("---")
heatmap_by_weekday_hour(log_data, params)
