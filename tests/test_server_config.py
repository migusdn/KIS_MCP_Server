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
                "--toolset", "catalog",
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
            self.assertEqual(cfg.toolset, "catalog")
            self.assertEqual(os.environ["KIS_ACCOUNT_TYPE"], "VIRTUAL")
            self.assertEqual(server.get_account_product_code(), "22")

    def test_catalog_toolset_disables_convenience_tools(self):
        disabled = server._disabled_tool_names("catalog")

        self.assertIn("inquery-balance", disabled)
        self.assertIn("order-overseas-stock", disabled)
        self.assertNotIn("call-kis-api", disabled)
        self.assertEqual(server._disabled_tool_names("full"), set())

    def test_toolset_can_be_configured_from_environment(self):
        with patch.dict(os.environ, {"KIS_MCP_TOOLSET": "catalog"}, clear=True):
            cfg = server.configure_runtime([])

        self.assertEqual(cfg.toolset, "catalog")

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

    def test_token_cache_ignores_other_account_scope(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            token_file = Path(tmpdir) / "token.json"
            token_file.write_text(json.dumps({
                "token": "cached",
                "expires_at": (datetime.now() + timedelta(hours=1)).isoformat(),
                "app_key": "app",
                "token_scope": "real",
            }))
            env = {
                "KIS_TOKEN_FILE": str(token_file),
                "KIS_APP_KEY": "app",
                "KIS_ACCOUNT_TYPE": "VIRTUAL",
            }
            with patch.dict(os.environ, env, clear=True):
                self.assertEqual(server.load_token(), (None, None))


class KisRequestTests(unittest.IsolatedAsyncioTestCase):
    def test_api_catalog_loads_all_collected_specs(self):
        catalog = server.load_kis_api_catalog()

        self.assertEqual(catalog["total_apis"], 166)
        self.assertEqual(catalog["groups"]["domestic_stock"]["count"], 74)
        self.assertEqual(catalog["groups"]["overseas_stock"]["count"], 34)
        self.assertNotIn("source", catalog)

    async def test_get_api_spec_returns_interface_metadata_only(self):
        spec = await server.get_kis_api_spec("domestic_stock", "inquire_price")

        self.assertEqual(spec["path"], "/uapi/domestic-stock/v1/quotations/inquire-price")
        self.assertEqual(spec["tr_ids"], ["FHKST01010100"])
        self.assertEqual(
            [param["wire_name"] for param in spec["params"]],
            ["FID_COND_MRKT_DIV_CODE", "FID_INPUT_ISCD"],
        )
        params_by_name = {param["name"]: param for param in spec["params"]}
        self.assertEqual(params_by_name["fid_cond_mrkt_div_code"]["label"], "시장 분류 코드")
        self.assertIn("J", params_by_name["fid_cond_mrkt_div_code"]["values"])
        self.assertIn("005930", params_by_name["fid_input_iscd"]["examples"])
        self.assertNotIn("description", json.dumps(spec, ensure_ascii=False).lower())

    async def test_overseas_balance_spec_includes_continuation_keys_from_examples(self):
        spec = await server.get_kis_api_spec("overseas_stock", "inquire_balance")

        params_by_wire = {param["wire_name"]: param for param in spec["params"]}

        self.assertEqual(params_by_wire["CTX_AREA_FK200"]["default"], "")
        self.assertEqual(params_by_wire["CTX_AREA_NK200"]["default"], "")
        self.assertFalse(params_by_wire["CTX_AREA_FK200"]["required"])
        self.assertFalse(params_by_wire["CTX_AREA_NK200"]["required"])
        self.assertEqual(params_by_wire["OVRS_EXCG_CD"]["label"], "해외거래소 코드")
        self.assertIn("NASD", params_by_wire["OVRS_EXCG_CD"]["values"])
        self.assertIn("USD", params_by_wire["TR_CRCY_CD"]["examples"])

    async def test_api_list_searches_parameter_guides(self):
        result = await server.list_kis_api_specs(group="overseas_stock", query="나스닥", limit=10)

        self.assertGreater(result["matched"], 0)
        first = result["items"][0]
        self.assertIn("required_param_guides", first)
        self.assertIn("guide", first["required_param_guides"][0])

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

    async def test_generic_call_rejects_unknown_params_by_default(self):
        with self.assertRaisesRegex(ValueError, "Unknown params"):
            await server.call_kis_api(
                "domestic_stock",
                "inquire_price",
                {
                    "fid_cond_mrkt_div_code": "J",
                    "fid_input_iscd": "005930",
                    "typo_param": "bad",
                },
            )

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

    async def test_overseas_balance_defaults_required_continuation_keys(self):
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
             patch.object(server, "get_access_token", AsyncMock(return_value="token")):
            result = await server.call_kis_api(
                "overseas_stock",
                "inquire_balance",
                {
                    "ovrs_excg_cd": "NASD",
                    "tr_crcy_cd": "USD",
                },
            )

        self.assertEqual(result, {"rt_cd": "0"})
        self.assertEqual(client.calls[0]["headers"]["tr_id"], "TTTS3012R")
        self.assertEqual(client.calls[0]["params"]["OVRS_EXCG_CD"], "NASD")
        self.assertEqual(client.calls[0]["params"]["TR_CRCY_CD"], "USD")
        self.assertEqual(client.calls[0]["params"]["CTX_AREA_FK200"], "")
        self.assertEqual(client.calls[0]["params"]["CTX_AREA_NK200"], "")

    async def test_generic_post_requires_explicit_trid_when_side_is_unknown(self):
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
                        "ord_dv": "hold",
                        "ord_dvsn": "00",
                        "ord_qty": "1",
                        "ord_unpr": "70000",
                        "pdno": "005930",
                    },
                )

    async def test_generic_post_blocks_trading_when_gate_is_disabled(self):
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
             patch.object(server, "get_access_token", AsyncMock(return_value="token")):
            with self.assertRaisesRegex(PermissionError, "KIS_ENABLE_TRADING"):
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

        self.assertEqual(client.calls, [])

    async def test_generic_post_uses_hashkey_and_json_body(self):
        env = {
            "KIS_APP_KEY": "app",
            "KIS_APP_SECRET": "secret",
            "KIS_ACCOUNT_TYPE": "REAL",
            "KIS_CANO": "12345678",
            "KIS_ACNT_PRDT_CD": "01",
            "KIS_ENABLE_TRADING": "true",
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
            )

        self.assertEqual(result, {"rt_cd": "0"})
        self.assertEqual(client.calls[0]["method"], "POST")
        self.assertEqual(client.calls[0]["headers"]["tr_id"], "TTTC0012U")
        self.assertEqual(client.calls[0]["headers"]["hashkey"], "hash")
        self.assertEqual(client.calls[0]["json"]["CANO"], "12345678")
        self.assertEqual(client.calls[0]["json"]["PDNO"], "005930")

    async def test_legacy_order_stock_delegates_to_catalog_order_cash(self):
        env = {
            "KIS_APP_KEY": "app",
            "KIS_APP_SECRET": "secret",
            "KIS_ACCOUNT_TYPE": "REAL",
            "KIS_CANO": "12345678",
            "KIS_ACNT_PRDT_CD": "01",
            "KIS_ENABLE_TRADING": "true",
        }
        client = StubClient(StubResponse({"rt_cd": "0"}))

        with patch.dict(os.environ, env, clear=True), \
             patch.object(server, "get_http_client", AsyncMock(return_value=client)), \
             patch.object(server, "get_access_token", AsyncMock(return_value="token")), \
             patch.object(server, "get_hashkey", AsyncMock(return_value="hash")):
            await server.order_stock("005930", 1, 0, "buy")

        self.assertEqual(client.calls[0]["headers"]["tr_id"], "TTTC0012U")
        self.assertEqual(client.calls[0]["json"]["EXCG_ID_DVSN_CD"], "KRX")
        self.assertEqual(client.calls[0]["json"]["ORD_DVSN"], "01")

    async def test_generic_post_infers_virtual_domestic_sell_trid(self):
        env = {
            "KIS_APP_KEY": "app",
            "KIS_APP_SECRET": "secret",
            "KIS_ACCOUNT_TYPE": "VIRTUAL",
            "KIS_CANO": "12345678",
            "KIS_ACNT_PRDT_CD": "01",
            "KIS_ENABLE_TRADING": "true",
        }
        client = StubClient(StubResponse({"rt_cd": "0"}))

        with patch.dict(os.environ, env, clear=True), \
             patch.object(server, "get_http_client", AsyncMock(return_value=client)), \
             patch.object(server, "get_access_token", AsyncMock(return_value="token")), \
             patch.object(server, "get_hashkey", AsyncMock(return_value="hash")):
            await server.call_kis_api(
                "domestic_stock",
                "order_cash",
                {
                    "excg_id_dvsn_cd": "KRX",
                    "ord_dv": "sell",
                    "ord_dvsn": "00",
                    "ord_qty": "1",
                    "ord_unpr": "70000",
                    "pdno": "005930",
                },
            )

        self.assertTrue(client.calls[0]["url"].startswith(server.VIRTUAL_DOMAIN))
        self.assertEqual(client.calls[0]["headers"]["tr_id"], "VTTC0011U")

    async def test_generic_post_infers_overseas_market_and_side_trid(self):
        env = {
            "KIS_APP_KEY": "app",
            "KIS_APP_SECRET": "secret",
            "KIS_ACCOUNT_TYPE": "REAL",
            "KIS_CANO": "12345678",
            "KIS_ACNT_PRDT_CD": "01",
            "KIS_ENABLE_TRADING": "true",
        }
        client = StubClient(StubResponse({"rt_cd": "0"}))

        with patch.dict(os.environ, env, clear=True), \
             patch.object(server, "get_http_client", AsyncMock(return_value=client)), \
             patch.object(server, "get_access_token", AsyncMock(return_value="token")), \
             patch.object(server, "get_hashkey", AsyncMock(return_value="hash")):
            await server.call_kis_api(
                "overseas_stock",
                "order",
                {
                    "ctac_tlno": "",
                    "mgco_aptm_odno": "",
                    "ord_dv": "sell",
                    "ord_dvsn": "00",
                    "ord_qty": "1",
                    "ord_svr_dvsn_cd": "0",
                    "ovrs_excg_cd": "NASD",
                    "ovrs_ord_unpr": "190.5",
                    "pdno": "AAPL",
                },
            )

        self.assertEqual(client.calls[0]["headers"]["tr_id"], "TTTT1006U")
        self.assertEqual(client.calls[0]["json"]["OVRS_EXCG_CD"], "NASD")

    async def test_generic_post_infers_virtual_overseas_order_trid(self):
        env = {
            "KIS_APP_KEY": "app",
            "KIS_APP_SECRET": "secret",
            "KIS_ACCOUNT_TYPE": "VIRTUAL",
            "KIS_CANO": "12345678",
            "KIS_ACNT_PRDT_CD": "01",
            "KIS_ENABLE_TRADING": "true",
        }
        client = StubClient(StubResponse({"rt_cd": "0"}))

        with patch.dict(os.environ, env, clear=True), \
             patch.object(server, "get_http_client", AsyncMock(return_value=client)), \
             patch.object(server, "get_access_token", AsyncMock(return_value="token")), \
             patch.object(server, "get_hashkey", AsyncMock(return_value="hash")):
            await server.call_kis_api(
                "overseas_stock",
                "order",
                {
                    "ctac_tlno": "",
                    "mgco_aptm_odno": "",
                    "ord_dv": "buy",
                    "ord_dvsn": "00",
                    "ord_qty": "1",
                    "ord_svr_dvsn_cd": "0",
                    "ovrs_excg_cd": "SEHK",
                    "ovrs_ord_unpr": "50",
                    "pdno": "00700",
                },
            )

        self.assertTrue(client.calls[0]["url"].startswith(server.VIRTUAL_DOMAIN))
        self.assertEqual(client.calls[0]["headers"]["tr_id"], "VTTS1002U")

    async def test_legacy_overseas_order_uses_catalog_hashkey_and_virtual_sell_trid(self):
        env = {
            "KIS_APP_KEY": "app",
            "KIS_APP_SECRET": "secret",
            "KIS_ACCOUNT_TYPE": "VIRTUAL",
            "KIS_CANO": "12345678",
            "KIS_ACNT_PRDT_CD": "01",
            "KIS_ENABLE_TRADING": "true",
        }
        client = StubClient(StubResponse({"rt_cd": "0"}))

        with patch.dict(os.environ, env, clear=True), \
             patch.object(server, "get_http_client", AsyncMock(return_value=client)), \
             patch.object(server, "get_access_token", AsyncMock(return_value="token")), \
             patch.object(server, "get_hashkey", AsyncMock(return_value="hash")):
            await server.order_overseas_stock("AAPL", 1, 190.5, "sell", "NASD")

        self.assertTrue(client.calls[0]["url"].startswith(server.VIRTUAL_DOMAIN))
        self.assertEqual(client.calls[0]["headers"]["tr_id"], "VTTT1006U")
        self.assertEqual(client.calls[0]["headers"]["hashkey"], "hash")
        self.assertEqual(client.calls[0]["json"]["OVRS_EXCG_CD"], "NASD")

    async def test_legacy_overseas_market_order_without_division_is_rejected(self):
        env = {
            "KIS_APP_KEY": "app",
            "KIS_APP_SECRET": "secret",
            "KIS_ACCOUNT_TYPE": "VIRTUAL",
            "KIS_CANO": "12345678",
            "KIS_ACNT_PRDT_CD": "01",
            "KIS_ENABLE_TRADING": "true",
        }
        client = StubClient(StubResponse({"rt_cd": "0"}))

        with patch.dict(os.environ, env, clear=True), \
             patch.object(server, "get_http_client", AsyncMock(return_value=client)), \
             patch.object(server, "get_access_token", AsyncMock(return_value="token")), \
             patch.object(server, "get_hashkey", AsyncMock(return_value="hash")):
            with self.assertRaises(ValueError) as us_ctx:
                await server.order_overseas_stock("AAPL", 1, 0, "buy", "NASD")
            with self.assertRaises(ValueError) as hk_ctx:
                await server.order_overseas_stock("00700", 1, 0, "buy", "SEHK")

        self.assertIn("US exchanges (NASD)", str(us_ctx.exception))
        self.assertIn("SEHK", str(hk_ctx.exception))
        self.assertEqual(client.calls, [])

    async def test_legacy_overseas_order_keeps_explicit_division_with_zero_price(self):
        env = {
            "KIS_APP_KEY": "app",
            "KIS_APP_SECRET": "secret",
            "KIS_ACCOUNT_TYPE": "REAL",
            "KIS_CANO": "12345678",
            "KIS_ACNT_PRDT_CD": "01",
            "KIS_ENABLE_TRADING": "true",
        }
        client = StubClient(StubResponse({"rt_cd": "0"}))

        with patch.dict(os.environ, env, clear=True), \
             patch.object(server, "get_http_client", AsyncMock(return_value=client)), \
             patch.object(server, "get_access_token", AsyncMock(return_value="token")), \
             patch.object(server, "get_hashkey", AsyncMock(return_value="hash")):
            await server.order_overseas_stock(
                "AAPL", 1, 0, "sell", "NASD", order_division="31"
            )

        self.assertEqual(client.calls[0]["json"]["ORD_DVSN"], "31")
        self.assertEqual(client.calls[0]["json"]["OVRS_ORD_UNPR"], "0")
        self.assertEqual(client.calls[0]["headers"]["tr_id"], "TTTT1006U")

    async def test_legacy_overseas_order_rejects_explicit_limit_with_zero_price(self):
        env = {
            "KIS_APP_KEY": "app",
            "KIS_APP_SECRET": "secret",
            "KIS_ACCOUNT_TYPE": "REAL",
            "KIS_CANO": "12345678",
            "KIS_ACNT_PRDT_CD": "01",
            "KIS_ENABLE_TRADING": "true",
        }
        client = StubClient(StubResponse({"rt_cd": "0"}))

        with patch.dict(os.environ, env, clear=True), \
             patch.object(server, "get_http_client", AsyncMock(return_value=client)), \
             patch.object(server, "get_access_token", AsyncMock(return_value="token")), \
             patch.object(server, "get_hashkey", AsyncMock(return_value="hash")):
            with self.assertRaisesRegex(ValueError, "positive limit price"):
                await server.order_overseas_stock(
                    "AAPL", 1, 0, "buy", "NASD", order_division="00"
                )

        self.assertEqual(client.calls, [])

    async def test_legacy_overseas_order_rejects_virtual_market_on_close_division(self):
        env = {
            "KIS_APP_KEY": "app",
            "KIS_APP_SECRET": "secret",
            "KIS_ACCOUNT_TYPE": "VIRTUAL",
            "KIS_CANO": "12345678",
            "KIS_ACNT_PRDT_CD": "01",
            "KIS_ENABLE_TRADING": "true",
        }
        client = StubClient(StubResponse({"rt_cd": "0"}))

        with patch.dict(os.environ, env, clear=True), \
             patch.object(server, "get_http_client", AsyncMock(return_value=client)), \
             patch.object(server, "get_access_token", AsyncMock(return_value="token")), \
             patch.object(server, "get_hashkey", AsyncMock(return_value="hash")):
            with self.assertRaisesRegex(ValueError, "not supported for VIRTUAL"):
                await server.order_overseas_stock(
                    "AAPL", 1, 0, "sell", "NASD", order_division="33"
                )

        self.assertEqual(client.calls, [])

    async def test_generic_overseas_order_rejects_plain_market_division_before_network(self):
        env = {
            "KIS_APP_KEY": "app",
            "KIS_APP_SECRET": "secret",
            "KIS_ACCOUNT_TYPE": "REAL",
            "KIS_CANO": "12345678",
            "KIS_ACNT_PRDT_CD": "01",
            "KIS_ENABLE_TRADING": "true",
        }
        client = StubClient(StubResponse({"rt_cd": "0"}))

        with patch.dict(os.environ, env, clear=True), \
             patch.object(server, "get_http_client", AsyncMock(return_value=client)), \
             patch.object(server, "get_access_token", AsyncMock(return_value="token")), \
             patch.object(server, "get_hashkey", AsyncMock(return_value="hash")):
            with self.assertRaisesRegex(ValueError, "ORD_DVSN '01' is not supported"):
                await server.call_kis_api(
                    "overseas_stock",
                    "order",
                    {
                        "ctac_tlno": "",
                        "mgco_aptm_odno": "",
                        "ord_dv": "buy",
                        "ord_dvsn": "01",
                        "ord_qty": "1",
                        "ord_svr_dvsn_cd": "0",
                        "ovrs_excg_cd": "NASD",
                        "ovrs_ord_unpr": "0",
                        "pdno": "AAPL",
                    },
                )

        self.assertEqual(client.calls, [])

    async def test_overseas_order_spec_documents_supported_divisions(self):
        spec = await server.get_kis_api_spec("overseas_stock", "order")
        ord_dvsn = next(param for param in spec["params"] if param["name"] == "ord_dvsn")

        self.assertNotIn("01", ord_dvsn["values"])
        self.assertIn("31", ord_dvsn["values"])
        self.assertIn("50", ord_dvsn["values"])
        self.assertIn("일반 시장가(01)는 지원하지 않습니다", ord_dvsn["guide"])

    async def test_legacy_overseas_limit_order_defaults_to_limit_division(self):
        env = {
            "KIS_APP_KEY": "app",
            "KIS_APP_SECRET": "secret",
            "KIS_ACCOUNT_TYPE": "VIRTUAL",
            "KIS_CANO": "12345678",
            "KIS_ACNT_PRDT_CD": "01",
            "KIS_ENABLE_TRADING": "true",
        }
        client = StubClient(StubResponse({"rt_cd": "0"}))

        with patch.dict(os.environ, env, clear=True), \
             patch.object(server, "get_http_client", AsyncMock(return_value=client)), \
             patch.object(server, "get_access_token", AsyncMock(return_value="token")), \
             patch.object(server, "get_hashkey", AsyncMock(return_value="hash")):
            await server.order_overseas_stock("AAPL", 1, 212.5, "buy", "NASD")

        self.assertEqual(client.calls[0]["json"]["ORD_DVSN"], "00")
        self.assertEqual(client.calls[0]["json"]["OVRS_ORD_UNPR"], "212.5")
        self.assertEqual(client.calls[0]["headers"]["tr_id"], "VTTT1002U")

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
            server._token_cache.update({"token": None, "expires_at": None, "app_key": None, "token_scope": None})

            with patch.dict(os.environ, env, clear=True):
                token = await server.get_access_token(client)

            self.assertEqual(token, "new-token")
            cached = json.loads(token_file.read_text())
            self.assertEqual(cached["token"], "new-token")
            self.assertEqual(cached["app_key"], "app")
            self.assertEqual(cached["token_scope"], "real")
            self.assertEqual(client.calls[0]["timeout"], 30.0)

    async def test_access_token_uses_virtual_domain_for_virtual_account(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            token_file = Path(tmpdir) / "token.json"
            env = {
                "KIS_APP_KEY": "app",
                "KIS_APP_SECRET": "secret",
                "KIS_ACCOUNT_TYPE": "VIRTUAL",
                "KIS_TOKEN_FILE": str(token_file),
            }
            client = StubClient(StubResponse({"access_token": "virtual-token"}))
            server._token_cache.update({"token": None, "expires_at": None, "app_key": None, "token_scope": None})

            with patch.dict(os.environ, env, clear=True):
                token = await server.get_access_token(client)

            self.assertEqual(token, "virtual-token")
            self.assertTrue(client.calls[0]["url"].startswith(server.VIRTUAL_DOMAIN))
            cached = json.loads(token_file.read_text())
            self.assertEqual(cached["token_scope"], "virtual")

    async def test_overseas_price_converts_order_market_to_quote_exchange(self):
        env = {
            "KIS_APP_KEY": "app",
            "KIS_APP_SECRET": "secret",
            "KIS_ACCOUNT_TYPE": "VIRTUAL",
        }
        client = StubClient(StubResponse({"output": {"last": "190.5"}}))

        with patch.dict(os.environ, env, clear=True), \
             patch.object(server, "get_http_client", AsyncMock(return_value=client)), \
             patch.object(server, "get_access_token", AsyncMock(return_value="token")):
            await server.inquery_overseas_stock_price("AAPL", "NASD")

        self.assertTrue(client.calls[0]["url"].startswith(server.DOMAIN))
        self.assertEqual(client.calls[0]["params"]["EXCD"], "NAS")


if __name__ == "__main__":
    unittest.main()
