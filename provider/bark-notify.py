from typing import Any

from dify_plugin import ToolProvider
from dify_plugin.errors.tool import ToolProviderCredentialValidationError
from tools.send_to_bark import SendNotify2Bark


class BarkNotifyProvider(ToolProvider):
    def _validate_credentials(self, credentials: dict[str, Any]) -> None:
        try:
            for _ in SendNotify2Bark.from_credentials(credentials).invoke(tool_parameters={"content": "test push from Dify bark-notify tool plugin"}):
                pass
        except ToolProviderCredentialValidationError as e:
            raise e
        except Exception as e:
            raise ToolProviderCredentialValidationError(str(e))
