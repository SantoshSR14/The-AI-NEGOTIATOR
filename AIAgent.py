"""
===========================================
AI NEGOTIATION AGENT
===========================================


"""

from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
from abc import ABC, abstractmethod
import math
import random

# ============================================
# PART 1: DATA STRUCTURES (DO NOT MODIFY)
# ============================================

@dataclass
class Product:
    """Product being negotiated"""
    name: str
    category: str
    quantity: int
    quality_grade: str  # 'A', 'B', or 'Export'
    origin: str
    base_market_price: int  # Reference price for this product
    attributes: Dict[str, Any]

@dataclass
class NegotiationContext:
    """Current negotiation state"""
    product: Product
    your_budget: int  # Your maximum budget (NEVER exceed this)
    current_round: int
    seller_offers: List[int]  # History of seller's offers
    your_offers: List[int]  # History of your offers
    messages: List[Dict[str, str]]  # Full conversation history

class DealStatus(Enum):
    ONGOING = "ongoing"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    TIMEOUT = "timeout"


# ============================================
# PART 2: BASE AGENT CLASS (DO NOT MODIFY)
# ============================================

class BaseBuyerAgent(ABC):
    """Base class for all buyer agents"""
    
    def __init__(self, name: str):
        self.name = name
        self.personality = self.define_personality()
        
    @abstractmethod
    def define_personality(self) -> Dict[str, Any]:
        pass
    
    @abstractmethod
    def generate_opening_offer(self, context: NegotiationContext) -> Tuple[int, str]:
        pass
    
    @abstractmethod
    def respond_to_seller_offer(self, context: NegotiationContext, seller_price: int, seller_message: str) -> Tuple[DealStatus, int, str]:
        pass
    
    @abstractmethod
    def get_personality_prompt(self) -> str:
        pass


# ============================================
# PART 3: YOUR IMPLEMENTATION STARTS HERE
# ============================================

class YourBuyerAgent(BaseBuyerAgent):
    """
    BUYER AGENT: "Data-Driven Diplomat"

    Strategy highlights:
    - Anchors low but plausible based on market, budget tightness, and quality.
    - Infers seller's hidden minimum from counter-offer patterns.
    - Concedes along a smooth S-curve toward a dynamic target (fair → closing band).
    - Proactively closes in late rounds if it can clear ≈110% of seller's floor (per mock).
    - Never exceeds budget.
    """

    # Personality of the agent
    def define_personality(self) -> Dict[str, Any]:
        return {
            "personality_type": "analytical-diplomatic",
            "traits": ["data-driven", "patient", "polite", "budget-conscious", "fair","dignified"],
            "negotiation_style": (
                "Opens with a brief rationale, concedes in measured steps using signals, "
                "and closes decisively when value aligns."
            ),
            "catchphrases": [
                "Let's keep this fair and crisp.",
                "Numbers talk—I follow the data.",
                "Meet me where value aligns."
            ],
        }

    # Helpers
    def _grade_multiplier(self, product: Product) -> float:
        grade = product.quality_grade.lower()
        export = bool(product.attributes.get("export_grade"))
        if grade == "export" or export:
            return 0.95
        if grade == "a":
            return 0.92
        return 0.88  # grade B or lower

    def calculate_fair_price(self, product: Product) -> int:
        return int(product.base_market_price * self._grade_multiplier(product))

    def _budget_tightness(self, context: NegotiationContext) -> float:
        # >1 roomy, ~1 medium, <1 tight
        return context.your_budget / max(1, context.product.base_market_price)

    def _estimate_min_price(self, context: NegotiationContext) -> Tuple[Optional[int], Dict[str, Any]]:
        """
        Infer seller's hidden min_price from history.
        In the provided mock seller: counter = max(min_price, int(offer*1.15)) (or 1.05 late).
        If a counter > int(offer*1.15), it reveals min_price exactly.
        Otherwise, that counter is an upper bound.
        """
        lower_bound = None
        upper_bound = math.inf
        for i, our_offer in enumerate(context.your_offers):
            if i + 1 >= len(context.seller_offers):
                break
            counter = context.seller_offers[i + 1]
            threshold = int(our_offer * 1.15)
            if counter > threshold:
                lower_bound = counter
                upper_bound = min(upper_bound, counter)
            else:
                upper_bound = min(upper_bound, counter)
        est = None
        if lower_bound is not None:
            est = lower_bound
        elif upper_bound < math.inf:
            est = int(upper_bound * 0.96)  # conservative
        return est, {"lower_bound": lower_bound, "upper_bound": None if upper_bound == math.inf else upper_bound}

    def analyze_negotiation_progress(self, context: NegotiationContext) -> Dict[str, Any]:
        est, bounds = self._estimate_min_price(context)
        return {
            "round": context.current_round,
            "budget_market_ratio": round(self._budget_tightness(context), 3),
            "min_price_estimate": est,
            "bounds": bounds,
            "last_seller_price": context.seller_offers[-1] if context.seller_offers else None,
            "last_our_offer": context.your_offers[-1] if context.your_offers else None,
        }

    def _concession_target(self, context: NegotiationContext, target: int) -> int:
        # S-curve: slow early, faster mid, decisive late across 10 rounds
        r = max(1, context.current_round)
        R = 10
        t = (r - 1) / (R - 1)
        eased = 1 / (1 + math.exp(-8 * (t - 0.5)))  # logistic easing
        anchor = context.your_offers[0] if context.your_offers else int(context.product.base_market_price * 0.65)
        return int(anchor + (target - anchor) * eased)

    def _say(self, body: str) -> str:
        if random.random() < 0.5:
            return f"{body} {random.choice(self.personality['catchphrases'])}"
        return body

    # ------------ Opening -------------
    def generate_opening_offer(self, context: NegotiationContext) -> Tuple[int, str]:
        market = context.product.base_market_price
        bmr = self._budget_tightness(context)
        # Anchor choice depends on budget room and premium grade
        anchor_ratio = 0.62 if bmr >= 1.05 else (0.58 if bmr >= 0.95 else 0.55)
        if context.product.quality_grade.lower() == "export" or context.product.attributes.get("export_grade"):
            anchor_ratio += 0.03
        opening = int(market * anchor_ratio)
        opening = min(opening, context.your_budget)
        opening = max(1, opening)
        msg = (
            f"For {context.product.quantity} {context.product.name} "
            f"({context.product.quality_grade}, {context.product.origin}), market is near ₹{market:,}. "
            f"My opening is ₹{opening:,} considering grade and volume. Happy to move if the numbers make sense."
        )
        return opening, self._say(msg)

    # ------------ Responses -------------
    def respond_to_seller_offer(self, context: NegotiationContext, seller_price: int, seller_message: str) -> Tuple[DealStatus, int, str]:
        market = context.product.base_market_price
        fair = self.calculate_fair_price(context.product)
        budget = context.your_budget
        round_i = context.current_round

        # Opportunistic accept if excellent offer
        if seller_price <= budget and seller_price <= int(0.87 * market):
            return DealStatus.ACCEPTED, seller_price, self._say(
                f"That's compelling at ₹{seller_price:,}. We have a deal."
            )

        est_min, _ = self._estimate_min_price(context)

        # Dynamic ceiling grows with rounds; never above min(budget, 96% of market)
        late_cap = min(budget, int(0.96 * market))
        ceil_now = int(fair + (late_cap - fair) * min(1.0, (round_i - 1) / 8.0))

        # Accept if within ceiling and roughly fair
        if seller_price <= budget and seller_price <= ceil_now and seller_price <= int(0.93 * market):
            return DealStatus.ACCEPTED, seller_price, self._say(
                f"Alright, ₹{seller_price:,} is fair given the grade. Let's lock it."
            )

        # Compute target to move toward
        accept_trigger = int(math.ceil(1.10 * est_min)) if est_min is not None else None
        if accept_trigger is not None:
            target = min(accept_trigger, ceil_now, budget)
        else:
            target = min(int(0.90 * market), ceil_now, budget)

        planned = self._concession_target(context, target)

        # Monotonic increase safeguards
        last = context.your_offers[-1] if context.your_offers else 0
        counter = max(planned, int(last * 1.08), last + 1000)
        counter = min(counter, budget)

        # Late push to avoid timeout
        if round_i >= 9:
            counter = min(max(counter, int(0.90 * market)), budget)
        if round_i >= 10:
            counter = min(max(counter, int(0.92 * market)), budget)

        # If we know the accept_trigger and can afford it in round ≥8, jump to close
        if accept_trigger is not None and round_i >= 8:
            jump = min(accept_trigger, budget, ceil_now)
            if jump > last:
                counter = max(counter, jump)

        # If we are within a whisker of the trigger, nudge above
        if est_min is not None:
            needed = int(math.ceil(1.10 * est_min))
            if needed <= budget and 0 < needed - counter <= max(2000, int(0.005 * market)):
                counter = needed

        msg = (
            f"I can move to ₹{counter:,}. "
            + ("I'm reading your floor and aiming to clear it cleanly; " if est_min is not None else "I'm calibrating to market and grade signals; ")
            + ("pushing to close before we time out." if round_i >= 8 else "let's land this fairly.")
        )
        return DealStatus.ONGOING, counter, self._say(msg)

    def get_personality_prompt(self) -> str:
        return (
            "You are the 'Data-Driven Diplomat' buyer. Speak politely and succinctly, "
            "justify offers with market/quality logic, and stay calm under pressure. "
            "Use short, confident sentences. Sprinkle a friendly catchphrase like "
            "'Numbers talk—I follow the data' or 'Let's keep this fair and crisp' occasionally. "
            "Avoid threats; emphasize fairness, budget discipline, and willingness to close fast when value aligns."
        )


# ============================================
# PART 4: EXAMPLE SIMPLE AGENT (FOR REFERENCE)
# ============================================

class ExampleSimpleAgent(BaseBuyerAgent):
    def define_personality(self) -> Dict[str, Any]:
        return {
            "personality_type": "cautious",
            "traits": ["careful", "budget-conscious", "polite"],
            "negotiation_style": "Makes small incremental offers, very careful with money",
            "catchphrases": ["Let me think about that...", "That's a bit steep for me"],
        }

    def generate_opening_offer(self, context: NegotiationContext) -> Tuple[int, str]:
        opening = int(context.product.base_market_price * 0.6)
        opening = min(opening, context.your_budget)
        return opening, f"I'm interested, but ₹{opening} is what I can offer. Let me think about that..."

    def respond_to_seller_offer(self, context: NegotiationContext, seller_price: int, seller_message: str) -> Tuple[DealStatus, int, str]:
        if seller_price <= context.your_budget and seller_price <= context.product.base_market_price * 0.85:
            return DealStatus.ACCEPTED, seller_price, f"Alright, ₹{seller_price} works for me!"
        last_offer = context.your_offers[-1] if context.your_offers else 0
        counter = min(int(last_offer * 1.1), context.your_budget)
        if counter >= seller_price * 0.95:
            counter = min(seller_price - 1000, context.your_budget)
            return DealStatus.ONGOING, counter, f"That's a bit steep for me. How about ₹{counter}?"
        return DealStatus.ONGOING, counter, f"I can go up to ₹{counter}, but that's pushing my budget."


# ============================================
# PART 5: TESTING FRAMEWORK (DO NOT MODIFY)
# ============================================

class MockSellerAgent:
    """A simple mock seller for testing your agent"""

    def __init__(self, min_price: int, personality: str = "standard"):
        self.min_price = min_price
        self.personality = personality

    def get_opening_price(self, product: Product) -> Tuple[int, str]:
        price = int(product.base_market_price * 1.5)
        return price, f"These are premium {product.quality_grade} grade {product.name}. I'm asking ₹{price}."

    def respond_to_buyer(self, buyer_offer: int, round_num: int) -> Tuple[int, str, bool]:
        if buyer_offer >= self.min_price * 1.1:  # Good profit
            return buyer_offer, f"You have a deal at ₹{buyer_offer}!", True
        if round_num >= 8:  # Close to timeout
            counter = max(self.min_price, int(buyer_offer * 1.05))
            return counter, f"Final offer: ₹{counter}. Take it or leave it.", False
        else:
            counter = max(self.min_price, int(buyer_offer * 1.15))
            return counter, f"I can come down to ₹{counter}.", False


def run_negotiation_test(buyer_agent: BaseBuyerAgent, product: Product, buyer_budget: int, seller_min: int) -> Dict[str, Any]:
    seller = MockSellerAgent(seller_min)
    context = NegotiationContext(
        product=product,
        your_budget=buyer_budget,
        current_round=0,
        seller_offers=[],
        your_offers=[],
        messages=[],
    )

    # Seller opens
    seller_price, seller_msg = seller.get_opening_price(product)
    context.seller_offers.append(seller_price)
    context.messages.append({"role": "seller", "message": seller_msg})

    # Run negotiation
    deal_made = False
    final_price = None

    for round_num in range(10):  # Max 10 rounds
        context.current_round = round_num + 1

        # Buyer responds
        if round_num == 0:
            buyer_offer, buyer_msg = buyer_agent.generate_opening_offer(context)
            status = DealStatus.ONGOING
        else:
            status, buyer_offer, buyer_msg = buyer_agent.respond_to_seller_offer(context, seller_price, seller_msg)

        context.your_offers.append(buyer_offer)
        context.messages.append({"role": "buyer", "message": buyer_msg})

        if status == DealStatus.ACCEPTED:
            deal_made = True
            final_price = seller_price
            break

        # Seller responds
        seller_price, seller_msg, seller_accepts = seller.respond_to_buyer(buyer_offer, round_num)

        if seller_accepts:
            deal_made = True
            final_price = buyer_offer
            context.messages.append({"role": "seller", "message": seller_msg})
            break

        context.seller_offers.append(seller_price)
        context.messages.append({"role": "seller", "message": seller_msg})

    # Calculate results
    result = {
        "deal_made": deal_made,
        "final_price": final_price,
        "rounds": context.current_round,
        "savings": buyer_budget - final_price if deal_made else 0,
        "savings_pct": ((buyer_budget - final_price) / buyer_budget * 100) if deal_made else 0,
        "below_market_pct": ((product.base_market_price - final_price) / product.base_market_price * 100) if deal_made else 0,
        "conversation": context.messages,
    }

    return result


# ============================================
# PART 6: TEST YOUR AGENT
# ============================================

def test_your_agent():
    # Create test products
    test_products = [
        Product(
            name="Alphonso Mangoes",
            category="Mangoes",
            quantity=100,
            quality_grade="A",
            origin="Ratnagiri",
            base_market_price=180000,
            attributes={"ripeness": "optimal", "export_grade": True},
        ),
        Product(
            name="Kesar Mangoes",
            category="Mangoes",
            quantity=150,
            quality_grade="B",
            origin="Gujarat",
            base_market_price=150000,
            attributes={"ripeness": "semi-ripe", "export_grade": False},
        ),
    ]

    your_agent = YourBuyerAgent("TestBuyer")

    print("=" * 60)
    print(f"TESTING YOUR AGENT: {your_agent.name}")
    print(f"Personality: {your_agent.personality['personality_type']}")
    print("=" * 60)

    total_savings = 0
    deals_made = 0

    for product in test_products:
        for scenario in ["easy", "medium", "hard"]:
            if scenario == "easy":
                buyer_budget = int(product.base_market_price * 1.2)
                seller_min = int(product.base_market_price * 0.8)
            elif scenario == "medium":
                buyer_budget = int(product.base_market_price * 1.0)
                seller_min = int(product.base_market_price * 0.85)
            else:  # hard
                buyer_budget = int(product.base_market_price * 0.9)
                seller_min = int(product.base_market_price * 0.82)

            print(f"\nTest: {product.name} - {scenario} scenario")
            print(f"Your Budget: ₹{buyer_budget:,} | Market Price: ₹{product.base_market_price:,}")

            result = run_negotiation_test(your_agent, product, buyer_budget, seller_min)

            if result["deal_made"]:
                deals_made += 1
                total_savings += result["savings"]
                print(f"DEAL at ₹{result['final_price']:,} in {result['rounds']} rounds")
                print(f"Savings: ₹{result['savings']:,} ({result['savings_pct']:.1f}%)")
                print(f"Below Market: {result['below_market_pct']:.1f}%")
            else:
                print(f"NO DEAL after {result['rounds']} rounds")

    print("\n" + "=" * 60)
    print("SUMMARY")
    print(f"Deals Completed: {deals_made}/6")
    print(f"Total Savings: ₹{total_savings:,}")
    print(f"Success Rate: {deals_made/6*100:.1f}%")
    print("=" * 60)


if __name__ == "__main__":
    test_your_agent()
