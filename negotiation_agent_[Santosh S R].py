#SAIRAM HACKATHON 2025 AI-ML
#---------------------------------
#Data driven strategic buyer agent
#---------------------------------


from dataclasses import dataclass
from typing import Dict, List, Any
import random

# ---------------------------
# DATA STRUCTURES
# ---------------------------
@dataclass
class Product:
    name: str
    category: str
    quantity: int
    quality_grade: str  # 'A', 'B', 'Export'
    origin: str
    base_market_price: int
    attributes: Dict[str, Any]

@dataclass
class NegotiationContext:
    product: Product
    your_budget: int
    current_round: int
    seller_offers: List[int]
    your_offers: List[int]
    messages: List[Dict[str, str]]
    seller_history: List[str]
    buyer_history: List[str]

# ---------------------------
# DIALOGUE GENERATOR
# ---------------------------
class DialogueGenerator:

    @staticmethod
    def pick_message(messages: List[str], history: List[str]) -> str:
        unused = [m for m in messages if m not in history]
        if not unused:
            history.clear()
            unused = messages.copy()
        msg = random.choice(unused)
        history.append(msg)
        return msg

    @staticmethod
    def seller_message(product: Product, offer: int, history: List[str]) -> str:
        if product.quality_grade == "Export":
            messages = [
                f"Premium {product.name} at ₹{offer}. These are Worth every rupee!",
                f"Let's seal these delicious mangoes at ₹{offer}.",
                f"Deal at ₹{offer}? These might get their own passport!",
                f"These are bloody sweet. Even LEO has ordered some at ₹{offer}. Will you? 😉",
                f"The taste is the key. Unlock your taste buds with this key. Offer at ₹{offer}.",
                f"King Virat Kohli is a regular customer of mine. He usually offers ₹{offer} and it is his fitness secret."
            ]
        elif product.quality_grade == "A":
            messages = [
                f"A-grade {product.name} at a reasonable ₹{offer}. Can't be over flexible",
                f"Prime quality, prime price: ₹{offer}. Let's fix it.",
                f"Win-win scenario for both of us at ₹{offer}, what do you say?",
                f"Both quality and quantity at reasonable price ₹{offer}."
            ]
        elif product.quality_grade == "B":
            messages = [
                f"B-grade {product.name} are highly worth of each penny you spend. Solid value at ₹{offer}.",
                f"₹{offer} is the maximum. Take it or leave it.",
                f"Best I can offer is ₹{offer}. Let's close this!",
                f"Let's settle at ₹{offer}, no nonsense.",
                f"Cheap and best at the price ₹{offer}, don't drag this and waste our time."
            ]
        else:
            messages = [f"My revised price is ₹{offer}."]
        return DialogueGenerator.pick_message(messages, history)

    @staticmethod
    def buyer_message(product: Product, offer: int, history: List[str]) -> str:
        if product.quality_grade == "Export":
            messages = [
                f"₹{offer}? Your humor is great, but my wallet disagrees!",
                f"Let's settle at ₹{offer}, fair but fun!",
                f"Data says ₹{offer} is fine. Deal?",
                f"Humor aside, let's fix the deal at ₹{offer}."
            ]
        elif product.quality_grade == "A":
            messages = [
                f"₹{offer} seems reasonable for A-grade. Can we close?",
                f"Respect quality, budget allows ₹{offer}. Let's settle.",
                f"A grade is good, ₹{offer} works for me.",
                f"For this quantity and quality, ₹{offer} is fair."
            ]
        elif product.quality_grade == "B":
            messages = [
                f"₹{offer} is my ceiling, final offer.",
                f"B-grade doesn't fetch premium. ₹{offer} final.",
                f"Don't jump the gun. Data-driven approach says ₹{offer} is fine.",
                f"You seem quite desperate. But I believe my approach and let's finish at ₹{offer}."
            ]
        else:
            messages = [f"My counter is ₹{offer}."]
        return DialogueGenerator.pick_message(messages, history)

# ---------------------------
# SELLER AGENT
# ---------------------------
class SellerAgent:
    def __init__(self, product: Product):
        self.product = product
        self.min_price = product.base_market_price
        self.current_price = self.initial_offer()

    def initial_offer(self) -> int:
        grade_markup = {"Export": 0.40, "A": 0.30, "B": 0.15}
        markup = grade_markup.get(self.product.quality_grade, 0.20)
        return int(self.min_price * (1 + markup))

    def respond(self, buyer_offer: int, round_num: int, max_rounds: int) -> int:
        remaining_gap = self.current_price - buyer_offer
        concession_factor = 0.1 + (round_num / max_rounds) * 0.25
        reduction = int(remaining_gap * concession_factor)
        new_price = self.current_price - reduction
        self.current_price = max(new_price, self.min_price)
        return self.current_price

# ---------------------------
# BUYER AGENT
# ---------------------------
class BuyerAgent:
    def __init__(self, budget: int):
        self.budget = budget

    def opening_offer(self, product: Product) -> int:
        grade_discount = {"Export": 0.75, "A": 0.70, "B": 0.65}
        discount = grade_discount.get(product.quality_grade, 0.70)
        return min(int(product.base_market_price * discount), self.budget)

    def counter_offer(self, product: Product, seller_price: int, last_offer: int) -> int:
        return min(int((seller_price + last_offer) / 2), self.budget)

# ---------------------------
# NEGOTIATION ENGINE
# ---------------------------
def negotiate(product: Product, buyer_budget: int):
    quality_rounds = {"Export": 3, "A": 6, "B": 8}
    max_rounds = quality_rounds.get(product.quality_grade, 5)

    context = NegotiationContext(product, buyer_budget, 0, [], [], [], [], [])

    seller = SellerAgent(product)
    buyer = BuyerAgent(buyer_budget)

    # Initial offers
    seller_price = seller.current_price
    context.seller_offers.append(seller_price)
    context.messages.append({"Seller": DialogueGenerator.seller_message(product, seller_price, context.seller_history)})

    buyer_offer = buyer.opening_offer(product)
    context.your_offers.append(buyer_offer)
    context.messages.append({"Buyer": DialogueGenerator.buyer_message(product, buyer_offer, context.buyer_history)})

    # Negotiation rounds
    for round_num in range(1, max_rounds + 1):
        context.current_round = round_num

        seller_price = seller.respond(buyer_offer, round_num, max_rounds)
        context.seller_offers.append(seller_price)
        context.messages.append({"Seller": DialogueGenerator.seller_message(product, seller_price, context.seller_history)})

        buyer_offer = buyer.counter_offer(product, seller_price, buyer_offer)
        context.your_offers.append(buyer_offer)
        context.messages.append({"Buyer": DialogueGenerator.buyer_message(product, buyer_offer, context.buyer_history)})

    # Print results 
    print(f"\nNegotiating for {product.name} ({product.quality_grade})")
    print(f"Buyer Budget: ₹{buyer_budget}")
    for msg in context.messages:
        for speaker, text in msg.items():
            print(f"{speaker}: {text}")

    final_price = context.seller_offers[-1]

    # Buyer accepts the final offer
    print(f"Buyer has accepted the final offer at ₹{final_price}.")

    savings = buyer_budget - final_price
    savings_pct = (savings / buyer_budget * 100) if buyer_budget else 0
    below_market_pct = ((product.base_market_price - final_price) / product.base_market_price * 100) if product.base_market_price else 0

    print(f"Final Deal Price: ₹{final_price}")
    print(f"Savings from Buyer Budget: ₹{savings} ({savings_pct:.1f}%)")
    print(f"Below Market Price: {below_market_pct:.1f}%")

# ---------------------------
# TEST PRODUCTS(Sellers With 3 different category of products)
# ---------------------------
products = [
    Product("Alphonso Mangoes", "Mangoes", 10, "Export", "Ratnagiri", 900, {}),
    Product("Kesar Mangoes", "Mangoes", 10, "A", "Gujarat", 750, {}),
    Product("Badami Mangoes", "Mangoes", 10, "B", "Karnataka", 600, {}),
]

buyer_budgets = {"Export": 1300, "A": 1000, "B": 800}

for product in products:
    negotiate(product, buyer_budgets[product.quality_grade])

