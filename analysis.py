##
import streamlit as st
from concurrent.futures import ThreadPoolExecutor
import pandas as pd
import time
import matplotlib.pyplot as plt
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go


def process_season(season_df: pd.DataFrame) -> pd.DataFrame:
    stats = {
        "mean_temp": season_df["temperature"].mean(),
        "std_temp": season_df["temperature"].std()
    }

    season_df = season_df.copy()
    season_df["mean_temp"] = stats["mean_temp"]
    season_df["std_temp"] = stats["std_temp"]

    season_df["is_anomaly"] = (
            (season_df["temperature"] > stats["mean_temp"] + 2 * stats["std_temp"]) |
            (season_df["temperature"] < stats["mean_temp"] - 2 * stats["std_temp"])
    )

    return season_df


def analyze_city_temperature(
        df: pd.DataFrame,
        city_name: str,
        window: int = 30
) -> tuple[pd.DataFrame, float, float]:
    """
    Анализ температур для одного города:
    - скользящее среднее
    - среднее и std по сезонам
    - поиск аномалий (mean ± 2σ)
    - сравнение скорости: последовательно vs параллельно

    Возвращает:
    - итоговый DataFrame
    - время последовательного выполнения
    - время параллельного выполнения
    """

    # ---------- загрузка ----------
    df["timestamp"] = pd.to_datetime(df["timestamp"])

    # фильтрация по городу
    df = df[df["city"] == city_name].copy()
    df = df.sort_values("timestamp")

    # ---------- 1. последовательный анализ ----------
    start = time.time()

    # скользящее среднее
    df["temp_ma_30"] = (
        df["temperature"]
        .rolling(window=window, min_periods=1)
        .mean()
    )

    # статистика по сезонам
    season_stats = (
        df.groupby("season")["temperature"]
        .agg(mean_temp="mean", std_temp="std")
        .reset_index()
    )

    df_seq = df.merge(season_stats, on="season", how="left")

    # аномалии
    df_seq["is_anomaly"] = (
            (df_seq["temperature"] > df_seq["mean_temp"] + 2 * df_seq["std_temp"]) |
            (df_seq["temperature"] < df_seq["mean_temp"] - 2 * df_seq["std_temp"])
    )
    seq_time = time.time() - start

    # параллельный анализ (по сезонам)
    start = time.time()
    season_groups = [group for _, group in df.groupby("season")]

    with ThreadPoolExecutor() as executor:
        df_par = pd.concat(executor.map(process_season, season_groups))

    # скользящее среднее
    df_par = df_par.sort_values("timestamp")
    df_par["temp_ma_30"] = (df_par["temperature"]
                            .rolling(window=window, min_periods=1)
                            .mean())
    par_time = time.time() - start

    return df_par, seq_time, par_time


# При использовании ThreadPoolExecutor ускорения не наблюдается,
# поскольку вычисления являются CPU-bound и выполняются в среде CPython
# с глобальной блокировкой интерпретатора (GIL).
# Кроме того, объём вычислений мал, а библиотека pandas уже оптимизирована
# на уровне C, что делает последовательный анализ более эффективным.


def get_season(dt):
    """Функция для определения текущего сезона
    для проверки на аномалии"""
    month = dt.month
    if month in (12, 1, 2):
        return "winter"
    elif month in (3, 4, 5):
        return "spring"
    elif month in (6, 7, 8):
        return "summer"
    else:
        return "autumn"


def graphics(result_df, current_data):
    """ Функция для вывода описательной статистики
    и визуализаций по обработанным данным
    :param result_df: pd.DataFrame с результатами анализа
    :param current_data: текущие данные
    """

    st.subheader("Описательная статистика")
    stats = result_df["temperature"].describe()
    st.dataframe(stats)

    st.subheader("Временной ряд температур, °C")

    fig = go.Figure()

    # линия температуры
    fig.add_trace(go.Scatter(
        x=result_df["timestamp"],
        y=result_df["temperature"],
        mode="lines",
        name="Температура",
        line=dict(color="#39addc"),
        hovertemplate="Дата: %{x}<br>Температура: %{y:.2f}°C"
    ))

    # точки аномалий
    anomalies = result_df[result_df["is_anomaly"]]
    fig.add_trace(go.Scatter(
        x=anomalies["timestamp"],
        y=anomalies["temperature"],
        mode="markers",
        name="Аномалии",
        marker=dict(color="#a70f1f", size=8),
        hovertemplate="Дата: %{x}<br>Аномалия: %{y:.2f}°C"
    ))

    fig.update_layout(
        xaxis_title="Дата",
        yaxis_title="Температура",
        template="plotly_white",
        legend=dict(x=0, y=1),
        hovermode="x unified"
    )

    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Сезонные профили, °C")

    season_stats = (
        result_df
        .groupby("season")
        .agg(
            mean_temp=("temperature", "mean"),
            std_temp=("temperature", "std")
        )
        .reset_index()
    )

    fig2 = go.Figure()

    fig2.add_trace(go.Bar(
        x=season_stats["season"],
        y=season_stats["mean_temp"],
        name="Средняя температура",
        error_y=dict(
            type='data',
            array=season_stats["std_temp"],
            visible=True, color='#a3192c'
        ),
        marker_color="#39addc",
        hovertemplate="Сезон: %{x}<br>Среднее: %{y:.2f}°C<br>σ: %{error_y.array:.2f}"
    ))

    fig2.update_layout(
        xaxis_title="Сезон",
        yaxis_title="Температура",
        template="plotly_white",
        showlegend=False
    )

    st.plotly_chart(fig2, use_container_width=True)

    # Проверка текущей температуры на аномальность
    current_season = get_season(datetime.now())
    season_df = result_df[result_df["season"] == current_season]

    mean_temp = season_df["temperature"].mean()
    std_temp = season_df["temperature"].std()

    lower = mean_temp - 2 * std_temp
    upper = mean_temp + 2 * std_temp

    is_normal = lower <= current_data['main']['temp'] <= upper
    if is_normal:
        st.success(f'Температура в пределах нормы для сезона {current_season}')
    else:
        st.error(f'Аномальная температура для сезона {current_season}')
    st.write(f'Максимум нормы {round(upper, 3)}°C')
    st.write(f'Минимум нормы {round(lower, 3)}°C')
