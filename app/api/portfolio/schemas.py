from enum import Enum

from pydantic import BaseModel

class MessageCountResponse(BaseModel):
    total_messages: int

class UsersCountResponse(BaseModel):
    total_users: int

class ShillingStatisticsResponse(BaseModel):
    result: dict | list | str

class ShillingStatisticsAction(str, Enum):
    dashboard_info = "dashboard-info"
    total_paid = "total-paid"
    max_min_trade_pnl = "max-min-trade-pnl"
    transactions = "transactions",
    rejections = "rejections"
    current_balance = "balance"
    trades = "trades"
    agent_balance_by_minutes = "agent-balance-by-minutes"
    agent_balance_by_day = "agent-balance-by-day"
    agent_balance_by_week = "agent-balance-by-week"
    agent_balance_by_month = "agent-balance-by-month"
    agent_balance_by_year = "agent-balance-by-year"
    tokens_approved = "tokens-approved",
    assets = "assets"