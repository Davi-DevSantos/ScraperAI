
from unittest.mock import MagicMock, patch

import pytest

from app.services.scraper import IAScrapeServices, _build_client, client


def _mock_openai_client(content: str | None = '{"nome": "teste"}'):
    mock_client = MagicMock()
    mock_message = MagicMock()
    mock_message.content = content
    mock_choice = MagicMock()
    mock_choice.message = mock_message
    mock_chat = MagicMock()
    mock_chat.choices = [mock_choice]
    mock_client.chat.completions.create.return_value = mock_chat
    return mock_client

def _mock_provider(content: str | None = '{"ok": true}', name: str = "openai"):
    mock = MagicMock()
    mock.name = name
    mock.complete.return_value = content
    return mock




class TestInit:
    def test_init_armazena_url_e_prompt(self):
        svc = IAScrapeServices(url="https://exemplo.com", prompt="extraia preços")
        assert svc.url == "https://exemplo.com"
        assert svc.prompt == "extraia preços"
        assert svc._client is None

    def test_init_com_client_injetado(self):
        mock_client = MagicMock()
        svc = IAScrapeServices(url="https://ex.com", prompt="p", client=mock_client)
        assert svc._client is mock_client

    def test_init_com_provider_injetado(self):
        mock_provider = _mock_provider()
        svc = IAScrapeServices(url="https://ex.com", prompt="p", provider=mock_provider)
        assert svc._provider is mock_provider

    def test_init_com_provider_name_e_api_key(self):
        with patch("app.services.scraper.get_provider") as mock_get_provider:
            mock_prov = _mock_provider()
            mock_get_provider.return_value = mock_prov
            svc = IAScrapeServices(url="https://ex.com", prompt="p", provider_name="anthropic", api_key="sk-ant-test")
            mock_get_provider.assert_called_once_with("anthropic", api_key="sk-ant-test")
            assert svc._provider is mock_prov

    def test_system_prompt_constante(self):
        assert IAScrapeServices.SYSTEM_PROMPT == "Você apenas extrai dados de sites e retorna os dados diretamente em formato json"




class TestBuildClient:
    def test_build_client_usa_api_key_do_setting(self):
        with patch("app.services.scraper.setting") as mock_setting:
            mock_setting.AI_API_KEY = "sk-real"
            mock_setting.get_api_key_for.return_value = "sk-real"
            with patch("app.services.scraper.OpenAI") as MockOpenAI:
                _build_client()
                MockOpenAI.assert_called_once_with(api_key="sk-real")

    def test_build_client_fallback_sk_test_quando_sem_chave(self):
        with patch("app.services.scraper.setting") as mock_setting:
            mock_setting.AI_API_KEY = ""
            mock_setting.get_api_key_for.return_value = ""
            with patch("app.services.scraper.OpenAI") as MockOpenAI:
                _build_client()
                MockOpenAI.assert_called_once_with(api_key="sk-test")

    def test_build_client_fallback_quando_none(self):
        with patch("app.services.scraper.setting") as mock_setting:
            mock_setting.AI_API_KEY = None
            mock_setting.get_api_key_for.return_value = None
            with patch("app.services.scraper.OpenAI") as MockOpenAI:
                _build_client()
                MockOpenAI.assert_called_once_with(api_key="sk-test")

    def test_client_global_existe(self):
        assert client is not None

    def test_get_client_retorna_adapter_quando_client_injetado(self):
        mock_injected = MagicMock()
        svc = IAScrapeServices(url="https://ex.com", prompt="p", client=mock_injected)

        adapter = svc._get_client()
        assert hasattr(adapter, "_c")
        assert adapter._c is mock_injected

    def test_get_client_retorna_provider_injetado(self):
        mock_provider = _mock_provider()
        svc = IAScrapeServices(url="https://ex.com", prompt="p", provider=mock_provider)
        assert svc._get_client() is mock_provider

    def test_provider_factory_fallback_dummy_quando_sem_chave(self):

        svc = IAScrapeServices(url="https://ex.com", prompt="p")

        assert svc._provider is not None
        assert hasattr(svc._provider, "complete")




class TestGetDataHappyPath:
    @patch("app.services.scraper.format_prompt")
    @patch("app.services.scraper.format_html")
    @patch("app.services.scraper.get_html")
    def test_get_data_fluxo_completo_com_client_injetado(self, mock_get_html, mock_format_html, mock_format_prompt):
        mock_get_html.return_value = "<html><body><h1>Teste</h1></body></html>"
        mock_soup = MagicMock()
        mock_soup.__str__.return_value = "<html>clean</html>"
        mock_format_html.return_value = mock_soup
        mock_format_prompt.return_value = "prompt formatado"
        mock_client = _mock_openai_client(content='{"titulo": "Teste"}')
        svc = IAScrapeServices(url="https://exemplo.com", prompt="extraia titulo", client=mock_client)
        result = svc.get_data()
        mock_get_html.assert_called_once_with("https://exemplo.com")
        mock_format_html.assert_called_once_with("<html><body><h1>Teste</h1></body></html>")
        mock_format_prompt.assert_called_once_with(html="<html>clean</html>", prompt="extraia titulo")
        mock_client.chat.completions.create.assert_called_once()
        assert result == '{"titulo": "Teste"}'

    @patch("app.services.scraper.format_prompt")
    @patch("app.services.scraper.format_html")
    @patch("app.services.scraper.get_html")
    def test_get_data_chama_openai_com_parametros_corretos(self, mock_get_html, mock_format_html, mock_format_prompt):
        mock_get_html.return_value = "<html></html>"
        mock_format_html.return_value = MagicMock(__str__=lambda s: "clean")
        mock_format_prompt.return_value = "user prompt"
        mock_client = _mock_openai_client()
        svc = IAScrapeServices(url="https://site.com", prompt="faça X", client=mock_client)
        with patch("app.services.scraper.setting") as mock_setting:
            mock_setting.AI_MODEL = "gpt-4o-mini"
            mock_setting.AI_MAX_TOKENS = 500
            mock_setting.AI_TEMPERATURE = 0.1
            mock_setting.AI_PROVIDER = "openai"
            svc.get_data()
            _, kwargs = mock_client.chat.completions.create.call_args
            assert kwargs["model"] == "gpt-4o-mini"
            assert kwargs["max_tokens"] == 500
            assert kwargs["temperature"] == 0.1
            assert kwargs["messages"][0]["role"] == "system"
            assert kwargs["messages"][0]["content"] == IAScrapeServices.SYSTEM_PROMPT
            assert kwargs["messages"][1]["role"] == "user"
            assert kwargs["messages"][1]["content"] == "user prompt"

    @patch("app.services.scraper.format_prompt")
    @patch("app.services.scraper.format_html")
    @patch("app.services.scraper.get_html")
    def test_get_data_usa_configuracao_customizada(self, mock_get_html, mock_format_html, mock_format_prompt):
        mock_get_html.return_value = "<html></html>"
        mock_format_html.return_value = MagicMock(__str__=lambda s: "clean")
        mock_format_prompt.return_value = "p"
        mock_client = _mock_openai_client()
        svc = IAScrapeServices(url="https://site.com", prompt="p", client=mock_client)
        with patch("app.services.scraper.setting") as mock_setting:
            mock_setting.AI_MODEL = "gpt-4o"
            mock_setting.AI_MAX_TOKENS = 2048
            mock_setting.AI_TEMPERATURE = 0.7
            mock_setting.AI_PROVIDER = "openai"
            svc.get_data()
            kwargs = mock_client.chat.completions.create.call_args[1]
            assert kwargs["model"] == "gpt-4o"
            assert kwargs["max_tokens"] == 2048
            assert kwargs["temperature"] == 0.7

    @patch("app.services.scraper.format_prompt")
    @patch("app.services.scraper.format_html")
    @patch("app.services.scraper.get_html")
    def test_get_data_fallback_valores_quando_setting_vazio(self, mock_get_html, mock_format_html, mock_format_prompt):
        mock_get_html.return_value = "<html></html>"
        mock_format_html.return_value = MagicMock(__str__=lambda s: "clean")
        mock_format_prompt.return_value = "p"
        mock_client = _mock_openai_client()
        svc = IAScrapeServices(url="https://site.com", prompt="p", client=mock_client)
        with patch("app.services.scraper.setting") as mock_setting:
            mock_setting.AI_MODEL = ""
            mock_setting.AI_MAX_TOKENS = 0
            mock_setting.AI_TEMPERATURE = None
            mock_setting.AI_PROVIDER = "openai"
            svc.get_data()
            kwargs = mock_client.chat.completions.create.call_args[1]
            assert kwargs["model"] == "gpt-4o-mini"
            assert kwargs["max_tokens"] == 500
            assert kwargs["temperature"] == 0.1

    @patch("app.services.scraper.format_prompt")
    @patch("app.services.scraper.format_html")
    @patch("app.services.scraper.get_html")
    def test_get_data_stringifica_soup_antes_format_prompt(self, mock_get_html, mock_format_html, mock_format_prompt):
        mock_get_html.return_value = "<html></html>"
        mock_soup = MagicMock()
        mock_soup.__str__.return_value = "<div>limpo</div>"
        mock_format_html.return_value = mock_soup
        mock_format_prompt.return_value = "x"
        mock_client = _mock_openai_client()
        svc = IAScrapeServices(url="https://a.com", prompt="prompt", client=mock_client)
        svc.get_data()
        _args, kwargs = mock_format_prompt.call_args
        assert kwargs["html"] == "<div>limpo</div>"
        assert kwargs["prompt"] == "prompt"

    @patch("app.services.scraper.format_prompt")
    @patch("app.services.scraper.format_html")
    @patch("app.services.scraper.get_html")
    def test_get_data_com_provider_mock(self, mock_get_html, mock_format_html, mock_format_prompt):
        mock_get_html.return_value = "<html></html>"
        mock_format_html.return_value = MagicMock(__str__=lambda s: "clean")
        mock_format_prompt.return_value = "p"
        mock_provider = _mock_provider(content='{"ok": true}', name="anthropic")
        svc = IAScrapeServices(url="https://site.com", prompt="p", provider=mock_provider)
        with patch("app.services.scraper.setting") as mock_setting:
            mock_setting.AI_MODEL = "claude-3-5-sonnet-latest"
            mock_setting.AI_MAX_TOKENS = 1024
            mock_setting.AI_TEMPERATURE = 0.5
            mock_setting.AI_PROVIDER = "anthropic"
            result = svc.get_data()
            mock_provider.complete.assert_called_once()

            kwargs = mock_provider.complete.call_args[1]
            assert kwargs["model"] == "claude-3-5-sonnet-latest"
            assert kwargs["max_tokens"] == 1024
            assert result == '{"ok": true}'




class TestGetDataEdgeCases:
    @patch("app.services.scraper.format_prompt")
    @patch("app.services.scraper.format_html")
    @patch("app.services.scraper.get_html")
    def test_get_data_retorna_none_quando_conteudo_none(self, mock_get_html, mock_format_html, mock_format_prompt):
        mock_get_html.return_value = "<html></html>"
        mock_format_html.return_value = MagicMock(__str__=lambda s: "clean")
        mock_format_prompt.return_value = "p"
        mock_client = _mock_openai_client(content=None)
        svc = IAScrapeServices(url="https://site.com", prompt="p", client=mock_client)
        result = svc.get_data()
        assert result is None

    @patch("app.services.scraper.format_prompt")
    @patch("app.services.scraper.format_html")
    @patch("app.services.scraper.get_html")
    def test_get_data_propaga_erro_get_html(self, mock_get_html, mock_format_html, mock_format_prompt):
        mock_get_html.side_effect = Exception("timeout")
        svc = IAScrapeServices(url="https://site.com", prompt="p", client=_mock_openai_client())
        with pytest.raises(Exception, match="timeout"):
            svc.get_data()
        mock_format_html.assert_not_called()

    @patch("app.services.scraper.format_prompt")
    @patch("app.services.scraper.format_html")
    @patch("app.services.scraper.get_html")
    def test_get_data_propaga_erro_format_html(self, mock_get_html, mock_format_html, mock_format_prompt):
        mock_get_html.return_value = "<html></html>"
        mock_format_html.side_effect = ValueError("parse error")
        svc = IAScrapeServices(url="https://site.com", prompt="p", client=_mock_openai_client())
        with pytest.raises(ValueError, match="parse error"):
            svc.get_data()

    @patch("app.services.scraper.format_prompt")
    @patch("app.services.scraper.format_html")
    @patch("app.services.scraper.get_html")
    def test_get_data_propaga_erro_provider(self, mock_get_html, mock_format_html, mock_format_prompt):
        mock_get_html.return_value = "<html></html>"
        mock_format_html.return_value = MagicMock(__str__=lambda s: "clean")
        mock_format_prompt.return_value = "p"
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = Exception("openai error")
        svc = IAScrapeServices(url="https://site.com", prompt="p", client=mock_client)
        with pytest.raises(Exception, match="openai error"):
            svc.get_data()

    @patch("app.services.scraper.format_prompt")
    @patch("app.services.scraper.format_html")
    @patch("app.services.scraper.get_html")
    def test_get_data_retorna_json_string(self, mock_get_html, mock_format_html, mock_format_prompt):
        mock_get_html.return_value = "<html>produto</html>"
        mock_format_html.return_value = MagicMock(__str__=lambda s: "produto limpo")
        mock_format_prompt.return_value = "extraia json"
        esperado = '{"produtos": [{"nome": "Caneta", "preco": "10,00"}]}'
        mock_client = _mock_openai_client(content=esperado)
        svc = IAScrapeServices(url="https://loja.com", prompt="extraia produtos", client=mock_client)
        assert svc.get_data() == esperado

    @patch("app.services.scraper.format_prompt")
    @patch("app.services.scraper.format_html")
    @patch("app.services.scraper.get_html")
    def test_get_data_multiplas_chamadas_independentes(self, mock_get_html, mock_format_html, mock_format_prompt):
        mock_get_html.return_value = "<html></html>"
        mock_format_html.return_value = MagicMock(__str__=lambda s: "clean")
        mock_format_prompt.return_value = "p"
        mock_client = _mock_openai_client(content="resposta")
        svc = IAScrapeServices(url="https://site.com", prompt="p", client=mock_client)
        assert svc.get_data() == "resposta"
        assert svc.get_data() == "resposta"
        assert mock_client.chat.completions.create.call_count == 2
        assert mock_get_html.call_count == 2

    @patch("app.services.scraper.format_prompt")
    @patch("app.services.scraper.format_html")
    @patch("app.services.scraper.get_html")
    def test_get_data_url_e_prompt_sao_usados_corretamente_em_multiplos_servicos(self, mock_get_html, mock_format_html, mock_format_prompt):
        mock_get_html.return_value = "<html></html>"
        mock_format_html.return_value = MagicMock(__str__=lambda s: "clean")
        mock_format_prompt.return_value = "fmt"
        mock_client1 = _mock_openai_client(content="r1")
        mock_client2 = _mock_openai_client(content="r2")
        svc1 = IAScrapeServices(url="https://a.com", prompt="prompt1", client=mock_client1)
        svc2 = IAScrapeServices(url="https://b.com", prompt="prompt2", client=mock_client2)
        svc1.get_data()
        svc2.get_data()
        assert mock_get_html.call_args_list[0][0][0] == "https://a.com"
        assert mock_get_html.call_args_list[1][0][0] == "https://b.com"
        assert mock_format_prompt.call_args_list[0][1]["prompt"] == "prompt1"
        assert mock_format_prompt.call_args_list[1][1]["prompt"] == "prompt2"




class TestIntegracaoUtils:
    def test_format_prompt_alone(self):
        from app.utils.format_data import format_prompt

        html = "<div>teste</div>"
        prompt = "extraia"
        result = format_prompt(html=html, prompt=prompt)
        assert prompt in result
        assert html in result
        assert "==============" in result

    def test_format_html_remove_tags_indesejadas(self):
        from app.utils.html_extractor import format_html

        html = """
        <html><head><style>body{}</style><script>alert(1)</script></head>
        <body><h1>Titulo</h1><svg></svg><canvas></canvas><p>texto</p></body></html>
        """
        soup = format_html(html)
        assert soup.find("script") is None
        assert soup.find("style") is None
        assert soup.find("svg") is None
        assert soup.find("canvas") is None
        assert soup.find("h1").text == "Titulo"
        assert soup.find("p").text == "texto"

    def test_format_html_preserva_conteudo(self):
        from app.utils.html_extractor import format_html

        html = "<html><body><div class='produto'>Caneta</div></body></html>"
        soup = format_html(html)
        assert "Caneta" in str(soup)




class TestMultiProvider:
    @patch("app.services.scraper.format_prompt")
    @patch("app.services.scraper.format_html")
    @patch("app.services.scraper.get_html")
    def test_anthropic_provider(self, mock_get_html, mock_format_html, mock_format_prompt):
        mock_get_html.return_value = "<html></html>"
        mock_format_html.return_value = MagicMock(__str__=lambda s: "clean")
        mock_format_prompt.return_value = "p"
        mock_provider = _mock_provider(content='{"x":1}', name="anthropic")
        svc = IAScrapeServices(url="https://ex.com", prompt="p", provider=mock_provider)
        assert svc.get_data() == '{"x":1}'
        mock_provider.complete.assert_called_once()

    @patch("app.services.scraper.format_prompt")
    @patch("app.services.scraper.format_html")
    @patch("app.services.scraper.get_html")
    def test_gemini_provider_strip_fences(self, mock_get_html, mock_format_html, mock_format_prompt):
        mock_get_html.return_value = "<html></html>"
        mock_format_html.return_value = MagicMock(__str__=lambda s: "clean")
        mock_format_prompt.return_value = "p"

        mock_provider = _mock_provider(content='```json\n{"y":2}\n```', name="gemini")

        from app.utils.json_parser import strip_markdown_fences

        assert strip_markdown_fences('```json\n{"y":2}\n```') == '{"y":2}'
        mock_provider.complete.return_value = '{"y":2}'
        svc = IAScrapeServices(url="https://ex.com", prompt="p", provider=mock_provider)
        assert svc.get_data() == '{"y":2}'

    def test_factory_normalize_google_para_gemini(self):
        from app.services.providers.factory import normalize_provider

        assert normalize_provider("google") == "gemini"
        assert normalize_provider("Google") == "gemini"
        assert normalize_provider("OPENAI") == "openai"

    def test_factory_provider_invalido(self):
        from app.core.exceptions import InvalidError
        from app.services.providers.factory import get_provider

        with pytest.raises(InvalidError):
            get_provider("invalido", api_key="sk-test")

    def test_provider_por_api_key_do_usuario(self):
        mock_inst = MagicMock()
        mock_cls = MagicMock(return_value=mock_inst)
        with patch.dict("app.services.providers.factory._PROVIDER_MAP", {"anthropic": mock_cls}):
            from app.services.providers.factory import get_provider

            result = get_provider("anthropic", api_key="sk-ant-user-key")
            mock_cls.assert_called_once_with(api_key="sk-ant-user-key")
            assert result is mock_inst

    def test_openai_provider_exige_chave(self):
        from app.core.exceptions import ServiceError
        from app.services.providers.openai_provider import OpenAIProvider

        with patch("app.services.providers.openai_provider.setting") as mock_setting:
            mock_setting.get_api_key_for.return_value = ""
            with pytest.raises(ServiceError, match="OPENAI_API_KEY"):
                OpenAIProvider(api_key=None)

    def test_anthropic_provider_exige_chave(self):
        from app.core.exceptions import ServiceError
        from app.services.providers.anthropic_provider import AnthropicProvider

        with patch("app.services.providers.anthropic_provider.setting") as mock_setting:
            mock_setting.get_api_key_for.return_value = ""
            with pytest.raises(ServiceError, match="ANTHROPIC_API_KEY"):
                AnthropicProvider(api_key=None)
