imu_conv
生のIMUデータをlog_mixer, Inertial Explorerで読み込めるフォーマットに変換する.

はじめに：
以下のライブラリをダウンロードしておく.
numpy, pandas, tqdm
　ダウンロード例：$ pip install numpy
                  $ conda install numpy

使い方:
imu_conv.py (生のimuデータを含むcsvファイル） （任意の出力ファイル名, csv or dat）
出力ファイル名をcsvにすると, log_mixer用のファイル, datにするとInertial Explorer用のファイルになる. 

使用例：
$ python imu_conv.py sample_input.csv sample_output.csv
$ python imu_conv.py sample_input.csv sample_output.dat

注意：
出力ファイル名に拡張子以外でドットを用いないこと.