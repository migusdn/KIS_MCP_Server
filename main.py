import json
import logging
import os
import sys
from dotenv import load_dotenv
from datetime import datetime, timedelta

import httpx
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
VIRTUAL_DOMAIN = "https://openapivts.koreainvestment.com:29443"  # 모의투자

# API paths
STOCK_PRICE_PATH = "/uapi/domestic-stock/v1/quotations/inquire-price"  # 현재가조회
BALANCE_PATH = "/uapi/domestic-stock/v1/trading/inquire-balance"  # 잔고조회
TOKEN_PATH = "/oauth2/tokenP"  # 토큰발급
HASHKEY_PATH = "/uapi/hashkey"  # 해시키발급
ORDER_PATH = "/uapi/domestic-stock/v1/trading/order-cash"  # 현금주문
ORDER_LIST_PATH = "/uapi/domestic-stock/v1/trading/inquire-daily-ccld"  # 일별주문체결조회
ORDER_DETAIL_PATH = "/uapi/domestic-stock/v1/trading/inquire-ccnl"  # 주문체결내역조회
STOCK_INFO_PATH = "/uapi/domestic-stock/v1/quotations/inquire-daily-price"  # 일별주가조회
STOCK_HISTORY_PATH = "/uapi/domestic-stock/v1/quotations/inquire-daily-itemchartprice"  # 주식일별주가조회
STOCK_ASK_PATH = "/uapi/domestic-stock/v1/quotations/inquire-asking-price-exp-ccn"  # 주식호가조회

# 해외주식 API 경로
OVERSEAS_STOCK_PRICE_PATH = "/uapi/overseas-price/v1/quotations/price"
OVERSEAS_ORDER_PATH = "/uapi/overseas-stock/v1/trading/order"
OVERSEAS_BALANCE_PATH = "/uapi/overseas-stock/v1/trading/inquire-balance"
OVERSEAS_ORDER_LIST_PATH = "/uapi/overseas-stock/v1/trading/inquire-daily-ccld"

# Headers and other constants
CONTENT_TYPE = "application/json"
AUTH_TYPE = "Bearer"

# Market codes for overseas stock
MARKET_CODES = {
    "NASD": "나스닥",
    "NYSE": "뉴욕",
    "AMEX": "아멕스",
    "SEHK": "홍콩",
    "SHAA": "중국상해",
    "SZAA": "중국심천",
    "TKSE": "일본",
    "HASE": "베트남 하노이",
    "VNSE": "베트남 호치민"
}

class TrIdManager:
    """Transaction ID manager for Korea Investment & Securities API"""
    
    # 실전계좌용 TR_ID
    REAL = {
        # 국내주식
        "balance": "TTTC8434R",  # 잔고조회
        "price": "FHKST01010100",  # 현재가조회
        "buy": "TTTC0802U",  # 주식매수
        "sell": "TTTC0801U",  # 주식매도
        "order_list": "TTTC8001R",  # 일별주문체결조회
        "order_detail": "TTTC8036R",  # 주문체결내역조회
        "stock_info": "FHKST01010400",  # 일별주가조회
        "stock_history": "FHKST03010200",  # 주식일별주가조회
        "stock_ask": "FHKST01010200",  # 주식호가조회
        
        # 해외주식
        "us_buy": "TTTT1002U",      # 미국 매수 주문
        "us_sell": "TTTT1006U",     # 미국 매도 주문
        "jp_buy": "TTTS0308U",      # 일본 매수 주문
        "jp_sell": "TTTS0307U",     # 일본 매도 주문
        "sh_buy": "TTTS0202U",      # 상해 매수 주문
        "sh_sell": "TTTS1005U",     # 상해 매도 주문
        "hk_buy": "TTTS1002U",      # 홍콩 매수 주문
        "hk_sell": "TTTS1001U",     # 홍콩 매도 주문
        "sz_buy": "TTTS0305U",      # 심천 매수 주문
        "sz_sell": "TTTS0304U",     # 심천 매도 주문
        "vn_buy": "TTTS0311U",      # 베트남 매수 주문
        "vn_sell": "TTTS0310U",     # 베트남 매도 주문
    }
    
    # 모의계좌용 TR_ID
    VIRTUAL = {
        # 국내주식
        "balance": "VTTC8434R",  # 잔고조회
        "price": "FHKST01010100",  # 현재가조회
        "buy": "VTTC0802U",  # 주식매수
        "sell": "VTTC0801U",  # 주식매도
        "order_list": "VTTC8001R",  # 일별주문체결조회
        "order_detail": "VTTC8036R",  # 주문체결내역조회
        "stock_info": "FHKST01010400",  # 일별주가조회
        "stock_history": "FHKST03010200",  # 주식일별주가조회
        "stock_ask": "FHKST01010200",  # 주식호가조회
        
        # 해외주식
        "us_buy": "VTTT1002U",      # 미국 매수 주문
        "us_sell": "VTTT1001U",     # 미국 매도 주문
        "jp_buy": "VTTS0308U",      # 일본 매수 주문
        "jp_sell": "VTTS0307U",     # 일본 매도 주문
        "sh_buy": "VTTS0202U",      # 상해 매수 주문
        "sh_sell": "VTTS1005U",     # 상해 매도 주문
        "hk_buy": "VTTS1002U",      # 홍콩 매수 주문
        "hk_sell": "VTTS1001U",     # 홍콩 매도 주문
        "sz_buy": "VTTS0305U",      # 심천 매수 주문
        "sz_sell": "VTTS0304U",     # 심천 매도 주문
        "vn_buy": "VTTS0311U",      # 베트남 매수 주문
        "vn_sell": "VTTS0310U",     # 베트남 매도 주문
    }
    
    @classmethod
    def get_tr_id(cls, operation: str) -> str:
        """
        Get transaction ID for the given operation
        
        Args:
            operation: Operation type ('balance', 'price', 'buy', 'sell', etc.)
            
        Returns:
            str: Transaction ID for the operation
        """
        is_real_account = os.environ.get("KIS_ACCOUNT_TYPE", "REAL").upper() == "REAL"
        tr_id_map = cls.REAL if is_real_account else cls.VIRTUAL
        return tr_id_map.get(operation)
    
    @classmethod
    def get_domain(cls, operation: str) -> str:
        """
        Get domain for the given operation
        
        Args:
            operation: Operation type ('balance', 'price', 'buy', 'sell', etc.)
            
        Returns:
            str: Domain URL for the operation
        """
        is_real_account = os.environ.get("KIS_ACCOUNT_TYPE", "REAL").upper() == "REAL"
        
        # 잔고조회는 실전/모의 계좌별로 다른 도메인 사용
        if operation == "balance":
            return DOMAIN if is_real_account else VIRTUAL_DOMAIN
            
        # 조회 API는 실전/모의 동일한 도메인 사용
        if operation in ["price", "stock_info", "stock_history", "stock_ask"]:
            return DOMAIN
            
        # 거래 API는 계좌 타입에 따라 다른 도메인 사용
        return DOMAIN if is_real_account else VIRTUAL_DOMAIN

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

async def get_hashkey(client: httpx.AsyncClient, token: str, body: dict) -> str:
    """
    Get hash key for order request
    
    Args:
        client: httpx client
        token: Access token
        body: Request body
        
    Returns:
        str: Hash key
    """
    response = await client.post(
        f"{TrIdManager.get_domain('buy')}{HASHKEY_PATH}",
        headers={
            "content-type": CONTENT_TYPE,
            "authorization": f"{AUTH_TYPE} {token}",
            "appkey": os.environ["KIS_APP_KEY"],
            "appsecret": os.environ["KIS_APP_SECRET"],
        },
        json=body
    )
    
    if response.status_code != 200:
        raise Exception(f"Failed to get hash key: {response.text}")
    
    return response.json()["HASH"]

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
            f"{TrIdManager.get_domain('price')}{STOCK_PRICE_PATH}",
            headers={
                "content-type": CONTENT_TYPE,
                "authorization": f"{AUTH_TYPE} {token}",
                "appkey": os.environ["KIS_APP_KEY"],
                "appsecret": os.environ["KIS_APP_SECRET"],
                "tr_id": TrIdManager.get_tr_id("price")
            },
            params={
                "fid_cond_mrkt_div_code": "J",
                "fid_input_iscd": symbol
            }
        )
        
        if response.status_code != 200:
            raise Exception(f"Failed to get stock price: {response.text}")
        
        return response.json()["output"]

@mcp.tool(
    name="inquery-balance",
    description="Get current stock balance information from Korea Investment & Securities",
)
async def inquery_balance():
    """
    Get current stock balance information from Korea Investment & Securities
    
    Returns:
        Dictionary containing stock balance information including:
        - pdno: Stock code
        - prdt_name: Stock name
        - hldg_qty: Holding quantity
        - pchs_amt: Purchase amount
        - prpr: Current price
        - evlu_amt: Evaluation amount
        - evlu_pfls_amt: Evaluation profit/loss amount
        - evlu_pfls_rt: Evaluation profit/loss rate
    """
    async with httpx.AsyncClient() as client:
        token = await get_access_token(client)
        logger.info(f"TrIdManager.get_tr_id('balance'): {TrIdManager.get_tr_id('balance')}")
        # Prepare request data
        request_data = {
            "CANO": os.environ["KIS_CANO"],  # 계좌번호
            "ACNT_PRDT_CD": "01",  # 계좌상품코드 (기본값: 01)
            "AFHR_FLPR_YN": "N",  # 시간외단일가여부
            "INQR_DVSN": "01",  # 조회구분
            "UNPR_DVSN": "01",  # 단가구분
            "FUND_STTL_ICLD_YN": "N",  # 펀드결제분포함여부
            "FNCG_AMT_AUTO_RDPT_YN": "N",  # 융자금액자동상환여부
            "PRCS_DVSN": "00",  # 처리구분
            "CTX_AREA_FK100": "",  # 연속조회검색조건100
            "CTX_AREA_NK100": "",  # 연속조회키100
            "OFL_YN": ""  # 오프라인여부
        }
        response = await client.get(
            f"{TrIdManager.get_domain('balance')}{BALANCE_PATH}",
            headers={
                "content-type": CONTENT_TYPE,
                "authorization": f"{AUTH_TYPE} {token}",
                "appkey": os.environ["KIS_APP_KEY"],
                "appsecret": os.environ["KIS_APP_SECRET"],
                "tr_id": TrIdManager.get_tr_id("balance")
            },
            params=request_data
        )
        
        if response.status_code != 200:
            raise Exception(f"Failed to get balance: {response.text}")
        
        return response.json()

@mcp.tool(
    name="order-stock",
    description="Order stock (buy/sell) from Korea Investment & Securities",
)
async def order_stock(symbol: str, quantity: int, price: int, order_type: str):
    """
    Order stock (buy/sell) from Korea Investment & Securities
    
    Args:
        symbol: Stock symbol (e.g. "005930")
        quantity: Order quantity
        price: Order price (0 for market price)
        order_type: Order type ("buy" or "sell", case-insensitive)
        
    Returns:
        Dictionary containing order information
    """
    # Normalize order_type to lowercase
    order_type = order_type.lower()
    if order_type not in ["buy", "sell"]:
        raise ValueError('order_type must be either "buy" or "sell"')

    async with httpx.AsyncClient() as client:
        token = await get_access_token(client)
        
        # Prepare request data
        request_data = {
            "CANO": os.environ["KIS_CANO"],  # 계좌번호
            "ACNT_PRDT_CD": "01",  # 계좌상품코드
            "PDNO": symbol,  # 종목코드
            "ORD_DVSN": "01" if price == 0 else "00",  # 주문구분 (01: 시장가, 00: 지정가)
            "ORD_QTY": str(quantity),  # 주문수량
            "ORD_UNPR": str(price),  # 주문단가
        }
        
        # Get hashkey
        hashkey = await get_hashkey(client, token, request_data)
        
        response = await client.post(
            f"{TrIdManager.get_domain(order_type)}{ORDER_PATH}",
            headers={
                "content-type": CONTENT_TYPE,
                "authorization": f"{AUTH_TYPE} {token}",
                "appkey": os.environ["KIS_APP_KEY"],
                "appsecret": os.environ["KIS_APP_SECRET"],
                "tr_id": TrIdManager.get_tr_id(order_type),
                "hashkey": hashkey
            },
            json=request_data
        )
        
        if response.status_code != 200:
            raise Exception(f"Failed to order stock: {response.text}")
        
        return response.json()

@mcp.tool(
    name="inquery-order-list",
    description="Get daily order list from Korea Investment & Securities",
)
async def inquery_order_list(start_date: str, end_date: str):
    """
    Get daily order list from Korea Investment & Securities
    
    Args:
        start_date: Start date (YYYYMMDD)
        end_date: End date (YYYYMMDD)
        
    Returns:
        Dictionary containing order list information
    """
    async with httpx.AsyncClient() as client:
        token = await get_access_token(client)
        
        # Prepare request data
        request_data = {
            "CANO": os.environ["KIS_CANO"],  # 계좌번호
            "ACNT_PRDT_CD": "01",  # 계좌상품코드
            "INQR_STRT_DT": start_date,  # 조회시작일자
            "INQR_END_DT": end_date,  # 조회종료일자
            "SLL_BUY_DVSN_CD": "00",  # 매도매수구분
            "INQR_DVSN": "00",  # 조회구분
            "PDNO": "",  # 종목코드
            "CCLD_DVSN": "00",  # 체결구분
            "ORD_GNO_BRNO": "",  # 주문채번지점번호
            "ODNO": "",  # 주문번호
            "INQR_DVSN_3": "00",  # 조회구분3
            "INQR_DVSN_1": "",  # 조회구분1
            "CTX_AREA_FK100": "",  # 연속조회검색조건100
            "CTX_AREA_NK100": "",  # 연속조회키100
        }
        
        response = await client.get(
            f"{TrIdManager.get_domain('order_list')}{ORDER_LIST_PATH}",
            headers={
                "content-type": CONTENT_TYPE,
                "authorization": f"{AUTH_TYPE} {token}",
                "appkey": os.environ["KIS_APP_KEY"],
                "appsecret": os.environ["KIS_APP_SECRET"],
                "tr_id": TrIdManager.get_tr_id("order_list")
            },
            params=request_data
        )
        
        if response.status_code != 200:
            raise Exception(f"Failed to get order list: {response.text}")
        
        return response.json()

@mcp.tool(
    name="inquery-order-detail",
    description="Get order detail from Korea Investment & Securities",
)
async def inquery_order_detail(order_no: str, order_date: str):
    """
    Get order detail from Korea Investment & Securities
    
    Args:
        order_no: Order number
        order_date: Order date (YYYYMMDD)
        
    Returns:
        Dictionary containing order detail information
    """
    async with httpx.AsyncClient() as client:
        token = await get_access_token(client)
        
        # Prepare request data
        request_data = {
            "CANO": os.environ["KIS_CANO"],  # 계좌번호
            "ACNT_PRDT_CD": "01",  # 계좌상품코드
            "INQR_DVSN": "00",  # 조회구분
            "PDNO": "",  # 종목코드
            "ORD_STRT_DT": order_date,  # 주문시작일자
            "ORD_END_DT": order_date,  # 주문종료일자
            "SLL_BUY_DVSN_CD": "00",  # 매도매수구분
            "CCLD_DVSN": "00",  # 체결구분
            "ORD_GNO_BRNO": "",  # 주문채번지점번호
            "ODNO": order_no,  # 주문번호
            "INQR_DVSN_3": "00",  # 조회구분3
            "INQR_DVSN_1": "",  # 조회구분1
            "CTX_AREA_FK100": "",  # 연속조회검색조건100
            "CTX_AREA_NK100": "",  # 연속조회키100
        }
        
        response = await client.get(
            f"{TrIdManager.get_domain('order_detail')}{ORDER_DETAIL_PATH}",
            headers={
                "content-type": CONTENT_TYPE,
                "authorization": f"{AUTH_TYPE} {token}",
                "appkey": os.environ["KIS_APP_KEY"],
                "appsecret": os.environ["KIS_APP_SECRET"],
                "tr_id": TrIdManager.get_tr_id("order_detail")
            },
            params=request_data
        )
        
        if response.status_code != 200:
            raise Exception(f"Failed to get order detail: {response.text}")
        
        return response.json()

@mcp.tool(
    name="inquery-stock-info",
    description="Get daily stock price information from Korea Investment & Securities",
)
async def inquery_stock_info(symbol: str, start_date: str, end_date: str):
    """
    Get daily stock price information from Korea Investment & Securities
    
    Args:
        symbol: Stock symbol (e.g. "005930")
        start_date: Start date (YYYYMMDD)
        end_date: End date (YYYYMMDD)
        
    Returns:
        Dictionary containing daily stock price information
    """
    async with httpx.AsyncClient() as client:
        token = await get_access_token(client)
        
        # Prepare request data
        request_data = {
            "FID_COND_MRKT_DIV_CODE": "J",  # 시장구분
            "FID_INPUT_ISCD": symbol,  # 종목코드
            "FID_INPUT_DATE_1": start_date,  # 시작일자
            "FID_INPUT_DATE_2": end_date,  # 종료일자
            "FID_PERIOD_DIV_CODE": "D",  # 기간분류코드
            "FID_ORG_ADJ_PRC": "0",  # 수정주가원구분
        }
        
        response = await client.get(
            f"{TrIdManager.get_domain('stock_info')}{STOCK_INFO_PATH}",
            headers={
                "content-type": CONTENT_TYPE,
                "authorization": f"{AUTH_TYPE} {token}",
                "appkey": os.environ["KIS_APP_KEY"],
                "appsecret": os.environ["KIS_APP_SECRET"],
                "tr_id": TrIdManager.get_tr_id("stock_info")
            },
            params=request_data
        )
        
        if response.status_code != 200:
            raise Exception(f"Failed to get stock info: {response.text}")
        
        return response.json()

@mcp.tool(
    name="inquery-stock-history",
    description="Get daily stock price history from Korea Investment & Securities",
)
async def inquery_stock_history(symbol: str, start_date: str, end_date: str):
    """
    Get daily stock price history from Korea Investment & Securities
    
    Args:
        symbol: Stock symbol (e.g. "005930")
        start_date: Start date (YYYYMMDD)
        end_date: End date (YYYYMMDD)
        
    Returns:
        Dictionary containing daily stock price history
    """
    async with httpx.AsyncClient() as client:
        token = await get_access_token(client)
        
        # Prepare request data
        request_data = {
            "FID_COND_MRKT_DIV_CODE": "J",  # 시장구분
            "FID_INPUT_ISCD": symbol,  # 종목코드
            "FID_INPUT_DATE_1": start_date,  # 시작일자
            "FID_INPUT_DATE_2": end_date,  # 종료일자
            "FID_PERIOD_DIV_CODE": "D",  # 기간분류코드
            "FID_ORG_ADJ_PRC": "0",  # 수정주가원구분
        }
        
        response = await client.get(
            f"{TrIdManager.get_domain('stock_history')}{STOCK_HISTORY_PATH}",
            headers={
                "content-type": CONTENT_TYPE,
                "authorization": f"{AUTH_TYPE} {token}",
                "appkey": os.environ["KIS_APP_KEY"],
                "appsecret": os.environ["KIS_APP_SECRET"],
                "tr_id": TrIdManager.get_tr_id("stock_history")
            },
            params=request_data
        )
        
        if response.status_code != 200:
            raise Exception(f"Failed to get stock history: {response.text}")
        
        return response.json()

@mcp.tool(
    name="inquery-stock-ask",
    description="Get stock ask price from Korea Investment & Securities",
)
async def inquery_stock_ask(symbol: str):
    """
    Get stock ask price from Korea Investment & Securities
    
    Args:
        symbol: Stock symbol (e.g. "005930")
        
    Returns:
        Dictionary containing stock ask price information
    """
    async with httpx.AsyncClient() as client:
        token = await get_access_token(client)
        
        # Prepare request data
        request_data = {
            "FID_COND_MRKT_DIV_CODE": "J",  # 시장구분
            "FID_INPUT_ISCD": symbol,  # 종목코드
        }
        
        response = await client.get(
            f"{TrIdManager.get_domain('stock_ask')}{STOCK_ASK_PATH}",
            headers={
                "content-type": CONTENT_TYPE,
                "authorization": f"{AUTH_TYPE} {token}",
                "appkey": os.environ["KIS_APP_KEY"],
                "appsecret": os.environ["KIS_APP_SECRET"],
                "tr_id": TrIdManager.get_tr_id("stock_ask")
            },
            params=request_data
        )
        
        if response.status_code != 200:
            raise Exception(f"Failed to get stock ask: {response.text}")
        
        return response.json()

@mcp.tool(
    name="order-overseas-stock",
    description="Order overseas stock (buy/sell) from Korea Investment & Securities",
)
async def order_overseas_stock(symbol: str, quantity: int, price: float, order_type: str, market: str):
    """
    Order overseas stock (buy/sell)
    
    Args:
        symbol: Stock symbol (e.g. "AAPL")
        quantity: Order quantity
        price: Order price (0 for market price)
        order_type: Order type ("buy" or "sell", case-insensitive)
        market: Market code ("NASD" for NASDAQ, "NYSE" for NYSE, etc.)
        
    Returns:
        Dictionary containing order information
    """
    # Normalize order_type to lowercase
    order_type = order_type.lower()
    if order_type not in ["buy", "sell"]:
        raise ValueError('order_type must be either "buy" or "sell"')

    # Normalize market code to uppercase
    market = market.upper()
    if market not in MARKET_CODES:
        raise ValueError(f"Unsupported market: {market}. Supported markets: {', '.join(MARKET_CODES.keys())}")

    async with httpx.AsyncClient() as client:
        token = await get_access_token(client)
        
        # Get market prefix for TR_ID
        market_prefix = {
            "NASD": "us",  # 나스닥
            "NYSE": "us",  # 뉴욕
            "AMEX": "us",  # 아멕스
            "SEHK": "hk",  # 홍콩
            "SHAA": "sh",  # 중국상해
            "SZAA": "sz",  # 중국심천
            "TKSE": "jp",  # 일본
            "HASE": "vn",  # 베트남 하노이
            "VNSE": "vn",  # 베트남 호치민
        }.get(market)
        
        if not market_prefix:
            raise ValueError(f"Unsupported market: {market}")
            
        tr_id_key = f"{market_prefix}_{order_type}"
        tr_id = TrIdManager.get_tr_id(tr_id_key)
        
        if not tr_id:
            raise ValueError(f"Invalid operation type: {tr_id_key}")
        
        # Prepare request data
        request_data = {
            "CANO": os.environ["KIS_CANO"],           # 계좌번호
            "ACNT_PRDT_CD": "01",                     # 계좌상품코드
            "OVRS_EXCG_CD": market,                   # 해외거래소코드
            "PDNO": symbol,                           # 종목코드
            "ORD_QTY": str(quantity),                 # 주문수량
            "OVRS_ORD_UNPR": str(price),             # 주문단가
            "ORD_SVR_DVSN_CD": "0",                  # 주문서버구분코드
            "ORD_DVSN": "00" if price > 0 else "01"  # 주문구분 (00: 지정가, 01: 시장가)
        }
        
        response = await client.post(
            f"{TrIdManager.get_domain(order_type)}{OVERSEAS_ORDER_PATH}",
            headers={
                "content-type": CONTENT_TYPE,
                "authorization": f"{AUTH_TYPE} {token}",
                "appkey": os.environ["KIS_APP_KEY"],
                "appsecret": os.environ["KIS_APP_SECRET"],
                "tr_id": tr_id,
            },
            json=request_data
        )
        
        if response.status_code != 200:
            raise Exception(f"Failed to order overseas stock: {response.text}")
        
        return response.json()

@mcp.tool(
    name="inquery-overseas-stock-price",
    description="Get overseas stock price from Korea Investment & Securities",
)
async def inquery_overseas_stock_price(symbol: str, market: str):
    """
    Get overseas stock price
    
    Args:
        symbol: Stock symbol (e.g. "AAPL")
        market: Market code ("NASD" for NASDAQ, "NYSE" for NYSE, etc.)
        
    Returns:
        Dictionary containing stock price information
    """
    async with httpx.AsyncClient() as client:
        token = await get_access_token(client)
        
        response = await client.get(
            f"{TrIdManager.get_domain('buy')}{OVERSEAS_STOCK_PRICE_PATH}",
            headers={
                "content-type": CONTENT_TYPE,
                "authorization": f"{AUTH_TYPE} {token}",
                "appkey": os.environ["KIS_APP_KEY"],
                "appsecret": os.environ["KIS_APP_SECRET"],
                "tr_id": "HHDFS00000300"
            },
            params={
                "AUTH": "",
                "EXCD": market,
                "SYMB": symbol
            }
        )
        
        if response.status_code != 200:
            raise Exception(f"Failed to get overseas stock price: {response.text}")
        
        return response.json()

if __name__ == "__main__":
    logger.info("Starting MCP server...")
    mcp.run()