import enum


class DealType(str, enum.Enum):
    BUY = "deal_buy"
    RENTAL = "deal_rental"
