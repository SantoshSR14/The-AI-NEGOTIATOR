#------------------------------------
#Sairam Hackathon 2025-AI ML 
#Buyer Agent-Calm & Smart Buyer Agent
#------------------------------------

import random
import ollama  

class BestBuyer:
    def _init_(self, max_rounds=5, ollama_model="gemma:2b"):
        self.max_rounds = max_rounds
        self.use_ollama = True
        self.ollama_model = ollama_model

    def _ask_ollama(self, prompt: str) -> str:
        resp = ollama.chat(model=self.ollama_model, messages=[{"role":"user","content":prompt}])
        if isinstance(resp, dict):
            return resp.get("message", {}).get("content", "") or ""
        return str(resp)

    def negotiate(self, product_name, base_price, quality, quantity, origin, seller_character):
        discounts = {"Export": 0.70, "A": 0.65, "B": 0.60}
        markups = {"Export": 1.40, "A": 1.25, "B": 1.15}

        buyer_offer = base_price * discounts.get(quality, 0.65)
        seller_price = base_price * markups.get(quality, 1.20)

        min_expected = base_price * (0.6 if quantity > 50 else 0.75)
        quality_markup = {"Export": 0.40, "A": 0.25, "B": 0.10}
        q_markup = quality_markup.get(quality, 0.20)
        origin_markup = 0.10 if origin in ["Ratnagiri", "Devgad"] else 0.0
        max_acceptable = base_price * (1 + q_markup + origin_markup)

        ACCEPT_THRESHOLD = 1.5  # quick accept if seller price within +3 of buyer_offer

        print(f"\nNegotiating for {product_name} ({quality}) from {origin}")
        print(f"Quantity: {quantity} | Base Market Price: ₹{base_price}")
        print(f"Seller Character: {seller_character}")
        print(f"Price Bounds: min ₹{min_expected:.2f} - max ₹{max_acceptable:.2f}")
        print(f"Initial Buyer Offer: ₹{buyer_offer:.2f} | Initial Seller Ask: ₹{seller_price:.2f}")
        print(f"Max Rounds: {self.max_rounds}\n")

        for round_num in range(1, self.max_rounds + 1):
            print(f"--- Round {round_num} ---")
            print(f"Seller asks: ₹{seller_price:.2f}")
            print(f"Buyer offers: ₹{buyer_offer:.2f}")

            # Quick accept
            if seller_price <= buyer_offer + ACCEPT_THRESHOLD:
                print(f"\nQuick deal! Seller's price ₹{seller_price:.2f} is within +₹{ACCEPT_THRESHOLD:.2f} of buyer's offer ₹{buyer_offer:.2f}")
                return seller_price

            # Ollama narration
            prompt = (
                f"Round {round_num} negotiation short exchange.\n"
                f"Product: {product_name}, Quality: {quality}, Origin: {origin}, Quantity: {quantity}\n"
                f"Seller character: {seller_character}\n"
                f"Seller asking: ₹{seller_price:.2f}\n"
                f"Buyer offering: ₹{buyer_offer:.2f}\n"
                f"Write a 1-2 line seller then buyer line (natural language)."
            )
            ollama_text = self._ask_ollama(prompt)
            if ollama_text:
                print("Ollama:", ollama_text)

            # Seller concession
            remaining_gap = max(seller_price - buyer_offer, 0.0)
            if seller_character.lower().startswith("jov"):
                concession_factor = 0.25 + (round_num / self.max_rounds) * 0.15
            elif seller_character.lower().startswith("ser"):
                concession_factor = 0.15 + (round_num / self.max_rounds) * 0.10
            else:
                concession_factor = 0.08 + (round_num / self.max_rounds) * 0.05

            reduction = remaining_gap * concession_factor
            seller_price = max(seller_price - reduction, min_expected)

            # Buyer counter-offer
            urgency = round_num / self.max_rounds
            gap_after = max(seller_price - buyer_offer, 0.0)
            if seller_character.lower().startswith("jov"):
                increment = gap_after * (0.4 + 0.2 * urgency)
            elif seller_character.lower().startswith("ser"):
                increment = gap_after * (0.25 + 0.15 * urgency)
            else:
                increment = gap_after * (0.15 + 0.10 * urgency)

            buyer_offer = min(buyer_offer + increment, max_acceptable)

            print(f" -> Seller reduces to: ₹{seller_price:.2f}")
            print(f" -> Buyer moves to:  ₹{buyer_offer:.2f}\n")

        if seller_price <= max_acceptable:
            print(f"Buyer accepts seller's final price ₹{seller_price:.2f} after {self.max_rounds} rounds.")
            return seller_price
        else:
            print(f"No deal. Seller's final ₹{seller_price:.2f} > Buyer's max acceptable ₹{max_acceptable:.2f}")
            return None


if _name_ == "_main_":
    product_name = input("Enter product name: ")
    category = input("Enter product category (optional): ")
    quantity = int(input("Enter quantity: "))
    quality = input("Enter quality grade (Export/A/B): ")
    origin = input("Enter origin: ")
    base_price = float(input("Enter base market price (₹): "))
    seller_character = input("Enter seller character (Jovial/Serious/Firm): ")
    max_rounds = int(input("Enter max no. of negotiation rounds: "))

    buyer = BestBuyer(max_rounds=max_rounds, ollama_model="gemma:2b")
    buyer.negotiate(product_name, base_price, quality, quantity, origin, seller_character)
