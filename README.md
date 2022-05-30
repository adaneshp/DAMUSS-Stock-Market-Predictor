# DAMUSS: An Intelligent Stock Market Predictor

- This code was developed in April, 2022.

This system is designed to predict the stock market using Deep Learning. For reading more about the intentions, goals, and the design of this system please go to the following link: 

https://medium.com/p/2bef82438f75#c7ab-f2a607021aa9

------

It uses Python 3.6 for implementing the AI part. GO language is used for developing the client server design. Finally HTML and CSS are for a very simplistic design of a front end.

Based on the stock that you search (you have to use the ticker symbol), the program will acquire the information about that stock from the Yahoo Finance API, starts the learning process which is optimized and quick. Based on the trained model, it will make a prediction about what is going to happen with that market in the next day.

## Known Issue

Please keep in mind that in order for the algorithm to work, it needs 5 years of data about the specific ticker symbol that you have searched. If a stock is younger than 5 years, it will not work.
