"""MCP Streamable HTTP Клиент"""

import argparse
import asyncio
from typing import Optional
from contextlib import AsyncExitStack
import os
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

from langchain_gigachat import GigaChat
from dotenv import load_dotenv
from langchain_mcp_adapters.tools import load_mcp_tools
from langgraph.prebuilt import create_react_agent

load_dotenv()


class MCPClient:
    def __init__(self, llm_auth_key: str):
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
        self.model: GigaChat = GigaChat(
            model="GigaChat-2-Max",
            credentials=llm_auth_key,
            verify_ssl_certs=False
        )

    async def connect_to_streamable_http_server(
        self, server_url: str, headers: Optional[dict] = None
    ):
        """
        Подключение к серверу MCP с использованием HTTP Streamable транспортного протокола.
        
        :param server_url: Полный URL сервера с указанием пути '/mcp'.
        :param headers: Дополнительные заголовки для подключения.
        """
        self._streams_context = streamablehttp_client(  # pylint: disable=W0201
            url=server_url,
            headers=headers or {},
        )
        read_stream, write_stream, _ = await self._streams_context.__aenter__()  # pylint: disable=E1101
        print(read_stream,'\n',write_stream,_)  # Отладочная печать
        self._session_context = ClientSession(read_stream, write_stream)  # pylint: disable=W0201
        print(self._session_context)  # Отладочная печать
        self.session: ClientSession = await self._session_context.__aenter__()  # pylint: disable=C2801
        print(self.session)  # Отладочная печать
        await self.session.initialize()

    async def process_query(self, query: str) -> str:
        """
        Обработка запроса с использованием модели GigaChat и доступных инструментов.
        
        :param query: Пользовательский запрос.
        :return: Красиво оформленный ответ с поддержкой вызова внешних инструментов.
        """
        messages = [{"role": "user", "content": query}]

        # Получаем список доступных инструментов
        response = await self.session.list_tools()
        
        # Загружаем доступные инструменты
        tools = await load_mcp_tools(self.session)

        # Создаем агента для обработки запросов
        agent = create_react_agent(self.model, tools)
        response = await agent.ainvoke({"messages": messages})

        # Подготовим красивую визуализацию результата
        steps = []  # Массив шагов вычислений
        final_result = ''  # Хранит итоговый результат

        for message in response['messages']:
            if message.content.startswith('['):  # Пропускаем служебные данные
                continue
            elif 'function_call' in message.additional_kwargs:
                # Обнаружен вызов функции
                func_data = message.additional_kwargs['function_call']
                tool_name = func_data['name']
                arguments = func_data['arguments']

                # Вызываем внешний инструмент
                result = await self.session.call_tool(tool_name, arguments)
                steps.append(f'- Вызван инструмент "{tool_name}" с аргументами: {arguments}')
                steps.append(f'→ Результат: {result.content}')
            elif message.content.endswith('.'):  # Итоговый результат
                final_result = message.content
            else:
                # Другие полезные сообщения
                steps.append(f'- {message.content}')

        # Составляем итоговый отчет
        output = [
            "Расчет шаг за шагом:",
            "",
            *steps,
            "",
            f"Окончательный результат: {final_result}",
        ]

        return "\n".join(output)



    async def chat_loop(self):
        """
        Интерактивный цикл обмена сообщениями.
        """
        print("\nMCP Клиент запущен!")
        print("Задавайте ваши запросы или введите 'quit', чтобы выйти.")

        while True:
            try:
                query = input("\nЗапрос: ").strip()

                if query.lower() == "quit":
                    break

                response = await self.process_query(query)
                print("\n" + response)

            except Exception as e:
                print(f"\nОшибка: {str(e)}")

    async def cleanup(self):
        """
        Освобождение ресурсов при завершении работы.
        """
        if self._session_context:
            await self._session_context.__aexit__(None, None, None)
        if self._streams_context:  # pylint: disable=W0125
            await self._streams_context.__aexit__(None, None, None)  # pylint: disable=E1101


async def run_console_chat_client():
    """
    Главная функция для запуска клиента MCP.
    """
    parser = argparse.ArgumentParser(description="Поддержка HTTP-транспортного протокола для клиентов MCP")
    parser.add_argument(
        "--mcp-localhost-port", type=int, default=8000, help="Порт для локального хоста"
    )
    args = parser.parse_args()

    client = MCPClient(os.getenv('LLM_API_KEY'))

    try:
        await client.connect_to_streamable_http_server(
            f"http://localhost:{args.mcp_localhost_port}/mcp"
        )
        await client.chat_loop()
    finally:
        await client.cleanup()
