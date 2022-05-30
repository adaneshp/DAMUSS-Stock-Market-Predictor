package main

import (
	"CloudNative/FinalProject/stockapi"
	"context"
	"fmt"
	"html/template"
	"log"
	"net/http"
	"time"

	"github.com/go-echarts/go-echarts/v2/charts"
	"github.com/go-echarts/go-echarts/v2/opts"
	"github.com/go-echarts/go-echarts/v2/types"
	"google.golang.org/grpc"
)

const (
	serverPort   = "localhost:50001"
	MLenginePort = ":50002"
)

func main() {
	server := http.Server{
		Addr: serverPort,
	}
	http.HandleFunc("/", info)
	http.HandleFunc("/stock", request)
	http.Handle("/picture/", http.StripPrefix("/picture", http.FileServer(http.Dir("picture"))))
	http.Handle("/css/", http.StripPrefix("/css", http.FileServer(http.Dir("css"))))
	//set port to localhost:50001
	log.Print("Setup Server......")
	log.Fatal(server.ListenAndServe())
}

// generate data for line chart
func generateLineItems(v []float32) []opts.LineData {
	items := make([]opts.LineData, 0)
	for i := range v {
		items = append(items, opts.LineData{Value: v[i]})
	}
	return items
}

// guide reference page
func info(w http.ResponseWriter, req *http.Request) {
	tmpl := template.Must(template.ParseFiles("main.html"))
	tmpl.ExecuteTemplate(w, "main.html", nil)
}

func request(w http.ResponseWriter, req *http.Request) {
	// get name from url
	stockName := req.FormValue("stockName")
	log.Println("receive request from client ", stockName)

	// Set up a connection to ML engine server.
	log.Println("make connection to ML Engine...")
	conn, err := grpc.Dial(MLenginePort, grpc.WithInsecure(), grpc.WithBlock())
	if err != nil {
		log.Fatalf("Fail to connect to ML Engine: ", err)
	}
	defer conn.Close()
	c := stockapi.NewStockPredictionClient(conn)
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()

	// get current time
	currentTime := time.Now()
	date := fmt.Sprintf("%v-%v-%v", currentTime.Year(), int(currentTime.Month()), currentTime.Day())

	//send a request to ML engine
	log.Println("Send request from ML Engine .....")
	r, err := c.GetStock(ctx, &stockapi.APIRequest{Name: stockName, Date: date})
	if err != nil {
		log.Println(err)
		return
	}
	if r.Status != "" {
		fmt.Fprintln(w, r.Status)
		return
	}
	log.Println("Plot the chart and show the result....")

	// create a new line instance
	line := charts.NewLine()
	// set some global options like Title/Legend/ToolTip or anything else
	str := fmt.Sprintf("value of %s in last 50 days, Time: ", stockName) + fmt.Sprintf(currentTime.Format("01-02-2006 15:04:05 Mon"))
	line.SetGlobalOptions(
		charts.WithInitializationOpts(opts.Initialization{Theme: types.ThemeWesteros}),
		charts.WithTitleOpts(opts.Title{
			Title:    stockName,
			Subtitle: str,
		}))

	// Put data into instance
	line.SetXAxis(r.Date).
		AddSeries(stockName, generateLineItems(r.Data)).
		SetSeriesOptions(charts.WithLineChartOpts(opts.LineChart{Smooth: false}))
	line.Render(w)
	fmt.Fprintf(w, "Prediction of stock value: $%v, ", r.Prediction)
	fmt.Fprintf(w, "DAMUSS recommandation: %s", r.Recomandation)
	log.Println("request finished....")
}
