import json
from bot.config import PROVIDER_TOKEN, TEST_PROVIDER_TOKEN, CURRENCY, PRICE
from dataclasses import dataclass

@dataclass
class Config:
    __instance = None

    def __new__(cls):
      if cls.__instance is None:

        cls.__instance = super(Config, cls).__new__(cls)
        cls.__instance.provider_token = PROVIDER_TOKEN
        cls.__instance.currency = CURRENCY
        cls.__instance.price = int(PRICE)
        provider_data = {
          "receipt": {
            "items": [
              {
                "description": "Подписка на месяц",
                "quantity": "1.00",
                "amount": {
                  "value": f"{cls.__instance.price / 100:.2f}",
                  "currency": cls.__instance.currency
                },
                "vat_code": 1
              }
            ]
          }
        }
        cls.__instance.provider_data = json.dumps(provider_data)
        return cls.__instance

config = Config()