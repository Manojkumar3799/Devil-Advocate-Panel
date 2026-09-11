"""Stripe tool connector using OAuth access tokens."""

from __future__ import annotations

import httpx
from langchain_core.tools import tool


def make_stripe_tool(access_token: str):
    @tool("stripe_revenue", description="Query real MRR, customer count, and subscription metrics from Stripe")
    def stripe_revenue(query: str) -> str:
        """Fetch live Stripe metrics using connected OAuth account."""
        headers = {"Authorization": f"Bearer {access_token}"}
        try:
            with httpx.Client(timeout=8.0) as client:
                # Query customers
                cust_res = client.get("https://api.stripe.com/v1/customers?limit=100", headers=headers)
                cust_count = len(cust_res.json().get("data", [])) if cust_res.status_code == 200 else 0

                # Query subscriptions
                sub_res = client.get("https://api.stripe.com/v1/subscriptions?limit=100", headers=headers)
                sub_data = sub_res.json().get("data", []) if sub_res.status_code == 200 else []
                active_subs = [s for s in sub_data if s.get("status") == "active"]

                # Calculate MRR estimate from active subscriptions
                mrr_cents = sum(
                    item.get("plan", {}).get("amount", 0)
                    for sub in active_subs
                    for item in sub.get("items", {}).get("data", [])
                )
                mrr_usd = mrr_cents / 100.0

                return (
                    f"Stripe Metrics: {len(active_subs)} active subscriptions, "
                    f"{cust_count} total customers, estimated MRR: ${mrr_usd:,.2f}."
                )
        except Exception as e:
            return f"Error querying Stripe API: {e}"

    return stripe_revenue
