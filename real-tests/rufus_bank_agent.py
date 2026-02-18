"""
## DEMO CODE FOR rufus-bank-agent SANTI.
## DO NOT USE IN PROD :)
## Interactive CLI agent using Strands + MCP Gateway
"""

from strands import Agent
from strands.models import BedrockModel
from strands.hooks import (
    HookProvider,
    HookRegistry,
    BeforeToolCallEvent,
    AfterToolCallEvent,
)
from strands.tools.mcp.mcp_client import MCPClient
from mcp.client.streamable_http import streamablehttp_client
import json


# ──────────────────────────────────────────────
# Configuración - Reemplaza con tus valores
# ──────────────────────────────────────────────
CLIENT_ID = "<YOUR_CLIENT_ID>"
CLIENT_SECRET = "<YOUR_CLIENT_SECRET>"
TOKEN_URL = "<TOKEN_ENDPOINT>"
GATEWAY_URL = "https://gateway-agentcore-bancolombia-outbound-tools-01-tv4ln7k9gd.gateway.bedrock-agentcore.us-east-1.amazonaws.com/mcp"


# ──────────────────────────────────────────────
# Hook para logging de tools (input/output)
# ──────────────────────────────────────────────
class ToolLoggingHook(HookProvider):
    """Loguea el input y output de cada tool call del agente."""

    def register_hooks(self, registry: HookRegistry) -> None:
        registry.add_callback(BeforeToolCallEvent, self.log_tool_input)
        registry.add_callback(AfterToolCallEvent, self.log_tool_output)

    def log_tool_input(self, event: BeforeToolCallEvent) -> None:
        tool_name = event.tool_use.get("name", "unknown")
        tool_input = event.tool_use.get("input", {})
        print(f"\n  🔧 [TOOL CALL] {tool_name}")
        print(f"  📥 [INPUT] {json.dumps(tool_input, indent=2, ensure_ascii=False)}")

    def log_tool_output(self, event: AfterToolCallEvent) -> None:
        tool_name = event.tool_use.get("name", "unknown")
        result = event.result
        # Truncar output largo para no llenar la terminal
        result_str = json.dumps(result, indent=2, ensure_ascii=False, default=str)
        if len(result_str) > 1000:
            result_str = result_str[:1000] + "\n  ... (truncado)"
        print(f"  📤 [OUTPUT] {tool_name}:")
        print(f"  {result_str}\n")


def create_streamable_http_transport(mcp_url: str, access_token: str):
    """Crea el transporte HTTP para conectarse al MCP Gateway."""
    return streamablehttp_client(
        mcp_url, headers={"Authorization": f"Bearer {access_token}"}
    )


def get_full_tools_list(client):
    """Lista todas las tools con soporte de paginación."""
    print("[PASO] Listando tools disponibles (con paginación)...")
    more_tools = True
    tools = []
    pagination_token = None
    while more_tools:
        tmp_tools = client.list_tools_sync(pagination_token=pagination_token)
        tools.extend(tmp_tools)
        if tmp_tools.pagination_token is None:
            more_tools = False
        else:
            pagination_token = tmp_tools.pagination_token
    print(f"[PASO] Se encontraron {len(tools)} tools en total.")
    return tools


# ──────────────────────────────────────────────
# System Prompt del agente Rufus Bank
# ──────────────────────────────────────────────
SYSTEM_PROMPT = """Eres Rufus Bank, un agente de servicio al cliente del banco.
Tu objetivo es ayudar a los clientes con sus consultas bancarias de forma amable y profesional.
RESPONDE SIEMPRE EN ESPAÑOL.

Puedes usar las siguientes herramientas para ayudar a los clientes:
- Consultar el estado de salud de cajeros automáticos (ATMs) por ciudad.
- Consultar el estado de salud de datáfonos por ciudad.
- Consultar el balance de cuentas de un usuario.

Siempre saluda al cliente, confirma lo que necesita, y usa las herramientas disponibles para dar respuestas precisas.
Si no tienes la información, indícalo amablemente.
"""


def main():
    print("\n╔═══════════════════════════════════════════╗")
    print("║   🏦 RUFUS BANK - Servicio al Cliente     ║")
    print("║   Escribe 'salir' para terminar            ║")
    print("╚═══════════════════════════════════════════╝\n")

    # ── Inicializar modelo ──
    print("[PASO] Inicializando modelo Bedrock...")
    model = BedrockModel(model_id="global.anthropic.claude-opus-4-6-v1")
    print("[PASO] Modelo inicializado.")

    # ── Conectar al MCP Gateway ──
    mcp_client = None
    mcp_tools = []

    try:
        print("[PASO] Conectando al MCP Gateway...")
        mcp_client = MCPClient(
            lambda: create_streamable_http_transport(
                GATEWAY_URL,
                "NONE_IT_IS_PUBLIC",
            )
        )
        mcp_client.start()
        print("[PASO] Conexión al MCP Gateway establecida.")

        mcp_tools = get_full_tools_list(mcp_client)
        print("[PASO] Tools cargadas:")
        for tool in mcp_tools:
            tool_name = getattr(tool, "tool_name", None) or getattr(
                tool, "name", str(tool)
            )
            tool_desc = getattr(tool, "description", "N/A")
            print(f"  - {tool_name}: {tool_desc}")

    except Exception as e:
        print(f"[ERROR] Error conectando al MCP Gateway: {e}")
        print("[INFO] El agente funcionará sin tools externas.")
        mcp_tools = []

    # ── Crear agente con hook de logging ──
    print("[PASO] Creando agente Rufus Bank...")
    tool_logger = ToolLoggingHook()
    agent = Agent(
        model=model,
        tools=mcp_tools,
        system_prompt=SYSTEM_PROMPT,
        hooks=[tool_logger],
    )
    print(f"[PASO] Agente creado con {len(agent.tool_names)} tools: {agent.tool_names}")
    print("\n" + "─" * 50)
    print("¡Listo! Puedes empezar a chatear con Rufus Bank.")
    print("─" * 50 + "\n")

    # ── Loop interactivo ──
    try:
        while True:
            user_input = input("🧑 Tú: ").strip()

            if not user_input:
                continue

            if user_input.lower() in ("salir", "exit", "quit", "q"):
                print("\n🏦 Rufus Bank: ¡Hasta luego! Fue un placer atenderte. 👋\n")
                break

            print("\n🏦 Rufus Bank: ", end="", flush=True)
            response = agent(user_input)

            # Extraer texto de la respuesta
            response_text = ""
            if hasattr(response, "message") and response.message:
                for block in response.message.get("content", []):
                    if isinstance(block, dict) and block.get("text"):
                        response_text += block["text"]

            if response_text:
                print(response_text)
            print()

    except KeyboardInterrupt:
        print("\n\n🏦 Rufus Bank: ¡Chao! Que tengas un excelente día. 👋\n")

    finally:
        if mcp_client:
            try:
                mcp_client.stop()
                print("[PASO] MCP Client desconectado.")
            except Exception as e:
                print(f"[ERROR] Error deteniendo MCP client: {e}")


if __name__ == "__main__":
    main()
