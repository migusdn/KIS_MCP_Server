import json
import os
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import AsyncMock, patch

import server


class StubResponse:
    def __init__(self, payload, status_code=200, text="OK"):
        self._payload = payload
        self.status_code = status_code
        self.text = text

    def json(self):
        return self._payload


class StubClient:
    def __init__(self, response):
        self.response = response
        self.calls = []

    async def get(self, url, headers=None, params=None):
        self.calls.append({"method": "GET", "url": url, "headers": headers, "params": params})
        return self.response

    async def post(self, url, headers=None, json=None, timeout=None):
        self.calls.append({"method": "POST", "url": url, "headers": headers, "json": json, "timeout": timeout})
        return self.response


class RuntimeConfigTests(unittest.TestCase):
    def test_cli_arguments_apply_environment_and_transport(self):
        with patch.dict(os.environ, {}, clear=True):
            cfg = server.configure_runtime([
                "--transport", "streamable-http",
                "--host", "0.0.0.0",
                "--port", "9000",
                "--path", "/kis",
                "--app-key", "app",
                "--app-secret", "secret",
                "--account-type", "virtual",
                "--cano", "12345678",
                "--acnt-prdt-cd", "22",
            ])

            self.assertEqual(cfg.transport, "streamable-http")
            self.assertEqual(cfg.host, "0.0.0.0")
            self.assertEqual(cfg.port, 9000)
            self.assertEqual(cfg.path, "/kis")
            self.assertEqual(os.environ["KIS_ACCOUNT_TYPE"], "VIRTUAL")
            self.assertEqual(server.get_account_product_code(), "22")

    def test_validation_reports_missing_credentials(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(ValueError, "KIS_APP_KEY"):
                server.validate_kis_credentials(require_account=True)

    def test_token_cache_ignores_other_app_key(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            token_file = Path(tmpdir) / "token.json"
            token_file.write_text(json.dumps({
                "token": "cached",
                "expires_at": (datetime.now() + timedelta(hours=1)).isoformat(),
                "app_key": "old-app",
            }))
            with patch.dict(os.environ, {"KIS_TOKEN_FILE": str(token_file), "KIS_APP_KEY": "new-app"}, clear=True):
                self.assertEqual(server.load_token(), (None, None))


class KisRequestTests(unittest.IsolatedAsyncioTestCase):
    async def test_balance_request_uses_configured_account_product_code(self):
        env = {
            "KIS_APP_KEY": "app",
            "KIS_APP_SECRET": "secret",
            "KIS_ACCOUNT_TYPE": "VIRTUAL",
            "KIS_CANO": "12345678",
            "KIS_ACNT_PRDT_CD": "22",
        }
        client = StubClient(StubResponse({"ok": True}))

        with patch.dict(os.environ, env, clear=True), \
             patch.object(server, "get_http_client", AsyncMock(return_value=client)), \
             patch.object(server, "get_access_token", AsyncMock(return_value="token")):
            result = await server.inquery_balance()

        self.assertEqual(result, {"ok": True})
        self.assertEqual(client.calls[0]["params"]["CANO"], "12345678")
        self.assertEqual(client.calls[0]["params"]["ACNT_PRDT_CD"], "22")
        self.assertEqual(client.calls[0]["headers"]["tr_id"], "VTTC8434R")

    async def test_stock_market_uses_official_index_endpoint(self):
        env = {
            "KIS_APP_KEY": "app",
            "KIS_APP_SECRET": "secret",
            "KIS_ACCOUNT_TYPE": "REAL",
        }
        client = StubClient(StubResponse({"output": [{"bstp_nmix_prpr": "3000.00"}]}))

        with patch.dict(os.environ, env, clear=True), \
             patch.object(server, "get_http_client", AsyncMock(return_value=client)), \
             patch.object(server, "get_access_token", AsyncMock(return_value="token")):
            result = await server.inquery_stock_market(index_code="0001")

        self.assertEqual(result["output"][0]["bstp_nmix_prpr"], "3000.00")
        self.assertTrue(client.calls[0]["url"].endswith(server.INDEX_PRICE_PATH))
        self.assertEqual(client.calls[0]["params"]["FID_COND_MRKT_DIV_CODE"], "U")
        self.assertEqual(client.calls[0]["params"]["FID_INPUT_ISCD"], "0001")
        self.assertEqual(client.calls[0]["headers"]["tr_id"], "FHPUP02100000")

    async def test_stock_basic_info_uses_official_search_endpoint(self):
        env = {
            "KIS_APP_KEY": "app",
            "KIS_APP_SECRET": "secret",
            "KIS_ACCOUNT_TYPE": "REAL",
        }
        client = StubClient(StubResponse({"output": [{"prdt_abrv_name": "삼성전자"}]}))

        with patch.dict(os.environ, env, clear=True), \
             patch.object(server, "get_http_client", AsyncMock(return_value=client)), \
             patch.object(server, "get_access_token", AsyncMock(return_value="token")):
            result = await server.inquery_stock_basic_info("005930")

        self.assertEqual(result["output"][0]["prdt_abrv_name"], "삼성전자")
        self.assertTrue(client.calls[0]["url"].endswith(server.STOCK_BASIC_INFO_PATH))
        self.assertEqual(client.calls[0]["params"]["PRDT_TYPE_CD"], "300")
        self.assertEqual(client.calls[0]["params"]["PDNO"], "005930")
        self.assertEqual(client.calls[0]["headers"]["tr_id"], "CTPF1002R")

    async def test_access_token_saves_app_scoped_cache(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            token_file = Path(tmpdir) / "token.json"
            env = {
                "KIS_APP_KEY": "app",
                "KIS_APP_SECRET": "secret",
                "KIS_ACCOUNT_TYPE": "REAL",
                "KIS_TOKEN_FILE": str(token_file),
            }
            client = StubClient(StubResponse({"access_token": "new-token"}))
            server._token_cache.update({"token": None, "expires_at": None, "app_key": None})

            with patch.dict(os.environ, env, clear=True):
                token = await server.get_access_token(client)

            self.assertEqual(token, "new-token")
            cached = json.loads(token_file.read_text())
            self.assertEqual(cached["token"], "new-token")
            self.assertEqual(cached["app_key"], "app")
            self.assertEqual(client.calls[0]["timeout"], 30.0)


if __name__ == "__main__":
    unittest.main()
