import math
import struct
import sys

import numpy as np
import pandas as pd
from tqdm import tqdm

import gpstime


def add_wtime(df):
    """
    週番号と秒を追加する
    """
    week_l, wsec_l, wtime_l, sec_l = [], [], [], []
    print('時刻を週番号と秒に変換中')
    for i in tqdm(range(df.shape[0])):

        date_s = df['StatusTime/Date'][i]
        date_l = date_s.split('/')
        time_s = df['StatusTime/Time'][i]
        time_l = time_s.split(':')
        milli_sec = int(df['StatusTime/MilliSeconds'][i])

        year    = int(date_l[0])
        month   = int(date_l[1])
        date    = int(date_l[2])
        target = gpstime.datetime.datetime(year, month, date, 0, 0, 0)
        strtm = target.timetuple()
        date_sec = gpstime.mktime2(strtm)

        #XX:XX:XXの秒数を計算する
        hour    = int(time_l[0])
        minute  = int(time_l[1])
        sec     = int(time_l[2])
        time_sec = milli_sec*10**(-3) + sec + minute*60 + hour*3600

        #閏秒の補正
        leap_sec = 18

        #wtimeを計算する
        t = date_sec + time_sec + leap_sec
        week = int((t-gpstime.TIME_T_ORIGIN)/gpstime.SECONDS_WEEK)
        wsec = round((t-gpstime.TIME_T_ORIGIN)%gpstime.SECONDS_WEEK, 5)
        week_l.append(week)
        wsec_l.append(wsec)
        wtime_l.append(str(week)+':'+str(wsec))
        sec_l.append(week*gpstime.SECONDS_WEEK + wsec)
    df['week']  = week_l
    df['wsec']  = wsec_l
    df['wtime'] = wtime_l
    df['sec']   = sec_l
    return df


args = sys.argv
#入力ファイル読み込み
df = pd.read_csv(args[1])
#出力モードを選択, 'dat' or 'csv'
extend_idx = args[2].find('.')
extend = args[2][extend_idx+1:]
mode_out = extend
if not (mode_out == 'csv' or mode_out == 'dat'):
    print('出力ファイル名に正しい拡張子を入力してください')

mode_drone = False
#ドローンデータから取得したIMUデータを読み込む際のカラム名の統合
if 'AircraftTime.Year' in df.columns:
    mode_drone = True
    df.rename(columns={'Sensor_MG200.PRate': 'Inertial/P [rad/s]'}, inplace=True)
    df.rename(columns={'Sensor_MG200.QRate': 'Inertial/Q [rad/s]'}, inplace=True)
    df.rename(columns={'Sensor_MG200.RRate': 'Inertial/R [rad/s]'}, inplace=True)

    df.rename(columns={'Sensor_MG200.XAcceleration': 'Inertial/X [m/s2]'}, inplace=True)
    df.rename(columns={'Sensor_MG200.YAcceleration': 'Inertial/Y [m/s2]'}, inplace=True)
    df.rename(columns={'Sensor_MG200.ZAcceleration': 'Inertial/Z [m/s2]'}, inplace=True)
    df['StatusTime/Date'] = df['AircraftTime.Year'].astype('str').str.cat([df['AircraftTime.Month'].astype('str'), df['AircraftTime.Day'].astype('str')], sep='/')
    df['StatusTime/Time'] = df['AircraftTime.Hour'].astype('str').str.cat([df['AircraftTime.Minute'].astype('str'), df['AircraftTime.Second'].astype('str')], sep=':')
    df.rename(columns={'AircraftTime.Millisecond': 'StatusTime/MilliSeconds'}, inplace=True)
    #時刻0の時の行をスキップ
    for i in range(df.shape[0]):
        if not df['AircraftTime.Year'].iloc[i] == 0:
            start_idx = i
            break
    df = df.iloc[start_idx:, :].copy()
    df.reset_index(drop=True, inplace=True)


#log_mixer用データ作成
#週番号と秒の追加
df = add_wtime(df)

if mode_out == 'csv':
    #角速度をラジアンから度に変更
    if not mode_drone:
        s = df[['Inertial/P [rad/s]', 'Inertial/Q [rad/s]', 'Inertial/R [rad/s]']]
        anglar_sp_df = s.applymap(math.degrees)
        anglar_sp_df.rename(columns={'Inertial/P [rad/s]': 'Inertial/P [deg/s]', 'Inertial/Q [rad/s]': 'Inertial/Q [deg/s]', 'Inertial/R [rad/s]': 'Inertial/R [deg/s]'}, inplace=True)
        df_new = pd.concat([df, anglar_sp_df], axis=1)

    else:
        df_new = df.copy()

    df_out = df_new[['sec', 'Inertial/X [m/s2]', 'Inertial/Y [m/s2]', 'Inertial/Z [m/s2]', 'Inertial/P [deg/s]', 'Inertial/Q [deg/s]', 'Inertial/R [deg/s]']].copy()

    #データ出力
    df_out.to_csv(args[2], index=False, header=False)

elif mode_out == 'dat':
    #バイナリデータ出力
    #角速度をラジアンから度に変更
    s = df[['Inertial/P [rad/s]', 'Inertial/Q [rad/s]', 'Inertial/R [rad/s]']]
    anglar_sp_df = s.applymap(math.degrees)
    anglar_sp_df.rename(columns={'Inertial/P [rad/s]': 'Inertial/P [deg/s]', 'Inertial/Q [rad/s]': 'Inertial/Q [deg/s]', 'Inertial/R [rad/s]': 'Inertial/R [deg/s]'}, inplace=True)
    df_new = pd.concat([df, anglar_sp_df], axis=1)

    df_out = df_new[['wsec', 'Inertial/X [m/s2]', 'Inertial/Y [m/s2]', 'Inertial/Z [m/s2]', 'Inertial/P [deg/s]', 'Inertial/Q [deg/s]', 'Inertial/R [deg/s]']].copy()

    with open("imu_data.dat", "wb") as fout:
        print('データをバイナリに変換中')
        for i in tqdm(range(df_out.shape[0])):
            format = "diiiiii"

            b = struct.pack(format, df_out['wsec'].iloc[i], int(df_out['Inertial/P [deg/s]'].iloc[i]*10**6), int(df_out['Inertial/Q [deg/s]'].iloc[i]*10**6),                            int(df_out['Inertial/R [deg/s]'].iloc[i]*10**6), int(df_out['Inertial/X [m/s2]'].iloc[i]*10**6), int(df_out['Inertial/Y [m/s2]'].iloc[i]*10**6), int(df_out['Inertial/Z [m/s2]'].iloc[i]*10**6))

            fout.write(b)

else:
    print('出力ファイルに適切な拡張子を記入してください')
