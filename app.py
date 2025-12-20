import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from current_weather import get_weather_sequential
from analysis import *

st.title("🌤 Анализ погодных данных")
st.header("1. Загрузка исторических данных")

uploaded_file = st.file_uploader("Загрузите файл с историческими данными (CSV)",
                                 type=["csv"])
if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    st.success("Файл успешно загружен")
    st.dataframe(df.head())

st.header("2. Выбор города")

cities = ["New York", "London", "Paris", "Tokyo", "Moscow", "Sydney",
          "Berlin", "Beijing", "Rio de Janeiro", "Dubai", "Los Angeles",
          "Singapore", "Mumbai", "Cairo", "Mexico City"]

city = st.selectbox("Выберите город:", cities)
st.write("Выбранный город:", city)

st.header("3. API-ключ OpenWeatherMap")

with st.form("api_key_form"):
    api_key = st.text_input("Введите API-ключ OpenWeatherMap",
                            type="password")
    submit_button = st.form_submit_button("Начать анализ")

if submit_button:
    if api_key:
        res = get_weather_sequential(city, api_key)
        if type(res) != str:
            try:
                result_df, t_seq, t_par = analyze_city_temperature(df=df,
                                                                   city_name=city)

                st.write(f"Последовательный анализ: {t_seq:.3f} сек")
                st.write(f"Параллельный анализ:     {t_par:.3f} сек")

                # вывод статистики, графиков и проверки на аномальность
                graphics(result_df, res[1])
                st.success(res[0])
                st.write('Время запроса:', round(res[2], 5), 'сек')

                st.write(f"Аномалии")
                st.dataframe(result_df[result_df["is_anomaly"]])
            except NameError:
                st.error("Загрузите файл с историческими данными")

        else:
            st.error(res)
    else:
        st.error("API-ключ не может быть пустым")
