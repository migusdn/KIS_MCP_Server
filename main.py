import json
import logging
import os
import sys
from dotenv import load_dotenv
from datetime import datetime, timedelta
from pathlib import Path

import httpx
import xmltodict
from fastmcp import FastMCP

# 로깅 설정: 반드시 stderr로 출력
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stderr)
    ]
)

logger = logging.getLogger("mcp-server")

# Create MCP instance
mcp = FastMCP("KIS MCP Server", dependencies=["httpx", "xmltodict"])

# Load environment variables from .env file
load_dotenv()

# Global strings for API endpoints and paths
DOMAIN = "https://openapi.koreainvestment.com:9443"
STOCK_PRICE_PATH = "/uapi/domestic-stock/v1/quotations/inquire-price"
TOKEN_PATH = "/oauth2/tokenP"

# Headers and other constants
CONTENT_TYPE = "application/json"
AUTH_TYPE = "Bearer"

# Token storage
TOKEN_FILE = Path("token.json")

def load_token():
    """Load token from file if it exists and is not expired"""
    if TOKEN_FILE.exists():
        try:
            with open(TOKEN_FILE, 'r') as f:
                token_data = json.load(f)
                expires_at = datetime.fromisoformat(token_data['expires_at'])
                if datetime.now() < expires_at:
                    return token_data['token'], expires_at
        except Exception as e:
            print(f"Error loading token: {e}", file=sys.stderr)
    return None, None

def save_token(token: str, expires_at: datetime):
    """Save token to file"""
    try:
        with open(TOKEN_FILE, 'w') as f:
            json.dump({
                'token': token,
                'expires_at': expires_at.isoformat()
            }, f)
    except Exception as e:
        print(f"Error saving token: {e}", file=sys.stderr)

async def get_access_token(client: httpx.AsyncClient) -> str:
    """
    Get access token with file-based caching
    Returns cached token if valid, otherwise requests new token
    """
    token, expires_at = load_token()
    if token and expires_at and datetime.now() < expires_at:
        return token
    
    token_response = await client.post(
        f"{DOMAIN}{TOKEN_PATH}",
        headers={"content-type": CONTENT_TYPE},
        json={
            "grant_type": "client_credentials",
            "appkey": os.environ["KIS_APP_KEY"],
            "appsecret": os.environ["KIS_APP_SECRET"]
        }
    )
    
    if token_response.status_code != 200:
        raise Exception(f"Failed to get token: {token_response.text}")
    
    token_data = token_response.json()
    token = token_data["access_token"]
    
    expires_at = datetime.now() + timedelta(hours=23)
    save_token(token, expires_at)
    
    return token

@mcp.tool(
    name="inquery-stock-price",
    description="Get current stock price information from Korea Investment & Securities",
)
async def inquery_stock_price(symbol: str):
    """
    Get current stock price information from Korea Investment & Securities
    
    Args:
        symbol: Stock symbol (e.g. "005930" for Samsung Electronics)
        
    Returns:
        Dictionary containing stock price information including:
        - stck_prpr: Current price
        - prdy_vrss: Change from previous day
        - prdy_vrss_sign: Change direction (+/-)
        - prdy_ctrt: Change rate (%)
        - acml_vol: Accumulated volume
        - acml_tr_pbmn: Accumulated trade value
        - hts_kor_isnm: Stock name in Korean
        - stck_mxpr: High price of the day
        - stck_llam: Low price of the day
        - stck_oprc: Opening price
        - stck_prdy_clpr: Previous day's closing price
    """
    async with httpx.AsyncClient() as client:
        token = await get_access_token(client)
        
        response = await client.get(
            f"{DOMAIN}{STOCK_PRICE_PATH}",
            headers={
                "content-type": CONTENT_TYPE,
                "authorization": f"{AUTH_TYPE} {token}",
                "appkey": os.environ["KIS_APP_KEY"],
                "appsecret": os.environ["KIS_APP_SECRET"],
                "tr_id": "FHKST01010100"
            },
            params={
                "fid_cond_mrkt_div_code": "J",
                "fid_input_iscd": symbol
            }
        )
        
        if response.status_code != 200:
            raise Exception(f"Failed to get stock price: {response.text}")
        
        return response.json()["output"]


if __name__ == "__main__":
    logger.info("Starting MCP server...")
    mcp.run()