from app.models import Customer, Plan

CUSTOMERS = {"C01" : Customer(customer_id="C01", name="Alice", plan=Plan.BASIC, data_remaining_gb=10.0),
             "C02" : Customer(customer_id="C02", name="Bob", plan=Plan.PREMIUM, data_remaining_gb=20.0),
             "C03" : Customer(customer_id="C03", name="Charlie", plan=Plan.PLUS, data_remaining_gb=30.0)
             }

def get_customer(customer_id: str) -> Customer | None:
    return CUSTOMERS.get(customer_id)

def save_customer(customer: Customer) -> None:
    CUSTOMERS[customer.customer_id] = customer
