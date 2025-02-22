from amadeus import Client, ResponseError

class FlightSearcher:
    def __init__(self, client_id, client_secret):
        self.amadeus = Client(
            client_id=client_id,
            client_secret=client_secret
        )

    def search_flights(self, origin, destination, departure_date, adults):
        try:
            response = self.amadeus.shopping.flight_offers_search.get(
                originLocationCode=origin,
                destinationLocationCode=destination,
                departureDate=departure_date,
                adults=adults
            )
            return response.data
        except ResponseError as error:
            print(error)
            return None

    def print_flight_info(self, flights):
        if flights:
            for flight in flights:
                print(f"航班号: {flight['id']}")
                print(f"价格: {flight['price']['total']} {flight['price']['currency']}")
                for segment in flight['itineraries'][0]['segments']:
                    print(f"出发机场: {segment['departure']['iataCode']}")
                    print(f"到达机场: {segment['arrival']['iataCode']}")
                    print(f"出发时间: {segment['departure']['at']}")
                    print(f"到达时间: {segment['arrival']['at']}")
                print('---')

# Example usage:
if __name__ == "__main__":
    searcher = FlightSearcher(client_id='rXbr6ZWtqNPddA2oGwXQIHYAdMtABAs6', client_secret='DMczAEMDZPpjlCqq')
    flights = searcher.search_flights(origin='PVG', destination='HND', departure_date='2024-12-15', adults=1)
    searcher.print_flight_info(flights)