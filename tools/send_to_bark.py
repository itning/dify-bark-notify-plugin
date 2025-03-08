from collections.abc import Generator
from typing import Any
from urllib.parse import parse_qs, urlencode, urlparse

import httpx
from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage
from dify_plugin.errors.tool import ToolProviderCredentialValidationError


def _get_http_path(server_url: str, key: str, title: str | None, content: str, query_params: str) -> str:
    if not title:
        return f"{server_url}/{key}/{content}{query_params}"
    return f"{server_url}/{key}/{title}/{content}{query_params}"


def _merge_query_params(global_params: str, current_params: str) -> str:
    if not current_params or current_params.strip() == "":
        return global_params or ""
    if not global_params or global_params.strip() == "":
        return current_params or ""

    global_dict = parse_qs(urlparse(global_params).query)
    current_dict = parse_qs(urlparse(current_params).query)
    merged_dict = {**global_dict, **current_dict}
    merged_dict = {k: v[0] for k, v in merged_dict.items()}
    merged_query = urlencode(merged_dict)
    return f"?{merged_query}"


class SendNotify2Bark(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage]:
        server_url: str = self.runtime.credentials['server-url'].rstrip('/')
        key = self.runtime.credentials['key']
        default_query_params = self.runtime.credentials.get('default-query-params', '')
        query_params = tool_parameters.get('query_params', '')

        if 'content' not in tool_parameters:
            yield self.create_json_message({"message": 'Send Failed, because push content is missing'})
            return

        if query_params and not query_params.startswith('?'):
            yield self.create_json_message({"message": 'Send Failed, because query param must start with "?"'})
            return

        query_params = _merge_query_params(default_query_params, query_params)

        try:
            response = httpx.get(
                _get_http_path(server_url, key, tool_parameters.get('title'), tool_parameters['content'], query_params)
            )
            response.raise_for_status()
            response_body = response.json()
        except httpx.RequestError as e:
            yield self.create_json_message({"message": f"Send Failed, because of a network error: {e}"})
            return
        except ValueError:
            yield self.create_json_message({"message": "Send Failed, because the response is not valid JSON"})
            return

        if not isinstance(response_body, dict) or response_body.get('code') != 200:
            raise ToolProviderCredentialValidationError(f"Got error: {response_body}")

        yield self.create_json_message({"message": 'Send Successful'})
