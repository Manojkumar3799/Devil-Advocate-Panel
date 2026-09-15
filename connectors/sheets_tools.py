"""Google Sheets tool connector using OAuth access tokens."""

from __future__ import annotations

import httpx
from langchain_core.tools import tool


def make_sheets_tool(access_token: str):
    @tool("sheets_model", description="Inspect rows and formulas of the founder's Google Sheet financial model")
    def sheets_model(spreadsheet_id: str) -> str:
        """Fetch values from the spreadsheet."""
        headers = {"Authorization": f"Bearer {access_token}"}
        try:
            url = f"https://sheets.googleapis.com/v4/spreadsheets/{spreadsheet_id}/values/A1:E25"
            with httpx.Client(timeout=8.0) as client:
                res = client.get(url, headers=headers)
                if res.status_code == 401:
                    return "Google Sheets connection expired or token revoked — no spreadsheet data available."
                if res.status_code != 200:
                    return f"Google Sheets API returned error {res.status_code}: {res.text}"
                values = res.json().get("values", [])
                lines = [", ".join(str(cell) for cell in row) for row in values[:10]]
                return f"Google Sheet Data Preview ({len(values)} rows found):\n" + "\n".join(lines)
        except Exception as e:
            return f"Error accessing Google Sheet: {e}"

    return sheets_model
