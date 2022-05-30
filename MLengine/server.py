from concurrent import futures
import grpc
import stockapi_pb2
import stockapi_pb2_grpc
import time
import sys 
#!{sys.executable} -m pip install yfinance
import yfinance as yf
import pandas as pd
import numpy as np
#!{sys.executable} -m pip install ta
from ta import add_all_ta_features
#!{sys.executable} -m pip install fastai
import fastai.tabular
#!{sys.executable} -m pip install sklearn
from sklearn.metrics import mean_squared_error
from sklearn.neural_network import MLPRegressor 
from sklearn.preprocessing import StandardScaler
import datetime

class Listener(stockapi_pb2_grpc.StockPredictionServicer):
    def __init__(self, *args, **kwargs):
        pass
    
    def getStock(self, request, context):
        # The tickerSymbol should be based on clients request 
        tickerSymbol = request.name
        df, dummy = prepare_data(tickerSymbol, '2015-04-01', '2020-01-01')
        df_lag, shift = CreateLags(df,1)
        df_lag = CorrectColumnTypes(df_lag)
        x_train, y_train, x_test, y_test, train, test = SplitData(df, 1, shift)
        # Provided by the server
        date_requested = request.date
        date_time_obj = datetime.datetime.strptime(date_requested, '%Y-%m-%d')
        day = datetime.timedelta(50)
        start_day = date_time_obj - day
        end_day = date_time_obj +  datetime.timedelta(1)

        date_requested_df, dates = prepare_data(tickerSymbol, start_day.strftime('%Y-%m-%d'), end_day.strftime('%Y-%m-%d'))
        scaler = StandardScaler()
        scaler.fit(x_train)
        x_train_scaled = scaler.transform(x_train)

        MLP = MLPRegressor(random_state=1, max_iter=1000, hidden_layer_sizes = (100,), activation = 'identity',learning_rate = 'adaptive').fit(x_train_scaled, y_train)


        df_lag, shift = CreateLags(date_requested_df,1)
        df_lag = CorrectColumnTypes(df_lag)
        x_req, y_req, _, __, ___, ____ = SplitData(date_requested_df, 1, shift)
        date_requested_scaled = scaler.transform(x_req)
        # Get the desired date from server, get the features for it from API and scale it. Then feed to network for prediction.
        MLP_pred = MLP.predict(date_requested_scaled[len(date_requested_scaled)-1].reshape(1, -1))
        
        today_price = date_requested_df.iloc[len(date_requested_df)-2]['Close']
        if today_price < MLP_pred[0]:
            response = "Buy it! It is gonna rise."
        else:
            response = "Sell it! It is gonna fall."

        from fastai.tabular import data
        data_to_sent_data = []
        data_to_sent_date = []
        for i in range (len(date_requested_df)):
            data_to_sent_date.append(dates[i].strftime('%Y-%m-%d'))
            data_to_sent_data.append(date_requested_df.iloc[i]["Close"])


        result = {'date': data_to_sent_date,'data': data_to_sent_data, 'prediction': MLP_pred[0], 'recomandation': response, 'status': ""}
        return stockapi_pb2.APIReturn(**result)

def prepare_data (tickerSymbol, startDate, endDate):
  tickerData = yf.Ticker(tickerSymbol)
  df = tickerData.history(start = startDate, end = endDate)
  date_change = '%Y-%m-%d'
  df['Date'] = df.index
  df['Date'] = pd.to_datetime(df['Date'], format = date_change)
  Dates = df['Date']
  df = add_all_ta_features(df, "Open", "High", "Low", "Close", "Volume", fillna=True) 
  fastai.tabular.add_datepart(df,'Date', drop = 'True')
  df['Date'] = pd.to_datetime(df.index.values, format = date_change)
  fastai.tabular.add_cyclic_datepart(df, 'Date', drop = 'True')
  return df, Dates

def CorrectColumnTypes(df):
  # Input: dataframe 
  # ouptut: dataframe (with column types changed)

  # Numbers
  for col in df.columns[1:80]:
      df[col] = df[col].astype('float')

  for col in df.columns[-10:]:
      df[col] = df[col].astype('float')

  # Categories 
  for col in df.columns[80:-10]:
      df[col] = df[col].astype('category')

  return df

def CreateLags(df,lag_size):
  # inputs: dataframe , size of the lag (int)
  # ouptut: dataframe ( with extra lag column), shift size (int)

  # add lag
  shiftdays = lag_size
  shift = -shiftdays
  df['Close_lag'] = df['Close'].shift(shift)
  return df, shift

def SplitData(df, train_pct, shift):
  # inputs: dataframe , training_pct (float between 0 and 1), size of the lag (int)
  # ouptut: x train dataframe, y train data frame, x test dataframe, y test dataframe, train data frame, test dataframe

  train_pt = int(len(df)*train_pct)
  
  train = df.iloc[:train_pt,:]
  test = df.iloc[train_pt:,:]
  
  x_train = train.iloc[:shift,1:-1]
  y_train = train['Close_lag'][:shift]
  x_test = test.iloc[:shift,1:-1]
  y_test = test['Close'][:shift]

  return x_train, y_train, x_test, y_test, train, test

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    stockapi_pb2_grpc.add_StockPredictionServicer_to_server(Listener(), server)
    server.add_insecure_port('[::]:50002')
    server.start()
    server.wait_for_termination()

if __name__ == '__main__':
    serve()
        