import random

class SellerAgent:
    """
    A simple Seller Agent for testing Buyer strategies.
    - Starts with a high ask (anchor).
    - Gradually lowers the price across rounds.
    - Accepts if buyer's offer is close enough to minimum acceptable.
    """

    def __init__(self, min_price=60, max_price=100):
        self.min_price = min_price
        self.max_price = max_price
        self.current_offer = max_price

    def respond(self, buyer_offer, round_number, max_rounds=10):
        """
        Decide whether to accept, reject, or counter a buyer offer.
        """
        # If buyer's offer is at or above min_price → accept
        if buyer_offer >= self.min_price:
            return "accept", buyer_offer

        # If last round → accept best offer within reason
        if round_number == max_rounds:
            if buyer_offer >= self.min_price * 0.9:
                return "accept", buyer_offer
            else:
                return "reject", None

        # Otherwise, counter-offer by conceding a bit
        concession = (self.current_offer - self.min_price) / (max_rounds - round_number + 1)
        self.current_offer = max(self.min_price, self.current_offer - concession)

        return "counter", int(self.current_offer)
