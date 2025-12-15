import json
import urllib.request
import urllib.error
from typing import Dict, Any, Optional

# Default Hachimi IPC address
HACHIMI_IPC_PORT = 50433
DEFAULT_HOST = "127.0.0.1"

class HachimiIpcClient:
    def __init__(self, host: str = DEFAULT_HOST):
        self.base_url = f"http://{host}:{HACHIMI_IPC_PORT}"

    def send_command(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sends a JSON command to Hachimi via HTTP POST.
        """
        data = json.dumps(command).encode('utf-8')
        req = urllib.request.Request(
            self.base_url,
            data=data,
            headers={'Content-Type': 'application/json'}
        )

        try:
            with urllib.request.urlopen(req) as response:
                response_data = response.read().decode('utf-8')
                return json.loads(response_data)
        except urllib.error.URLError as e:
            return {
                "type": "Error",
                "message": f"Failed to connect to Hachimi: {e}"
            }
        except json.JSONDecodeError:
            return {
                "type": "Error",
                "message": "Invalid response from Hachimi"
            }
        except Exception as e:
            return {
                "type": "Error",
                "message": f"Unexpected error: {e}"
            }

# Singleton instance for easy import
ipc_client = HachimiIpcClient()
