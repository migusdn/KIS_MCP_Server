import argparse
from dataclasses import dataclass
import json
import logging
import os
from pathlib import Path
import sys
from functools import lru_cache
from typing import Any
from dotenv import load_dotenv
from datetime import datetime, timedelta

import httpx
from fastmcp import FastMCP

def _log_level() -> int:
    level_name = os.getenv("KIS_MCP_LOG_LEVEL", "INFO").upper()
    return getattr(logging, level_name, logging.INFO)


# 로깅 설정: 반드시 stderr로 출력
logging.basicConfig(
    level=_log_level(),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stderr)
    ]
)

logger = logging.getLogger("mcp-server")

# MCP 클라이언트별 실행 환경을 명시적으로 다룬다.
SUPPORTED_TRANSPORTS = {"stdio", "sse", "streamable-http"}


@dataclass(frozen=True)
class RuntimeConfig:
    """MCP 서버 실행 설정."""

    transport: str = "stdio"
    host: str = "127.0.0.1"
    port: int = 8000
    path: str = "/mcp"


# Create MCP instance
mcp = FastMCP(
    name="KIS MCP Server",
    instructions="한국투자증권 REST API를 MCP 도구로 제공하는 서버입니다.",
    version="0.2.0",
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="KIS MCP Server")
    parser.add_argument("--env", help="추가로 로드할 .env.<env> 파일 이름")
    parser.add_argument("--app-key", dest="KIS_APP_KEY", help="KIS App Key")
    parser.add_argument("--app-secret", dest="KIS_APP_SECRET", help="KIS App Secret")
    parser.add_argument(
        "--account-type",
        dest="KIS_ACCOUNT_TYPE",
        choices=["REAL", "VIRTUAL", "real", "virtual"],
        help="계좌 타입 (REAL 또는 VIRTUAL)",
    )
    parser.add_argument("--cano", dest="KIS_CANO", help="계좌번호")
    parser.add_argument("--acnt-prdt-cd", dest="KIS_ACNT_PRDT_CD", help="계좌상품코드 (기본값: 01)")
    parser.add_argument(
        "--transport",
        choices=sorted(SUPPORTED_TRANSPORTS),
        help="MCP transport 모드 (기본값: MCP_TYPE 또는 stdio)",
    )
    parser.add_argument("--host", help="HTTP/SSE transport host (기본값: MCP_HOST 또는 127.0.0.1)")
    parser.add_argument("--port", type=int, help="HTTP/SSE transport port (기본값: MCP_PORT 또는 8000)")
    parser.add_argument("--path", help="HTTP/SSE transport path (기본값: MCP_PATH 또는 /mcp)")
    return parser


def _load_env_file(env_name: str | None) -> None:
    """Load .env and optional .env.<env_name> without requiring credentials at import time."""

    load_dotenv()

    if not env_name:
        env_name = os.getenv("ENV")
    if not env_name:
        return

    env_path = Path(f".env.{env_name}")
    if not env_path.exists():
        raise FileNotFoundError(f"환경 파일을 찾을 수 없습니다: {env_path}")
    load_dotenv(dotenv_path=env_path, override=True)


def _apply_cli_env(args: argparse.Namespace) -> None:
    for key in ["KIS_APP_KEY", "KIS_APP_SECRET", "KIS_ACCOUNT_TYPE", "KIS_CANO", "KIS_ACNT_PRDT_CD"]:
        value = getattr(args, key, None)
        if value:
            os.environ[key] = value.upper() if key == "KIS_ACCOUNT_TYPE" else value


def get_runtime_config(args: argparse.Namespace) -> RuntimeConfig:
    transport = args.transport or os.getenv("MCP_TYPE", "stdio")
    if transport not in SUPPORTED_TRANSPORTS:
        logger.warning("지원하지 않는 MCP_TYPE=%s, stdio로 대체합니다.", transport)
        transport = "stdio"

    port_value = args.port or int(os.getenv("MCP_PORT", "8000") or "8000")
    return RuntimeConfig(
        transport=transport,
        host=args.host or os.getenv("MCP_HOST", "127.0.0.1"),
        port=port_value,
        path=args.path or os.getenv("MCP_PATH", "/mcp"),
    )


def configure_runtime(argv: list[str] | None = None) -> RuntimeConfig:
    parser = build_parser()
    args = parser.parse_args(argv)
    _load_env_file(args.env)
    _apply_cli_env(args)
    return get_runtime_config(args)


def run_mcp_server(config: RuntimeConfig) -> None:
    logger.info("Starting KIS MCP server with transport=%s", config.transport)
    if config.transport == "stdio":
        mcp.run(transport="stdio")
        return

    mcp.run(
        transport=config.transport,
        host=config.host,
        port=config.port,
        path=config.path,
    )


def main(argv: list[str] | None = None) -> None:
    try:
        config = configure_runtime(argv)
        validate_kis_credentials(require_account=True)
    except (FileNotFoundError, ValueError) as exc:
        logger.error("%s", exc)
        sys.exit(1)

    run_mcp_server(config)


# Load default .env for import-time helper usage, but do not fail when absent.
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
INDEX_PRICE_PATH = "/uapi/domestic-stock/v1/quotations/inquire-index-price"  # 국내업종 현재지수
STOCK_BASIC_INFO_PATH = "/uapi/domestic-stock/v1/quotations/search-stock-info"  # 주식기본조회

# 해외주식 API 경로
OVERSEAS_STOCK_PRICE_PATH = "/uapi/overseas-price/v1/quotations/price"
OVERSEAS_ORDER_PATH = "/uapi/overseas-stock/v1/trading/order"
OVERSEAS_BALANCE_PATH = "/uapi/overseas-stock/v1/trading/inquire-balance"
OVERSEAS_ORDER_LIST_PATH = "/uapi/overseas-stock/v1/trading/inquire-daily-ccld"

# Headers and other constants
CONTENT_TYPE = "application/json"
AUTH_TYPE = "Bearer"
TRADING_ENABLED_ENV = "KIS_ENABLE_TRADING"
TRUTHY_VALUES = {"1", "true", "yes", "y", "on"}

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

OVERSEAS_QUOTE_EXCHANGE_CODES = {
    "NASD": "NAS",
    "NYSE": "NYS",
    "AMEX": "AMS",
    "SEHK": "HKS",
    "SHAA": "SHS",
    "SZAA": "SZS",
    "TKSE": "TSE",
    "HASE": "HNX",
    "VNSE": "HSX",
    "NAS": "NAS",
    "NYS": "NYS",
    "AMS": "AMS",
    "HKS": "HKS",
    "SHS": "SHS",
    "SZS": "SZS",
    "TSE": "TSE",
    "HNX": "HNX",
    "HSX": "HSX",
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
        "index_price": "FHPUP02100000",  # 국내업종 현재지수
        "stock_basic_info": "CTPF1002R",  # 주식기본조회
        
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
        "index_price": "FHPUP02100000",  # 국내업종 현재지수
        "stock_basic_info": "CTPF1002R",  # 주식기본조회
        
        # 해외주식
        "us_buy": "VTTT1002U",      # 미국 매수 주문
        "us_sell": "VTTT1006U",     # 미국 매도 주문
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
        if operation in ["price", "stock_info", "stock_history", "stock_ask", "index_price", "stock_basic_info"]:
            return DOMAIN
            
        # 거래 API는 계좌 타입에 따라 다른 도메인 사용
        return DOMAIN if is_real_account else VIRTUAL_DOMAIN

# Token storage
TOKEN_FILE = Path(os.getenv("KIS_TOKEN_FILE", "token.json"))
DEFAULT_ACNT_PRDT_CD = "01"
API_SPEC_FILE = Path(__file__).resolve().parent / "data" / "kis_api_specs.json"

_http_client: httpx.AsyncClient | None = None
_token_cache = {
    "token": None,
    "expires_at": None,
    "app_key": None,
    "token_scope": None,
}


def get_token_file() -> Path:
    """Return the token cache file path, allowing tests/users to override it."""

    return Path(os.getenv("KIS_TOKEN_FILE", str(TOKEN_FILE)))


def get_account_product_code() -> str:
    """Return account product code; KIS stock accounts usually use 01."""

    return os.getenv("KIS_ACNT_PRDT_CD") or os.getenv("KIS_ACNT_PRDT_CODE") or DEFAULT_ACNT_PRDT_CD


def get_account_number() -> str:
    cano = os.getenv("KIS_CANO")
    if not cano:
        raise ValueError("Missing required environment variable: KIS_CANO")
    return cano


def validate_kis_credentials(require_account: bool = False) -> None:
    required = ["KIS_APP_KEY", "KIS_APP_SECRET", "KIS_ACCOUNT_TYPE"]
    if require_account:
        required.append("KIS_CANO")

    missing = [name for name in required if not os.getenv(name)]
    if missing:
        raise ValueError(
            "Missing required environment variables: "
            + ", ".join(missing)
            + ". 환경변수, .env 또는 명령줄 인자로 설정하세요."
        )

    account_type = os.getenv("KIS_ACCOUNT_TYPE", "").upper()
    if account_type not in {"REAL", "VIRTUAL"}:
        raise ValueError('KIS_ACCOUNT_TYPE must be either "REAL" or "VIRTUAL"')


async def get_http_client() -> httpx.AsyncClient:
    """Return a shared async HTTP client for KIS API calls."""

    global _http_client
    if _http_client is None or _http_client.is_closed:
        _http_client = httpx.AsyncClient(
            timeout=httpx.Timeout(30.0),
            limits=httpx.Limits(
                max_keepalive_connections=10,
                max_connections=20,
                keepalive_expiry=60,
            ),
        )
    return _http_client


class _KisClientContext:
    async def __aenter__(self) -> httpx.AsyncClient:
        return await get_http_client()

    async def __aexit__(self, exc_type, exc, tb) -> bool:
        return False


def kis_client() -> _KisClientContext:
    """Context manager that preserves existing call structure while reusing one client."""

    return _KisClientContext()


async def close_http_client() -> None:
    global _http_client
    if _http_client is not None and not _http_client.is_closed:
        await _http_client.aclose()
    _http_client = None


def kis_headers(token: str, tr_id: str | None = None, hashkey: str | None = None) -> dict[str, str]:
    validate_kis_credentials(require_account=False)
    headers = {
        "content-type": CONTENT_TYPE,
        "authorization": f"{AUTH_TYPE} {token}",
        "appkey": os.environ["KIS_APP_KEY"],
        "appsecret": os.environ["KIS_APP_SECRET"],
    }
    if tr_id:
        headers["tr_id"] = tr_id
    if hashkey:
        headers["hashkey"] = hashkey
    return headers


def response_json(response: httpx.Response, error_message: str) -> dict:
    if response.status_code != 200:
        raise Exception(f"{error_message}: {response.text}")
    try:
        return response.json()
    except ValueError as exc:
        raise Exception(f"{error_message}: invalid JSON response") from exc


@lru_cache(maxsize=1)
def load_kis_api_catalog() -> dict[str, Any]:
    """Load KIS API interface metadata collected for this MCP server."""

    with open(API_SPEC_FILE, encoding="utf-8") as f:
        return json.load(f)


def iter_kis_api_specs() -> list[dict[str, Any]]:
    catalog = load_kis_api_catalog()
    specs: list[dict[str, Any]] = []
    for group, group_data in catalog["groups"].items():
        for api_type, spec in group_data["apis"].items():
            specs.append({**spec, "group": group, "api_type": api_type})
    return specs


def get_kis_api_spec_record(group: str, api_type: str) -> dict[str, Any]:
    catalog = load_kis_api_catalog()
    try:
        return catalog["groups"][group]["apis"][api_type]
    except KeyError as exc:
        raise ValueError(f"Unknown KIS API spec: {group}.{api_type}") from exc


def _env_is_virtual(env_dv: str | None = None) -> bool:
    if env_dv:
        return env_dv.lower() in {"demo", "virtual", "vps", "paper"}
    return os.getenv("KIS_ACCOUNT_TYPE", "REAL").upper() == "VIRTUAL"


def _select_api_domain(spec: dict[str, Any], tr_id: str | None, env_dv: str | None) -> str:
    path = spec["path"]
    if spec["group"] == "auth":
        return VIRTUAL_DOMAIN if _env_is_virtual(env_dv) else DOMAIN

    if _env_is_virtual(env_dv) and (tr_id or "").startswith("V"):
        return VIRTUAL_DOMAIN
    if _env_is_virtual(env_dv) and "/trading/" in path:
        return VIRTUAL_DOMAIN
    return DOMAIN


def _norm_lookup(payload: dict[str, Any], *names: str) -> str:
    for name in names:
        for key in {name, name.lower(), name.upper()}:
            if key in payload and payload[key] is not None:
                return str(payload[key])
    return ""


def _norm_side(value: str) -> str:
    normalized = value.strip().lower()
    if normalized in {"buy", "b", "02", "2", "매수"}:
        return "buy"
    if normalized in {"sell", "s", "01", "1", "매도"}:
        return "sell"
    return normalized


def _virtualize_tr_id(tr_id: str, env_dv: str | None = None) -> str:
    if _env_is_virtual(env_dv) and tr_id and tr_id[0] in {"T", "J", "C"}:
        return "V" + tr_id[1:]
    return tr_id


def _env_flag_enabled(name: str) -> bool:
    return os.getenv(name, "").strip().lower() in TRUTHY_VALUES


def _is_state_changing_trading_api(spec: dict[str, Any]) -> bool:
    return spec.get("http_method") == "POST" and "/trading/" in spec.get("path", "")


def _ensure_trading_enabled(spec: dict[str, Any]) -> None:
    if not _is_state_changing_trading_api(spec):
        return
    if _env_flag_enabled(TRADING_ENABLED_ENV):
        return
    raise PermissionError(
        f"{spec['group']}.{spec['api_type']} is a state-changing trading API. "
        f"Set {TRADING_ENABLED_ENV}=true to enable order/modify/cancel calls."
    )


def _infer_tr_id_from_payload(spec: dict[str, Any], payload: dict[str, Any], env_dv: str | None) -> str | None:
    key = (spec["group"], spec["api_type"])

    if key == ("domestic_stock", "order_cash"):
        side = _norm_side(_norm_lookup(payload, "ORD_DV"))
        mapping = {
            "sell": "TTTC0011U",
            "buy": "TTTC0012U",
        }
        if side in mapping:
            return _virtualize_tr_id(mapping[side], env_dv)

    if key == ("domestic_stock", "order_credit"):
        side = _norm_side(_norm_lookup(payload, "ORD_DV"))
        mapping = {
            "buy": "TTTC0052U",
            "sell": "TTTC0051U",
        }
        if side in mapping:
            return mapping[side]

    if key == ("domestic_stock", "inquire_daily_ccld"):
        period = _norm_lookup(payload, "PD_DV").strip().lower()
        mapping = {
            "before": "CTSC9215R",
            "inner": "TTTC0081R",
        }
        if period in mapping:
            return _virtualize_tr_id(mapping[period], env_dv)

    if key == ("domestic_stock", "order_resv_rvsecncl"):
        order_type = _norm_lookup(payload, "ORD_TYPE").strip().lower()
        mapping = {
            "cancel": "CTSC0009U",
            "modify": "CTSC0013U",
        }
        if order_type in mapping:
            return mapping[order_type]

    if key == ("domestic_futureoption", "order"):
        day = _norm_lookup(payload, "ORD_DV").strip().lower()
        if _env_is_virtual(env_dv) and day == "day":
            return "VTTO1101U"
        mapping = {
            "day": "TTTO1101U",
            "night": "STTN1101U",
        }
        if day in mapping and not _env_is_virtual(env_dv):
            return mapping[day]
        if day == "night" and _env_is_virtual(env_dv):
            raise ValueError("domestic_futureoption.order demo environment supports only day orders")

    if key == ("domestic_futureoption", "order_rvsecncl"):
        day = _norm_lookup(payload, "DAY_DV").strip().lower()
        if _env_is_virtual(env_dv) and day == "day":
            return "VTTO1103U"
        mapping = {
            "day": "TTTO1103U",
            "night": "TTTN1103U",
        }
        if day in mapping and not _env_is_virtual(env_dv):
            return mapping[day]
        if day == "night" and _env_is_virtual(env_dv):
            raise ValueError("domestic_futureoption.order_rvsecncl demo environment supports only day orders")

    if key == ("overseas_futureoption", "order_rvsecncl"):
        order_division = _norm_lookup(payload, "ORD_DV").strip().lower()
        mapping = {
            "0": "OTFM3002U",
            "modify": "OTFM3002U",
            "1": "OTFM3003U",
            "cancel": "OTFM3003U",
        }
        if order_division in mapping:
            return mapping[order_division]

    if key == ("overseas_stock", "daytime_order"):
        side = _norm_side(_norm_lookup(payload, "ORDER_DV"))
        mapping = {
            "buy": "TTTS6036U",
            "sell": "TTTS6037U",
        }
        if side in mapping:
            return mapping[side]

    if key == ("overseas_stock", "order"):
        side = _norm_side(_norm_lookup(payload, "ORD_DV"))
        market = _norm_lookup(payload, "OVRS_EXCG_CD").strip().upper()
        market_group = {
            "NASD": "us",
            "NYSE": "us",
            "AMEX": "us",
            "SEHK": "hk",
            "SHAA": "sh",
            "SZAA": "sz",
            "TKSE": "jp",
            "HASE": "vn",
            "VNSE": "vn",
        }.get(market)
        mapping = {
            ("us", "buy"): "TTTT1002U",
            ("us", "sell"): "TTTT1006U",
            ("hk", "buy"): "TTTS1002U",
            ("hk", "sell"): "TTTS1001U",
            ("sh", "buy"): "TTTS0202U",
            ("sh", "sell"): "TTTS1005U",
            ("sz", "buy"): "TTTS0305U",
            ("sz", "sell"): "TTTS0304U",
            ("jp", "buy"): "TTTS0308U",
            ("jp", "sell"): "TTTS0307U",
            ("vn", "buy"): "TTTS0311U",
            ("vn", "sell"): "TTTS0310U",
        }
        selected = mapping.get((market_group, side))
        if selected:
            return _virtualize_tr_id(selected, env_dv)

    if key == ("overseas_stock", "order_resv"):
        order_type = _norm_lookup(payload, "ORD_DV").strip()
        mapping = {
            "usBuy": "TTTT3014U",
            "usSell": "TTTT3016U",
            "asia": "TTTS3013U",
        }
        if order_type in mapping:
            return _virtualize_tr_id(mapping[order_type], env_dv)

    if key == ("overseas_stock", "order_resv_list"):
        nation = _norm_lookup(payload, "NAT_DV").strip().lower()
        mapping = {
            "us": "TTTT3039R",
            "asia": "TTTS3014R",
        }
        if nation in mapping:
            return mapping[nation]

    return None


def _select_tr_id(
    spec: dict[str, Any],
    tr_id: str | None = None,
    env_dv: str | None = None,
    payload: dict[str, Any] | None = None,
) -> str | None:
    if tr_id:
        return tr_id

    candidates = spec.get("tr_ids", [])
    if not candidates:
        return None

    if payload is not None:
        inferred = _infer_tr_id_from_payload(spec, payload, env_dv)
        if inferred:
            return inferred

    if len(candidates) == 1:
        return candidates[0]

    want_virtual = _env_is_virtual(env_dv)
    filtered = [candidate for candidate in candidates if candidate.startswith("V") == want_virtual]
    if len(filtered) == 1:
        return filtered[0]

    raise ValueError(
        f"{spec['group']}.{spec['api_type']} has multiple TR_ID candidates and could not infer one. "
        f"Pass tr_id explicitly. candidates={', '.join(candidates)}"
    )


def _lookup_input_value(input_params: dict[str, Any], name: str, wire_name: str) -> tuple[bool, Any]:
    lookup_keys = {
        name,
        name.lower(),
        name.upper(),
        wire_name,
        wire_name.lower(),
        wire_name.upper(),
    }
    for key in lookup_keys:
        if key in input_params:
            return True, input_params[key]
    return False, None


def _default_param_value(name: str, wire_name: str) -> tuple[bool, Any]:
    if wire_name == "CANO":
        return True, get_account_number()
    if wire_name == "ACNT_PRDT_CD":
        return True, get_account_product_code()
    if name == "grant_type":
        return True, "client_credentials"
    if name == "appkey":
        value = os.getenv("KIS_APP_KEY")
        return (value is not None), value
    if name == "appsecret":
        value = os.getenv("KIS_APP_SECRET")
        return (value is not None), value
    return False, None


def _prepare_api_payload(
    spec: dict[str, Any],
    params: dict[str, Any] | None,
    allow_extra_params: bool = False,
) -> dict[str, Any]:
    input_params = params or {}
    if not isinstance(input_params, dict):
        raise ValueError("params must be an object/dict")

    payload: dict[str, Any] = {}
    consumed: set[str] = set()
    missing: list[str] = []
    known_wire_names = {param["wire_name"] for param in spec.get("params", [])}

    for param in spec.get("params", []):
        name = param["name"]
        wire_name = param["wire_name"]
        found, value = _lookup_input_value(input_params, name, wire_name)
        if found:
            consumed.update({name, name.lower(), name.upper(), wire_name, wire_name.lower(), wire_name.upper()})
        else:
            found, value = _default_param_value(name, wire_name)
        if not found and param.get("default") is not None:
            found, value = True, param["default"]
        if not found:
            if param.get("required"):
                missing.append(name)
            continue
        payload[wire_name] = value

    unknown: list[str] = []
    for key, value in input_params.items():
        if key in consumed:
            continue
        wire_key = key if key in known_wire_names or key.upper() in known_wire_names else key.upper()
        if wire_key.upper() in known_wire_names:
            wire_key = wire_key.upper()
        elif not allow_extra_params:
            unknown.append(key)
            continue
        payload[wire_key] = value

    if missing:
        raise ValueError(f"Missing required params for {spec['group']}.{spec['api_type']}: {', '.join(missing)}")
    if unknown:
        raise ValueError(f"Unknown params for {spec['group']}.{spec['api_type']}: {', '.join(sorted(unknown))}")

    return payload


@mcp.tool(
    name="list-kis-api-specs",
    description="List collected KIS REST API specs available through the generic KIS API caller",
)
async def list_kis_api_specs(group: str | None = None, query: str | None = None, limit: int = 50):
    catalog = load_kis_api_catalog()
    query_text = (query or "").lower()
    items: list[dict[str, Any]] = []

    for spec in iter_kis_api_specs():
        if group and spec["group"] != group:
            continue
        searchable = " ".join(
            str(spec.get(key, "")) for key in ["group", "api_type", "category", "name", "path"]
        ).lower()
        if query_text and query_text not in searchable:
            continue
        items.append(
            {
                "group": spec["group"],
                "api_type": spec["api_type"],
                "category": spec.get("category", ""),
                "name": spec.get("name", ""),
                "path": spec["path"],
                "http_method": spec["http_method"],
                "tr_ids": spec.get("tr_ids", []),
                "required_params": [p["name"] for p in spec.get("params", []) if p.get("required")],
            }
        )

    return {
        "total_apis": catalog["total_apis"],
        "matched": len(items),
        "items": items[: max(1, min(limit, 200))],
    }


@mcp.tool(
    name="get-kis-api-spec",
    description="Get one KIS REST API spec with endpoint, TR_ID candidates, and request parameters",
)
async def get_kis_api_spec(group: str, api_type: str):
    return get_kis_api_spec_record(group, api_type)


@mcp.tool(
    name="call-kis-api",
    description="Call any collected KIS REST API by group/api_type using cataloged interface metadata",
)
async def call_kis_api(
    group: str,
    api_type: str,
    params: dict[str, Any] | None = None,
    tr_id: str | None = None,
    tr_cont: str = "",
    env_dv: str | None = None,
    auto_hashkey: bool = True,
    allow_extra_params: bool = False,
):
    spec = get_kis_api_spec_record(group, api_type)
    payload = _prepare_api_payload(spec, params, allow_extra_params=allow_extra_params)
    selected_tr_id = _select_tr_id(spec, tr_id=tr_id, env_dv=env_dv, payload=payload)
    _ensure_trading_enabled(spec)
    base_url = _select_api_domain(spec, selected_tr_id, env_dv)
    url = f"{base_url}{spec['path']}"

    async with kis_client() as client:
        if group == "auth":
            headers = {"content-type": CONTENT_TYPE}
        else:
            token = await get_access_token(client, env_dv=env_dv)
            headers = kis_headers(token, selected_tr_id)
            headers["custtype"] = "P"
            headers["tr_cont"] = tr_cont
            if spec["http_method"] == "POST" and auto_hashkey:
                headers["hashkey"] = await get_hashkey(client, token, payload, domain=base_url)

        if spec["http_method"] == "POST":
            response = await client.post(url, headers=headers, json=payload)
        else:
            response = await client.get(url, headers=headers, params=payload)
        return response_json(response, f"Failed to call KIS API {group}.{api_type}")


def _token_scope(env_dv: str | None = None) -> str:
    return "virtual" if _env_is_virtual(env_dv) else "real"


def load_token(env_dv: str | None = None):
    """Load token from file if it exists and is not expired"""
    token_file = get_token_file()
    if token_file.exists():
        try:
            with open(token_file, 'r') as f:
                token_data = json.load(f)
                expires_at = datetime.fromisoformat(token_data['expires_at'])
                cached_app_key = token_data.get("app_key")
                current_app_key = os.getenv("KIS_APP_KEY")
                if cached_app_key and current_app_key and cached_app_key != current_app_key:
                    return None, None
                cached_scope = token_data.get("token_scope")
                if cached_scope != _token_scope(env_dv):
                    return None, None
                if datetime.now() < expires_at:
                    return token_data['token'], expires_at
        except Exception as e:
            print(f"Error loading token: {e}", file=sys.stderr)
    return None, None


def save_token(token: str, expires_at: datetime, env_dv: str | None = None):
    """Save token to file"""
    try:
        token_file = get_token_file()
        token_file.parent.mkdir(parents=True, exist_ok=True)
        fd = os.open(token_file, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, 'w') as f:
            json.dump({
                'token': token,
                'expires_at': expires_at.isoformat(),
                'app_key': os.getenv("KIS_APP_KEY"),
                'token_scope': _token_scope(env_dv),
            }, f)
        os.chmod(token_file, 0o600)
    except Exception as e:
        print(f"Error saving token: {e}", file=sys.stderr)


async def get_access_token(client: httpx.AsyncClient, env_dv: str | None = None) -> str:
    """
    Get access token with file-based caching
    Returns cached token if valid, otherwise requests new token
    """
    validate_kis_credentials(require_account=False)
    current_app_key = os.environ["KIS_APP_KEY"]
    current_scope = _token_scope(env_dv)

    if (
        _token_cache["token"]
        and _token_cache["expires_at"]
        and _token_cache["app_key"] == current_app_key
        and _token_cache["token_scope"] == current_scope
        and datetime.now() < _token_cache["expires_at"]
    ):
        return _token_cache["token"]

    token, expires_at = load_token(env_dv=env_dv)
    if token and expires_at and datetime.now() < expires_at:
        _token_cache.update({
            "token": token,
            "expires_at": expires_at,
            "app_key": current_app_key,
            "token_scope": current_scope,
        })
        return token
    
    token_response = await client.post(
        f"{VIRTUAL_DOMAIN if _env_is_virtual(env_dv) else DOMAIN}{TOKEN_PATH}",
        headers={"content-type": CONTENT_TYPE},
        json={
            "grant_type": "client_credentials",
            "appkey": current_app_key,
            "appsecret": os.environ["KIS_APP_SECRET"]
        },
        timeout=30.0,
    )
    token_data = response_json(token_response, "Failed to get token")
    if "access_token" not in token_data:
        raise Exception("Failed to get token: access_token missing in response")

    token = token_data["access_token"]
    
    expires_at = datetime.now() + timedelta(hours=23)
    save_token(token, expires_at, env_dv=env_dv)
    _token_cache.update({
        "token": token,
        "expires_at": expires_at,
        "app_key": current_app_key,
        "token_scope": current_scope,
    })
    
    return token

async def get_hashkey(client: httpx.AsyncClient, token: str, body: dict, domain: str | None = None) -> str:
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
        f"{(domain or TrIdManager.get_domain('buy')).rstrip('/')}{HASHKEY_PATH}",
        headers=kis_headers(token, tr_id=""),
        json=body
    )
    data = response_json(response, "Failed to get hash key")
    if "HASH" not in data:
        raise Exception("Failed to get hash key: HASH missing in response")
    return data["HASH"]

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
    async with kis_client() as client:
        token = await get_access_token(client)
        response = await client.get(
            f"{TrIdManager.get_domain('price')}{STOCK_PRICE_PATH}",
            headers=kis_headers(token, TrIdManager.get_tr_id("price")),
            params={
                "fid_cond_mrkt_div_code": "J",
                "fid_input_iscd": symbol
            }
        )
        return response_json(response, "Failed to get stock price")["output"]

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
    async with kis_client() as client:
        token = await get_access_token(client)
        logger.debug("balance tr_id=%s", TrIdManager.get_tr_id("balance"))
        # Prepare request data
        request_data = {
            "CANO": get_account_number(),  # 계좌번호
            "ACNT_PRDT_CD": get_account_product_code(),  # 계좌상품코드 (기본값: 01)
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
            headers=kis_headers(token, TrIdManager.get_tr_id("balance")),
            params=request_data
        )
        return response_json(response, "Failed to get balance")

@mcp.tool(
    name="order-stock",
    description="Order stock (buy/sell) from Korea Investment & Securities",
)
async def order_stock(symbol: str, quantity: int, price: int, order_type: str, exchange: str = "KRX"):
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

    return await call_kis_api(
        "domestic_stock",
        "order_cash",
        {
            "excg_id_dvsn_cd": exchange,
            "ord_dv": order_type,
            "ord_dvsn": "01" if price == 0 else "00",
            "ord_qty": str(quantity),
            "ord_unpr": str(price),
            "pdno": symbol,
        },
    )

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
    async with kis_client() as client:
        token = await get_access_token(client)
        
        # Prepare request data
        request_data = {
            "CANO": get_account_number(),  # 계좌번호
            "ACNT_PRDT_CD": get_account_product_code(),  # 계좌상품코드
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
            headers=kis_headers(token, TrIdManager.get_tr_id("order_list")),
            params=request_data
        )
        return response_json(response, "Failed to get order list")

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
    async with kis_client() as client:
        token = await get_access_token(client)
        
        # Prepare request data
        request_data = {
            "CANO": get_account_number(),  # 계좌번호
            "ACNT_PRDT_CD": get_account_product_code(),  # 계좌상품코드
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
            headers=kis_headers(token, TrIdManager.get_tr_id("order_detail")),
            params=request_data
        )
        return response_json(response, "Failed to get order detail")

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
    async with kis_client() as client:
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
            headers=kis_headers(token, TrIdManager.get_tr_id("stock_info")),
            params=request_data
        )
        return response_json(response, "Failed to get stock info")

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
    async with kis_client() as client:
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
            headers=kis_headers(token, TrIdManager.get_tr_id("stock_history")),
            params=request_data
        )
        return response_json(response, "Failed to get stock history")

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
    async with kis_client() as client:
        token = await get_access_token(client)
        
        # Prepare request data
        request_data = {
            "FID_COND_MRKT_DIV_CODE": "J",  # 시장구분
            "FID_INPUT_ISCD": symbol,  # 종목코드
        }
        
        response = await client.get(
            f"{TrIdManager.get_domain('stock_ask')}{STOCK_ASK_PATH}",
            headers=kis_headers(token, TrIdManager.get_tr_id("stock_ask")),
            params=request_data
        )
        return response_json(response, "Failed to get stock ask")


@mcp.tool(
    name="inquery-stock-market",
    description="Get Korean stock market index price from Korea Investment & Securities",
)
async def inquery_stock_market(index_code: str = "0001", market_div_code: str = "U"):
    """
    Get Korean stock market index price.

    Args:
        index_code: 업종/지수 코드. 예: 코스피 "0001", 코스닥 "1001", 코스피200 "2001"
        market_div_code: 시장 분류 코드. 국내업종 현재지수는 보통 "U"를 사용

    Returns:
        Dictionary containing current index information
    """
    if not index_code:
        raise ValueError("index_code is required. e.g. '0001' for KOSPI")
    if not market_div_code:
        raise ValueError("market_div_code is required. e.g. 'U'")

    async with kis_client() as client:
        token = await get_access_token(client)
        response = await client.get(
            f"{TrIdManager.get_domain('index_price')}{INDEX_PRICE_PATH}",
            headers=kis_headers(token, TrIdManager.get_tr_id("index_price")),
            params={
                "FID_COND_MRKT_DIV_CODE": market_div_code,
                "FID_INPUT_ISCD": index_code,
            },
        )
        return response_json(response, "Failed to get stock market index")


@mcp.tool(
    name="inquery-stock-basic-info",
    description="Get basic domestic stock product information from Korea Investment & Securities",
)
async def inquery_stock_basic_info(symbol: str, product_type: str = "300"):
    """
    Get basic domestic stock information.

    Args:
        symbol: 종목코드 6자리. 예: 삼성전자 "005930"
        product_type: 상품유형코드. 주식/ETF/ETN/ELW는 "300"

    Returns:
        Dictionary containing basic stock/product metadata
    """
    if not symbol:
        raise ValueError("symbol is required. e.g. '005930'")
    if not product_type:
        raise ValueError("product_type is required. e.g. '300'")

    async with kis_client() as client:
        token = await get_access_token(client)
        response = await client.get(
            f"{TrIdManager.get_domain('stock_basic_info')}{STOCK_BASIC_INFO_PATH}",
            headers=kis_headers(token, TrIdManager.get_tr_id("stock_basic_info")),
            params={
                "PRDT_TYPE_CD": product_type,
                "PDNO": symbol,
            },
        )
        return response_json(response, "Failed to get stock basic info")


@mcp.tool(
    name="order-overseas-stock",
    description="Order overseas stock (buy/sell) from Korea Investment & Securities",
)
async def order_overseas_stock(
    symbol: str,
    quantity: int,
    price: float,
    order_type: str,
    market: str,
    order_division: str | None = None,
    contact_phone: str = "",
    mgco_aptm_odno: str = "",
    order_server_division: str = "0",
):
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

    return await call_kis_api(
        "overseas_stock",
        "order",
        {
            "ctac_tlno": contact_phone,
            "mgco_aptm_odno": mgco_aptm_odno,
            "ord_dv": order_type,
            "ord_dvsn": order_division or ("00" if price > 0 else "01"),
            "ord_qty": str(quantity),
            "ord_svr_dvsn_cd": order_server_division,
            "ovrs_excg_cd": market,
            "ovrs_ord_unpr": str(price),
            "pdno": symbol,
        },
    )

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
    quote_exchange = OVERSEAS_QUOTE_EXCHANGE_CODES.get(market.upper(), market.upper())
    async with kis_client() as client:
        token = await get_access_token(client)
        
        response = await client.get(
            f"{DOMAIN}{OVERSEAS_STOCK_PRICE_PATH}",
            headers=kis_headers(token, "HHDFS00000300"),
            params={
                "AUTH": "",
                "EXCD": quote_exchange,
                "SYMB": symbol
            }
        )
        return response_json(response, "Failed to get overseas stock price")

if __name__ == "__main__":
    main()
