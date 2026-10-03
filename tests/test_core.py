"""Verificações do estado das conversas e do contrato com o Ollama."""

import unittest
from unittest.mock import patch

from instances.conversations import Conversa, Mensagem
from instances.ollama import OllamaClient, baixar_modelo, listar_modelos
from instances.service import garantir_servico_ollama


class ServiceTest(unittest.TestCase):
    def test_servidor_conectado_nao_inicia_systemd(self):
        with (
            patch('instances.service.ollama_esta_disponivel', return_value=True),
            patch('instances.service.subprocess.run') as run,
        ):
            self.assertEqual(garantir_servico_ollama(), (True, 'Servidor conectado'))
        run.assert_not_called()


class RespostaFalsa:
    ok = True

    def __init__(self, dados=None, linhas=()):
        self.dados = dados
        self.linhas = linhas

    def json(self):
        return self.dados

    def iter_lines(self, **kwargs):
        return iter(self.linhas)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


class ConversasTest(unittest.TestCase):
    def test_conversas_tem_estado_independente(self):
        primeira = Conversa()
        segunda = Conversa()
        primeira.historico.append({"role": "user", "content": "Olá"})
        primeira.mensagens.append(Mensagem(usuario=True, texto="Olá"))
        primeira.nomear_pela_primeira_mensagem("Olá")

        self.assertEqual(primeira.titulo, "Olá")
        self.assertEqual(segunda.historico, [])
        primeira.rascunho = "texto não enviado"
        self.assertEqual(segunda.rascunho, "")
        primeira.limpar()
        self.assertEqual(primeira.titulo, "Nova conversa")
        self.assertEqual(primeira.mensagens, [])
        self.assertEqual(primeira.rascunho, "")


class OllamaTest(unittest.TestCase):
    def test_lista_modelos_ordenados_e_filtra_modelos_sem_completion(self):
        resposta = RespostaFalsa(dados={"models": [
            {"name": "zeta:latest"},
            {"name": "embed", "capabilities": ["embedding"]},
            {"name": "Alfa", "capabilities": ["completion"]},
        ]})
        with patch("instances.ollama.requests.get", return_value=resposta):
            self.assertEqual(listar_modelos(), ["Alfa", "zeta:latest"])

    def test_fragmento_malformado_nao_passa_para_interface(self):
        resposta = RespostaFalsa(linhas=['{"message": null}'])
        cliente = OllamaClient()
        with patch("instances.ollama.requests.post", return_value=resposta):
            with self.assertRaisesRegex(RuntimeError, "mensagem inválida"):
                list(cliente.iterar_resposta("modelo", []))
        self.assertIsNone(cliente.resposta_ativa)

    def test_stream_entrega_fragmentos_e_libera_resposta(self):
        resposta = RespostaFalsa(linhas=[
            '{"message": {"content": "Olá"}}',
            '{"message": {"content": " mundo"}}',
        ])
        cliente = OllamaClient()
        with patch("instances.ollama.requests.post", return_value=resposta):
            self.assertEqual(
                list(cliente.iterar_resposta("modelo", [])), ["Olá", " mundo"]
            )
        self.assertIsNone(cliente.resposta_ativa)

    def test_download_informa_progresso(self):
        resposta = RespostaFalsa(linhas=[
            '{"status": "downloading", "total": 100, "completed": 40}',
            '{"status": "success"}',
        ])
        eventos = []
        with patch("instances.ollama.requests.post", return_value=resposta) as post:
            baixar_modelo("llama3.2:1b", lambda *args: eventos.append(args))
        self.assertEqual(post.call_args.kwargs["json"]["name"], "llama3.2:1b")
        self.assertEqual(eventos, [("downloading", 0.4), ("success", None)])

    def test_cancelar_fluxo_permite_nova_resposta(self):
        cliente = OllamaClient()

        class RespostaInterrompida(RespostaFalsa):
            def iter_lines(self, **kwargs):
                yield '{"message": {"content": "parcial"}}'
                raise AttributeError("'NoneType' object has no attribute 'read'")

            def close(self):
                pass

        respostas = [
            RespostaInterrompida(),
            RespostaFalsa(linhas=['{"message": {"content": "nova resposta"}}']),
        ]
        with patch("instances.ollama.requests.post", side_effect=respostas):
            fluxo = cliente.iterar_resposta("modelo", [])
            self.assertEqual(next(fluxo), "parcial")
            cliente.parar()
            self.assertEqual(list(fluxo), [])
            self.assertIsNone(cliente.resposta_ativa)

            cliente.iniciar()
            self.assertEqual(list(cliente.iterar_resposta("modelo", [])), ["nova resposta"])
            self.assertIsNone(cliente.resposta_ativa)

    def test_fechamento_agendado_nao_fecha_uma_nova_resposta(self):
        cliente = OllamaClient()
        fechadas = []

        class Resposta:
            def __init__(self, nome):
                self.nome = nome

            def close(self):
                fechadas.append(self.nome)

        cliente.resposta_ativa = Resposta('anterior')
        tarefas = []
        cliente.parar(tarefas.append)
        cliente.iniciar()
        cliente.resposta_ativa = Resposta('nova')
        tarefas.pop()()
        self.assertEqual(fechadas, ['anterior'])
        self.assertFalse(cliente.cancelar.is_set())


if __name__ == "__main__":
    unittest.main()
