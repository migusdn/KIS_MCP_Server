[![MseeP.ai Security Assessment Badge](https://mseep.net/pr/migusdn-kis-mcp-server-badge.png)](https://mseep.ai/app/migusdn-kis-mcp-server)

# 한국투자증권 REST API MCP (Model Context Protocol)

[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Verified on MseeP](https://mseep.ai/badge.svg)](https://mseep.ai/app/51ce86bd-d78d-48da-8227-1e5cf29157d5)

<a href="https://glama.ai/mcp/servers/@migusdn/KIS_MCP_Server">
  <img width="380" height="200" src="https://glama.ai/mcp/servers/@migusdn/KIS_MCP_Server/badge" alt="KIS REST API Server MCP server" />
</a>

한국투자증권(KIS)의 REST API를 사용하여 주식 거래 및 시세 정보를 조회하는 MCP(Model Context Protocol) 서버입니다. 국내 및 해외 주식 거래, 시세 조회, 계좌 관리 등 다양한 금융 거래 기능을 제공합니다.

## ✨ 주요 기능

- 🇰🇷 **국내 주식 거래**
  - 실시간 현재가 조회
  - 매수/매도 주문
  - 잔고 조회
  - 호가 정보 조회
  - 주문 내역 조회

- 🌏 **해외 주식 거래**
  - 미국, 일본, 중국, 홍콩, 베트남 등 주요 시장 지원
  - 실시간 현재가 조회
  - 매수/매도 주문

- ⚡ **특징**
  - 비동기 처리로 빠른 응답
  - 실시간 시세 및 체결 정보
  - 안정적인 에러 처리
  - 확장 가능한 설계

## ⚠️ 주의사항

이 프로젝트는 아직 개발 중인 미완성 프로젝트입니다. 실제 투자에 사용하기 전에 충분한 테스트를 거치시기 바랍니다.

* 본 프로젝트를 사용하여 발생하는 모든 손실과 책임은 전적으로 사용자에게 있습니다.
* API 사용 시 한국투자증권의 이용약관을 준수해야 합니다.
* 실제 계좌 사용 시 주의가 필요하며, 모의투자 계좌로 충분한 테스트를 권장합니다.
* API 호출 제한과 관련된 제약사항을 반드시 확인하시기 바랍니다.

## Requirements

* Python >= 3.13
* uv (Python packaging tool)

## Installation

```bash
# 1. Install uv if not already installed
pip install uv

# 2. Create and activate virtual environment
uv venv
source .venv/bin/activate  # Linux/MacOS
# or
.venv\\Scripts\\activate  # Windows

# 3. Install dependencies
uv pip install -e .

mcp install server.py \
    -v KIS_APP_KEY={KIS_APP_KEY} \
    -v KIS_APP_SECRET={KIS_APP_SECRET} \
    -v KIS_ACCOUNT_TYPE={KIS_ACCOUNT_TYPE} \
    -v KIS_CANO={KIS_CANO}
```

### MCP Server Configuration

You can also configure the MCP server using a JSON configuration file. Create a file named `mcp-config.json` with the following content (replace the paths and environment variables with your own):

```json
{
  "mcpServers": {
    "KIS MCP Server": {
      "command": "/opt/homebrew/bin/uv",
      "args": [
        "run",
        "--with",
        "httpx",
        "--with",
        "mcp[cli]",
        "--with",
        "xmltodict",
        "mcp",
        "run",
        "/path/to/your/project/server.py"
      ],
      "env": {
        "KIS_APP_KEY": "your_app_key",
        "KIS_APP_SECRET": "your_secret_key",
        "KIS_ACCOUNT_TYPE": "VIRTUAL",
        "KIS_CANO": "your_account_number"
      }
    }
  }
}
```

This configuration can be used with MCP-compatible tools and IDEs to run the server with the specified dependencies and environment variables.

## Functions

### Domestic Stock Trading

* **inquery_stock_price** - 주식 현재가 조회
  * `symbol`: 종목코드 (예: "005930") (string, required)
  * Returns: 현재가, 전일대비, 등락률, 거래량 등

* **order_stock** - 주식 매수/매도 주문
  * `symbol`: 종목코드 (string, required)
  * `quantity`: 주문수량 (number, required)
  * `price`: 주문가격 (0: 시장가) (number, required)
  * `order_type`: 주문유형 ("buy" 또는 "sell") (string, required)

* **inquery_balance** - 계좌 잔고 조회
  * Returns: 보유종목, 평가금액, 손익현황 등

* **inquery_order_list** - 일별 주문 내역 조회
  * `start_date`: 조회 시작일 (YYYYMMDD) (string, required)
  * `end_date`: 조회 종료일 (YYYYMMDD) (string, required)

* **inquery_order_detail** - 주문 상세 내역 조회
  * `order_no`: 주문번호 (string, required)
  * `order_date`: 주문일자 (YYYYMMDD) (string, required)

* **inquery_stock_ask** - 호가 정보 조회
  * `symbol`: 종목코드 (string, required)
  * Returns: 매도/매수 호가, 호가수량 등

### Overseas Stock Trading

* **order_overseas_stock** - 해외 주식 매수/매도 주문
  * `symbol`: 종목코드 (예: "AAPL") (string, required)
  * `quantity`: 주문수량 (number, required)
  * `price`: 주문가격 (number, required)
  * `order_type`: 주문유형 ("buy" 또는 "sell") (string, required)
  * `market`: 시장코드 (string, required)
    * "NASD": 나스닥
    * "NYSE": 뉴욕
    * "AMEX": 아멕스
    * "SEHK": 홍콩
    * "SHAA": 중국상해
    * "SZAA": 중국심천
    * "TKSE": 일본
    * "HASE": 베트남 하노이
    * "VNSE": 베트남 호치민

* **inquery_overseas_stock_price** - 해외 주식 현재가 조회
  * `symbol`: 종목코드 (string, required)
  * `market`: 시장코드 (string, required)

## Resources

### Configuration

환경 변수를 통해 API 키와 계좌 정보를 설정합니다:

* `KIS_APP_KEY`: 한국투자증권 앱키
* `KIS_APP_SECRET`: 한국투자증권 시크릿키
* `KIS_ACCOUNT_TYPE`: 계좌 타입 ("REAL" 또는 "VIRTUAL")
* `KIS_CANO`: 계좌번호

### Trading Hours

국내 주식:
* 정규장: 09:00 ~ 15:30
* 시간외 단일가: 15:40 ~ 16:00

해외 주식:
* 미국(나스닥/뉴욕): 22:30 ~ 05:00 (한국시간)
* 일본: 09:00 ~ 15:10
* 중국: 10:30 ~ 16:00
* 홍콩: 10:30 ~ 16:00
* 베트남: 11:15 ~ 16:15

## Error Handling

API 호출 시 발생할 수 있는 주요 에러:

* 인증 오류: API 키 또는 시크릿키가 잘못된 경우
* 잔고 부족: 주문 금액이 계좌 잔고보다 큰 경우
* 시간 제한: 거래 시간이 아닌 경우
* 주문 제한: 주문 수량이나 금액이 제한을 초과한 경우

## About

* 확장 가능한 설계
* 비동기 처리로 빠른 응답
* 실시간 시세 및 체결 정보
* 안정적인 에러 처리

## License

MIT License