[![MseeP.ai Security Assessment Badge](https://mseep.net/pr/migusdn-kis-mcp-server-badge.png)](https://mseep.ai/app/migusdn-kis-mcp-server)

# 한국투자증권 REST API MCP (Model Context Protocol)

[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Verified on MseeP](https://mseep.ai/badge.svg)](https://mseep.ai/app/51ce86bd-d78d-48da-8227-1e5cf29157d5)

<a href="https://glama.ai/mcp/servers/@migusdn/KIS_MCP_Server">
  <img width="380" height="200" src="https://glama.ai/mcp/servers/@migusdn/KIS_MCP_Server/badge" alt="KIS REST API Server MCP server" />
</a>

한국투자증권(KIS) REST API를 MCP 도구로 호출하는 서버입니다. 국내/해외 주식 조회, 계좌 조회, 주문 관련 API를 카탈로그 기반 범용 도구와 자주 쓰는 편의 도구로 제공합니다.

## 주요 기능

- **API 카탈로그 기반 호출**
  - 8개 그룹, 166개 REST API 제공
  - API 그룹/ID, 경로, HTTP 메서드, TR_ID 후보, 요청 파라미터 확인
  - 파라미터별 한글 라벨, 입력 가이드, 예시값, 주요 코드값 제공
  - 전체 목록: [`API_CATALOG.md`](API_CATALOG.md)
- **국내주식**
  - 현재가, 기간/일별 시세, 호가, 업종지수, 기본정보 조회
  - 잔고, 투자계좌 자산현황, 매수가능금액, 매도가능수량 조회
  - 주문/주문내역/정정취소 가능 주문 조회
- **해외주식**
  - 미국, 일본, 중국, 홍콩, 베트남 시장 코드 지원
  - 현재가, 잔고, 체결기준 현재잔고, 통화별 증거금, 매수가능금액 조회
  - 시장/매수매도 방향에 따른 주문 TR_ID 자동 선택
- **실행/운영**
  - `stdio`, `sse`, `streamable-http` transport 지원
  - `.env` 또는 명령줄 인자 기반 설정
  - 계좌번호, 계좌상품코드, 인증값 자동 보완
  - 앱키와 계좌 타입 기준 토큰 캐시
  - 알 수 없는 요청 파라미터 기본 거부
  - 주문/정정/취소 API 기본 차단

## 안전 기본값

주문/정정/취소처럼 계좌 상태를 바꾸는 API는 기본적으로 차단됩니다.

```bash
KIS_ENABLE_TRADING=true
```

위 값을 명시적으로 설정한 경우에만 상태 변경 API가 실행됩니다. 조회 API만 사용하는 경우에는 설정하지 마세요.

## 요구 사항

- Python >= 3.13
- uv

## 설치

설치는 [`INSTALL.md`](INSTALL.md)를 기준으로 진행하세요. LLM이나 MCP 클라이언트가 설정할 때도 이 파일을 우선 읽으면 됩니다.

`INSTALL.md`에는 다음 내용이 포함되어 있습니다.

- `uv` 기반 의존성 설치
- `.env` 생성과 `KIS_APP_KEY`, `KIS_APP_SECRET`, `KIS_CANO`, `KIS_ACNT_PRDT_CD` 설정
- Codex CLI, Claude Code, Claude Desktop, 일반 MCP 클라이언트 등록 예시
- 컨텍스트 절약용 `KIS_MCP_TOOLSET=catalog` 설정
- 잔고, 매수가능금액, 현재가 조회용 `call-kis-api` 예시

빠른 로컬 준비:

```bash
pip install uv
uv sync
cp .env.example .env
chmod 600 .env
```

그 다음 `.env`에 아래 값을 설정합니다. 자세한 값 설명과 클라이언트별 등록 명령은 [`INSTALL.md`](INSTALL.md)를 참고하세요.

```bash
KIS_APP_KEY="발급받은 앱키"
KIS_APP_SECRET="발급받은 시크릿키"
KIS_ACCOUNT_TYPE="REAL"   # REAL 또는 VIRTUAL
KIS_CANO="계좌번호 앞 8자리"
KIS_ACNT_PRDT_CD="01"
KIS_MCP_TOOLSET="catalog"
```

## 실행

```bash
# stdio, 로컬 MCP 클라이언트 권장
uv run python server.py
```

명령줄 인자로도 설정할 수 있습니다.

```bash
uv run python server.py \
  --app-key "앱키" \
  --app-secret "시크릿키" \
  --account-type "REAL" \
  --cano "계좌번호" \
  --acnt-prdt-cd "01"
```

Transport 선택:

```bash
MCP_TYPE=stdio uv run python server.py
MCP_TYPE=streamable-http MCP_HOST=127.0.0.1 MCP_PORT=8000 MCP_PATH=/mcp uv run python server.py
MCP_TYPE=sse MCP_HOST=127.0.0.1 MCP_PORT=8000 MCP_PATH=/sse uv run python server.py
```

MCP 클라이언트 등록 예시:

아래는 일반 MCP 클라이언트용 최소 예시입니다. Codex CLI, Claude Code, Claude Desktop 명령은 [`INSTALL.md`](INSTALL.md)를 사용하세요.

```json
{
  "mcpServers": {
    "kis-mcp-server": {
      "command": "uv",
      "args": ["run", "python", "server.py"],
      "cwd": "<project-root>",
      "env": {
        "KIS_MCP_TOOLSET": "catalog",
        "KIS_MCP_LOG_LEVEL": "WARNING"
      }
    }
  }
}
```

## MCP 도구 구성

### 카탈로그 도구

| 도구 | 설명 |
|---|---|
| `list-kis-api-specs` | API 그룹/검색어 기준 목록 조회 |
| `get-kis-api-spec` | 단일 API의 경로, TR_ID 후보, 파라미터 확인 |
| `call-kis-api` | `group`, `api_type`, `params`로 카탈로그 API 호출 |

`list-kis-api-specs`는 필수 파라미터의 라벨, 예시값, 주요 코드값을 함께 반환합니다.
`get-kis-api-spec`는 전체 파라미터의 `label`, `guide`, `examples`, `values`, `default`, `auto_fill` 정보를 반환하므로 LLM이 호출에 필요한 입력 형태를 바로 확인할 수 있습니다.

`call-kis-api`는 다음 처리를 공통으로 수행합니다.

- 환경변수 기반 계좌번호/계좌상품코드 자동 입력
- 인증 토큰 발급 및 캐시
- GET/POST 요청 구성
- 다중 TR_ID 중 자동 판별 가능한 주문 TR_ID 선택
- 상태 변경 API 안전 게이트 적용
- 카탈로그에 없는 파라미터 기본 거부

### 편의 도구

자주 쓰는 국내/해외 주식 기능은 별도 MCP 도구로도 제공합니다.

| 도구 | 설명 |
|---|---|
| `inquery-stock-price` | 국내주식 현재가 조회 |
| `inquery-balance` | 국내주식 잔고 조회 |
| `inquery-order-list` | 국내주식 일별 주문/체결 조회 |
| `inquery-order-detail` | 국내주식 주문 상세 조회 |
| `inquery-stock-info` | 국내주식 일별 시세 조회 |
| `inquery-stock-history` | 국내주식 기간 시세 조회 |
| `inquery-stock-ask` | 국내주식 호가 조회 |
| `inquery-stock-market` | 국내 업종/지수 현재가 조회 |
| `inquery-stock-basic-info` | 국내주식 기본정보 조회 |
| `inquery-overseas-stock-price` | 해외주식 현재가 조회 |
| `order-stock` | 국내주식 매수/매도 주문 |
| `order-overseas-stock` | 해외주식 매수/매도 주문 |

주문 도구도 `KIS_ENABLE_TRADING=true`가 없으면 실행되지 않습니다.

### 도구 로드 최적화

MCP 클라이언트는 서버 연결 시 도구 이름, 설명, 입력 스키마를 컨텍스트에 올립니다. 편의 도구를 많이 노출할수록 대화 시작 시점의 컨텍스트 사용량이 늘어나므로, 필요한 경우 카탈로그 도구 3개만 노출하는 경량 모드를 사용할 수 있습니다.

```bash
KIS_MCP_TOOLSET=catalog uv run python server.py
```

| 값 | 노출 도구 수 | 노출 도구 | 용도 |
|---|---:|---|---|
| `full` | 15개 | 카탈로그 도구 + 편의 도구 전체 | 기존 동작과 호환 |
| `catalog` | 3개 | `list-kis-api-specs`, `get-kis-api-spec`, `call-kis-api` | 낮은 컨텍스트 사용량 |

`catalog` 모드는 MCP 도구 스키마 로드량을 줄이기 위한 모드입니다. 편의 도구는 숨기지만, 166개 API는 그대로 `call-kis-api`로 호출할 수 있습니다. 필요한 API는 `list-kis-api-specs`로 찾고, 필요한 상세 파라미터는 `get-kis-api-spec`로 그때그때 조회하면 됩니다.

권장 사용 흐름:

1. `list-kis-api-specs`로 API를 검색합니다.
2. `get-kis-api-spec`로 필수 파라미터, 예시값, 코드값을 확인합니다.
3. `call-kis-api`로 실제 API를 호출합니다.

MCP 클라이언트 설정에서도 환경변수만 추가하면 됩니다.

```json
{
  "env": {
    "KIS_MCP_TOOLSET": "catalog"
  }
}
```

자주 쓰는 편의 도구를 도구 목록에 직접 노출하고 싶으면 기본값인 `full`을 사용하세요.

## `call-kis-api` 예시

국내주식 현재가:

```json
{
  "group": "domestic_stock",
  "api_type": "inquire_price",
  "params": {
    "fid_cond_mrkt_div_code": "J",
    "fid_input_iscd": "005930"
  }
}
```

해외주식 잔고:

```json
{
  "group": "overseas_stock",
  "api_type": "inquire_balance",
  "params": {
    "ovrs_excg_cd": "NASD",
    "tr_crcy_cd": "USD"
  }
}
```

해외주식 체결기준 현재잔고:

```json
{
  "group": "overseas_stock",
  "api_type": "inquire_present_balance",
  "params": {
    "wcrc_frcr_dvsn_cd": "01",
    "natn_cd": "000",
    "tr_mket_cd": "00",
    "inqr_dvsn_cd": "00"
  }
}
```

해외주식 매수가능금액:

```json
{
  "group": "overseas_stock",
  "api_type": "inquire_psamount",
  "params": {
    "ovrs_excg_cd": "NASD",
    "ovrs_ord_unpr": "1",
    "item_cd": "QQQ"
  }
}
```

## 주요 API 그룹

| 그룹 | 설명 | API 수 |
|---|---|---:|
| `auth` | 인증 | 2 |
| `domestic_stock` | 국내주식 | 74 |
| `overseas_stock` | 해외주식 | 34 |
| `domestic_bond` | 국내채권 | 14 |
| `domestic_futureoption` | 국내선물옵션 | 20 |
| `overseas_futureoption` | 해외선물옵션 | 19 |
| `elw` | ELW | 1 |
| `etfetn` | ETF/ETN | 2 |

전체 API ID, 경로, TR_ID, 필수 파라미터 가이드는 [`API_CATALOG.md`](API_CATALOG.md)에 정리되어 있습니다.

## 환경 변수

| 이름 | 설명 | 기본값 |
|---|---|---|
| `KIS_APP_KEY` | KIS 앱키 | - |
| `KIS_APP_SECRET` | KIS 시크릿키 | - |
| `KIS_ACCOUNT_TYPE` | `REAL` 또는 `VIRTUAL` | - |
| `KIS_CANO` | 계좌번호 앞 8자리 | - |
| `KIS_ACNT_PRDT_CD` | 계좌상품코드 | `01` |
| `KIS_TOKEN_FILE` | 토큰 캐시 파일 | `token.json` |
| `KIS_ENABLE_TRADING` | 주문/정정/취소 API 활성화 | 비활성 |
| `KIS_MCP_TOOLSET` | MCP 도구 노출 범위 (`full`, `catalog`) | `full` |
| `KIS_MCP_LOG_LEVEL` | 로그 레벨 | `INFO` |
| `MCP_TYPE` | `stdio`, `sse`, `streamable-http` | `stdio` |
| `MCP_HOST` | HTTP/SSE host | `127.0.0.1` |
| `MCP_PORT` | HTTP/SSE port | `8000` |
| `MCP_PATH` | HTTP/SSE path | `/mcp` |

## 개발/검증

```bash
uv run python -m compileall main.py server.py example.py tests
uv run python -m unittest discover -v
git diff --check
```

## 라이선스

MIT
