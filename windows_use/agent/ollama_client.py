from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from typing import List, Dict, Any
import requests
import re


class OllamaChat:
    """
    Minimal chat client adapter for Ollama's /api/chat endpoint with image support.
    Provides an .invoke(messages) API returning an AIMessage, compatible with Agent.
    """

    def __init__(self, model: str = "gemma3:latest", base_url: str = "http://localhost:11434", request_timeout: int = 900):
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.request_timeout = request_timeout

    def _convert_messages(self, messages: List[BaseMessage]) -> List[Dict[str, Any]]:
        converted: List[Dict[str, Any]] = []
        for m in messages:
            role = "user"
            if isinstance(m, SystemMessage):
                role = "system"
            elif isinstance(m, HumanMessage):
                role = "user"
            else:
                # Treat any AI/assistant message as assistant
                role = "assistant"

            content_text = ""
            images: List[str] = []

            # HumanMessage may contain multimodal content as a list
            if isinstance(m, HumanMessage) and isinstance(m.content, list):
                for part in m.content:
                    if isinstance(part, dict) and part.get("type") == "text":
                        content_text += (part.get("text") or "")
                    elif isinstance(part, dict) and part.get("type") == "image_url":
                        image_url = None
                        image_block = part.get("image_url")
                        if isinstance(image_block, dict):
                            image_url = image_block.get("url")
                        elif isinstance(image_block, str):
                            image_url = image_block
                        if image_url:
                            images.append(self._to_raw_base64(image_url))
            else:
                # Regular string content
                try:
                    content_text = str(m.content)
                except Exception:
                    content_text = ""

            message_obj: Dict[str, Any] = {"role": role, "content": content_text}
            if images:
                # Ollama supports base64 data URIs in images array
                message_obj["images"] = images
            converted.append(message_obj)
        return converted

    @staticmethod
    def _to_raw_base64(possibly_data_uri: str) -> str:
        """
        Accepts either a full data URI (data:image/png;base64,AAA...) or raw base64 and returns raw base64 string only.
        Ollama expects raw base64 in the images array.
        """
        if not isinstance(possibly_data_uri, str):
            return ""
        # Match data URI prefix
        match = re.match(r"^data:image/[^;]+;base64,(.*)$", possibly_data_uri)
        if match:
            return match.group(1)
        return possibly_data_uri

    def invoke(self, messages: List[BaseMessage]) -> AIMessage:
        converted_messages = self._convert_messages(messages)
        payload = {
            "model": self.model,
            "messages": converted_messages,
            "stream": False,
        }
        url = f"{self.base_url}/api/chat"
        
        try:
            print(f"🔄 Calling Ollama: {self.model} at {url}")
            print(f"📝 Messages: {len(converted_messages)} messages")
            # Check if we have images
            image_count = sum(1 for msg in converted_messages if msg.get("images"))
            if image_count > 0:
                print(f"🖼️  Images: {image_count} messages with images")
            
            response = requests.post(url, json=payload, timeout=self.request_timeout)
            response.raise_for_status()
            data = response.json()

            # The non-streaming response typically includes { "message": { "content": "..." }, ... }
            content = ""
            if isinstance(data, dict):
                msg = data.get("message") or {}
                content = msg.get("content") or data.get("response") or ""
            
            print(f"✅ Ollama response received: {len(content)} chars")
            return AIMessage(content=content)
            
        except requests.exceptions.Timeout:
            print(f"⏰ Ollama timeout after {self.request_timeout}s")
            return AIMessage(content="Error: Ollama request timed out. The model may be processing a large image.")
        except requests.exceptions.RequestException as e:
            print(f"❌ Ollama request error: {e}")
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_data = e.response.json()
                    print(f"Error details: {error_data}")
                except:
                    print(f"Error response: {e.response.text}")
            return AIMessage(content=f"Error: Failed to communicate with Ollama: {e}")
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            return AIMessage(content=f"Error: Unexpected error calling Ollama: {e}")


