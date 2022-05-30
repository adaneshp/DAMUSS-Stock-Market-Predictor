package main

import (
	"CloudNative/FinalProject/stockapi"
	"context"
	"log"
	"net"

	"google.golang.org/grpc"
)

const (
	port = ":50002"
)

type server struct {
	stockapi.UnimplementedStockPredictionServer
}

//a simple getstock grpc server
func (s *server) GetStock(ctx context.Context, in *stockapi.APIRequest) (*stockapi.APIReturn, error) {
	name := in.GetName()
	date := in.GetDate()
	log.Printf("Received{Name: %s, Date: %s", name, date)
	reply := &stockapi.APIReturn{}
	var data []float32
	for i := 0; i < 50; i++ {
		data = append(data, float32(i))
	}
	reply.Data = data
	reply.Prediction = 20
	reply.Recomandation = "buy"
	reply.Status = ""
	return reply, nil
}

func main() {
	lis, err := net.Listen("tcp", port)
	if err != nil {
		log.Fatalf("fialt to listen: %v", err)
	}
	s := grpc.NewServer()
	stockapi.RegisterStockPredictionServer(s, &server{})
	if err := s.Serve(lis); err != nil {
		log.Fatalf("failed to serve: %v", err)
	}
}
