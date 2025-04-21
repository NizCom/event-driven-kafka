import uuid
from datetime import datetime
import random


CURRENCIES = ['USD', 'EUR', 'NIS']
STATUSES = ['new', 'pending', 'confirmed']


class Order:
    def __init__(self, order_id: str, items_num: int):
        self.orderId = order_id
        self.customerId = str(uuid.uuid4())
        self.orderDate = datetime.today().strftime("%Y-%m-%d")
        self.items = self._generate_items(items_num)
        self.totalAmount = round(sum(item['quantity'] * item['price'] for item in self.items), 2)
        self.currency = random.choice(CURRENCIES)
        # self.status = random.choice(STATUSES)
        self.status = STATUSES[0]

    def _generate_items(self, items_num: int):
        items = []

        for _ in range(items_num):
            item = {
                "itemId": str(uuid.uuid4()),
                "quantity": random.randint(1, 10),
                "price": round(random.uniform(5.0, 100.0), 2)
            }
            items.append(item)

        return items

    def to_dict(self) -> dict:
        return {
            "orderId": self.orderId,
            "customerId": self.customerId,
            "orderDate": self.orderDate,
            "items": self.items,
            "totalAmount": self.totalAmount,
            "currency": self.currency,
            "status": self.status
        }
