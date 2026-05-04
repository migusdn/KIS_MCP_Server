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
        self.responses = list(response) if isinstance(response, list) else [response]
        self.calls = []

    def _next_response(self):
        if len(self.responses) > 1:
            return self.responses.pop(0)
        return self.responses[0]

    async def get(self, url, headers=None, params=None):
        self.calls.append({"method": "GET", "url": url, "headers": headers, "params": params})
        return self._next_response()

    async def post(self, url, headers=None, json=None, timeout=None):
        self.calls.append({"method": "POST", "url": url, "headers": headers, "json": json, "timeout": timeout})
        return self._next_response()


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
    def test_api_catalog_loads_all_collected_specs(self):
        catalog = server.load_kis_api_catalog()

        self.assertEqual(catalog["total_apis"], 166)
        self.assertEqual(catalog["groups"]["domestic_stock"]["count"], 74)
        self.assertEqual(catalog["groups"]["overseas_stock"]["count"], 34)
        self.assertIn("sample implementation code", catalog["source"]["excluded"])

    async def test_get_api_spec_returns_interface_metadata_only(self):
        spec = await server.get_kis_api_spec("domestic_stock", "inquire_price")

        self.assertEqual(spec["path"], "/uapi/domestic-stock/v1/quotations/inquire-price")
        self.assertEqual(spec["tr_ids"], ["FHKST01010100"])
        self.assertEqual(
            [param["wire_name"] for param in spec["params"]],
            ["FID_COND_MRKT_DIV_CODE", "FID_INPUT_ISCD"],
        )
        self.assertNotIn("description", json.dumps(spec, ensure_ascii=False).lower())

    async def test_generic_call_maps_lowercase_params_to_wire_keys(self):
        env = {
            "KIS_APP_KEY": "app",
            "KIS_APP_SECRET": "secret",
            "KIS_ACCOUNT_TYPE": "REAL",
        }
        client = StubClient(StubResponse({"output": {"stck_prpr": "70000"}}))

        with patch.dict(os.environ, env, clear=True), \
             patch.object(server, "get_http_client", AsyncMock(return_value=client)), \
             patch.object(server, "get_access_token", AsyncMock(return_value="token")):
            result = await server.call_kis_api(
                "domestic_stock",
                "inquire_price",
                {
                    "fid_cond_mrkt_div_code": "J",
                    "fid_input_iscd": "005930",
                },
            )

        self.assertEqual(result["output"]["stck_prpr"], "70000")
        self.assertEqual(client.calls[0]["method"], "GET")
        self.assertTrue(client.calls[0]["url"].endswith("/uapi/domestic-stock/v1/quotations/inquire-price"))
        self.assertEqual(client.calls[0]["headers"]["tr_id"], "FHKST01010100")
        self.assertEqual(client.calls[0]["params"]["FID_COND_MRKT_DIV_CODE"], "J")
        self.assertEqual(client.calls[0]["params"]["FID_INPUT_ISCD"], "005930")

    async def test_generic_call_fills_account_and_selects_virtual_trid(self):
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
            result = await server.call_kis_api(
                "domestic_stock",
                "inquire_balance",
                {
                    "afhr_flpr_yn": "N",
                    "fncg_amt_auto_rdpt_yn": "N",
                    "fund_sttl_icld_yn": "N",
                    "inqr_dvsn": "01",
                    "prcs_dvsn": "00",
                    "unpr_dvsn": "01",
                },
            )

        self.assertEqual(result, {"ok": True})
        self.assertTrue(client.calls[0]["url"].startswith(server.VIRTUAL_DOMAIN))
        self.assertEqual(client.calls[0]["headers"]["tr_id"], "VTTC8434R")
        self.assertEqual(client.calls[0]["params"]["CANO"], "12345678")
        self.assertEqual(client.calls[0]["params"]["ACNT_PRDT_CD"], "22")

    async def test_generic_post_requires_explicit_trid_when_ambiguous(self):
        with patch.dict(
            os.environ,
            {"KIS_ACCOUNT_TYPE": "REAL", "KIS_CANO": "12345678", "KIS_ACNT_PRDT_CD": "01"},
            clear=True,
        ):
            with self.assertRaisesRegex(ValueError, "Pass tr_id explicitly"):
                await server.call_kis_api(
                    "domestic_stock",
                    "order_cash",
                    {
                        "excg_id_dvsn_cd": "KRX",
                        "ord_dv": "buy",
                        "ord_dvsn": "00",
                        "ord_qty": "1",
                        "ord_unpr": "70000",
                        "pdno": "005930",
                    },
                )

    async def test_generic_post_uses_hashkey_and_json_body(self):
        env = {
            "KIS_APP_KEY": "app",
            "KIS_APP_SECRET": "secret",
            "KIS_ACCOUNT_TYPE": "REAL",
            "KIS_CANO": "12345678",
            "KIS_ACNT_PRDT_CD": "01",
        }
        client = StubClient(StubResponse({"rt_cd": "0"}))

        with patch.dict(os.environ, env, clear=True), \
             patch.object(server, "get_http_client", AsyncMock(return_value=client)), \
             patch.object(server, "get_access_token", AsyncMock(return_value="token")), \
             patch.object(server, "get_hashkey", AsyncMock(return_value="hash")):
            result = await server.call_kis_api(
                "domestic_stock",
                "order_cash",
                {
                    "excg_id_dvsn_cd": "KRX",
                    "ord_dv": "buy",
                    "ord_dvsn": "00",
                    "ord_qty": "1",
                    "ord_unpr": "70000",
                    "pdno": "005930",
                },
                tr_id="TTTC0012U",
            )

        self.assertEqual(result, {"rt_cd": "0"})
        self.assertEqual(client.calls[0]["method"], "POST")
        self.assertEqual(client.calls[0]["headers"]["tr_id"], "TTTC0012U")
        self.assertEqual(client.calls[0]["headers"]["hashkey"], "hash")
        self.assertEqual(client.calls[0]["json"]["CANO"], "12345678")
        self.assertEqual(client.calls[0]["json"]["PDNO"], "005930")

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

    async def test_stock_market_uses_catalog_index_endpoint(self):
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

    async def test_stock_basic_info_uses_catalog_search_endpoint(self):
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
