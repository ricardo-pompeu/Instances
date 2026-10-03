"""Regressões de estado e ciclo de vida sem criar widgets GTK."""

import threading
import unittest
from unittest.mock import patch

from instances.controller import InstancesController


class FakeClient:
    def __init__(self):
        self.cancelar = threading.Event()
        self.interrupt_first = True
        self.requests = []

    def iniciar(self):
        self.cancelar.clear()

    def parar(self, worker=None):
        self.cancelar.set()

    def iterar_resposta(self, model, messages):
        self.requests.append(messages)
        if self.interrupt_first:
            self.interrupt_first = False
            yield 'parcial'
            self.cancelar.set()
            raise AttributeError("'NoneType' object has no attribute 'read'")
        yield 'nova resposta'


class ControllerTest(unittest.TestCase):
    def setUp(self):
        self.jobs = []
        self.callbacks = []
        self.client = FakeClient()
        self.controller = InstancesController(
            client=self.client, worker=self.jobs.append,
            dispatch=self.callbacks.append,
        )
        self.controller.servico_ativo = True
        self.controller.modelos = ['modelo']
        self.conversa = self.controller.nova_conversa('modelo')

    def drain(self):
        while self.callbacks:
            self.callbacks.pop(0)()

    def run_job(self):
        self.jobs.pop(0)()
        self.drain()

    def test_cancelamento_preserva_pergunta_e_permite_continuar(self):
        self.controller.gerar('primeira pergunta', 'modelo')
        self.run_job()
        self.assertFalse(self.controller.gerando)
        self.assertIn('Geração interrompida.', self.conversa.mensagens[-1].texto)
        self.assertEqual(self.conversa.historico, [
            {'role': 'user', 'content': 'primeira pergunta'},
        ])
        self.controller.gerar('segunda pergunta', 'modelo')
        self.run_job()
        self.assertEqual(self.client.requests[-1], [
            {'role': 'user', 'content': 'primeira pergunta'},
            {'role': 'user', 'content': 'segunda pergunta'},
        ])
        self.assertEqual(self.conversa.ultima_resposta, 'nova resposta')
        self.assertFalse(self.controller.gerando)

    def test_fechar_descarta_callbacks_pendentes(self):
        signals = []
        self.controller.connect('message-updated', lambda *_: signals.append(True))
        self.controller.gerar('pergunta', 'modelo')
        self.jobs.pop(0)()
        self.controller.fechar()
        self.drain()
        self.assertEqual(signals, [])
        self.assertEqual(self.conversa.mensagens[-1].texto, 'Pensando…')

    def test_callback_antigo_nao_atualiza_nova_geracao(self):
        self.controller.gerar('pergunta', 'modelo')
        generation = self.controller._generation
        resposta = self.conversa.mensagens[-1]
        self.run_job()
        self.controller.gerar('outra pergunta', 'modelo')
        anterior = resposta.texto
        self.controller._fragment(generation, resposta, 'atrasado', False)
        self.assertEqual(resposta.texto, anterior)

    def test_erro_inesperado_libera_estado_da_geracao(self):
        self.client.interrupt_first = False
        with patch.object(self.client, 'iterar_resposta', side_effect=OSError('falha')):
            self.controller.gerar('pergunta', 'modelo')
            with self.assertLogs('instances.controller', level='ERROR'):
                self.run_job()
        self.assertFalse(self.controller.gerando)
        self.assertIn('falha', self.conversa.mensagens[-1].texto)

    def test_download_invalido_nao_inicia_operacao(self):
        with self.assertRaises(ValueError):
            self.controller.baixar('nome com espaços')
        self.assertFalse(self.controller.baixando)
        self.assertEqual(self.jobs, [])

    def test_download_publica_fracao_e_limpa_estado_ao_falhar(self):
        self.controller.baixando = True
        self.controller._download_progress('modelo', 'baixando', 0.4)
        self.assertEqual(self.controller.download_fraction, 0.4)
        self.assertIn('40%', self.controller.download_status)
        notices = []
        self.controller.connect('notice', lambda _c, text: notices.append(text))
        self.controller._download_finished('modelo', 'sem espaço')
        self.assertFalse(self.controller.baixando)
        self.assertIsNone(self.controller.download_fraction)
        self.assertEqual(self.controller.download_status, '')
        self.assertIn('sem espaço', notices[0])

    def test_callback_download_descartado_apos_encerramento(self):
        self.controller._later(self.controller._download_progress,
                               'modelo', 'baixando', 0.5)
        self.controller.fechar()
        self.drain()
        self.assertEqual(self.controller.download_status, '')
        self.assertIsNone(self.controller.download_fraction)

    def test_parar_solicita_cancelamento_sem_esperar_worker(self):
        self.controller.gerar('pergunta', 'modelo')
        self.controller.parar()
        self.assertTrue(self.client.cancelar.is_set())
        self.assertTrue(self.controller.interrompendo)
