import json
import unittest

from last30days_pro_max import mcp_server


def req(method, params=None, mid=1):
    message = {"jsonrpc": "2.0", "method": method}
    if mid is not None:
        message["id"] = mid
    if params is not None:
        message["params"] = params
    return message


class McpServerTests(unittest.TestCase):
    def test_initialize_returns_protocol_and_server_info(self):
        resp = mcp_server.handle_message(req("initialize", mid=1))
        self.assertEqual(resp["id"], 1)
        self.assertIn("protocolVersion", resp["result"])
        self.assertEqual(resp["result"]["serverInfo"]["name"], "last30days-pro-max")
        self.assertIn("tools", resp["result"]["capabilities"])

    def test_initialized_notification_returns_no_response(self):
        self.assertIsNone(mcp_server.handle_message(req("notifications/initialized", mid=None)))

    def test_tools_list_exposes_pipeline_tools(self):
        resp = mcp_server.handle_message(req("tools/list", mid=2))
        names = {t["name"] for t in resp["result"]["tools"]}
        for expected in {"build_query_pack", "search_serp", "normalize_evidence", "generate_report", "run_report"}:
            self.assertIn(expected, names)
        for tool in resp["result"]["tools"]:
            self.assertIn("description", tool)
            self.assertIn("inputSchema", tool)

    def test_tools_call_build_query_pack_returns_text_content(self):
        resp = mcp_server.handle_message(
            req("tools/call", {"name": "build_query_pack",
                               "arguments": {"seed_keywords": ["MCP web scraping"], "competitors": ["Apify"]}}, mid=3)
        )
        self.assertFalse(resp["result"]["isError"])
        payload = json.loads(resp["result"]["content"][0]["text"])
        self.assertIn('"MCP" "web scraping"', payload["queries"])

    def test_tools_call_run_report_mock(self):
        resp = mcp_server.handle_message(
            req("tools/call", {"name": "run_report", "arguments": {"mock": True, "query_limit": 1}}, mid=4)
        )
        payload = json.loads(resp["result"]["content"][0]["text"])
        self.assertIn("# Last30Days Pro Max", payload["report_markdown"])

    def test_unknown_tool_is_reported_as_error(self):
        resp = mcp_server.handle_message(
            req("tools/call", {"name": "does_not_exist", "arguments": {}}, mid=5)
        )
        # Either a JSON-RPC error or an isError tool result is acceptable.
        self.assertTrue("error" in resp or resp["result"]["isError"])

    def test_tool_handler_exception_becomes_error_result(self):
        # search_serp requires "query"; omitting it makes the handler raise.
        resp = mcp_server.handle_message(
            req("tools/call", {"name": "search_serp", "arguments": {}}, mid=6)
        )
        self.assertTrue(resp["result"]["isError"])

    def test_unknown_method_returns_jsonrpc_error(self):
        resp = mcp_server.handle_message(req("no/such/method", mid=7))
        self.assertEqual(resp["error"]["code"], -32601)


if __name__ == "__main__":
    unittest.main()
