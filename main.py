from AIAgent import BuyerAgent
from SellerAgent import SellerAgent

def run_negotiation():
    print("Negotiation Session Started")

    buyer = BuyerAgent(budget=85, target_price=70)
    seller = SellerAgent(min_price=70, max_price=100)

    max_rounds = 10
    for round_number in range(1, max_rounds + 1):
        print(f"\nRound {round_number}")

        # Buyer makes an offer
        buyer_offer = buyer.make_offer(round_number)
        print(f"Buyer offers: {buyer_offer}")

        # Seller responds
        response, value = seller.respond(buyer_offer, round_number, max_rounds)

        if response == "accept":
            print(f"Seller accepts at {value}")
            print(f"DEAL CLOSED: Buyer saved {seller.max_price - value}")
            return
        elif response == "reject":
            print("Seller rejects. No deal.")
            return
        elif response == "counter":
            print(f"Seller counters with: {value}")
            buyer.receive_counter(value)

    print("Negotiation ended. No agreement reached.")

if __name__ == "__main__":
    run_negotiation()
