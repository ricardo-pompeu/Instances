# Validação do porte

Verificações executadas em 1 de outubro de 2026:

- Runtime: Python 3.15.0rc2, GTK 4.24.0, libadwaita 1.10.0.
- Compilação Meson/Ninja e geração do GResource concluídas.
- 16 testes unitários do estado, controlador e cliente HTTP aprovados.
- Teste de interface em display GTK Broadway aprovado com críticos GTK fatais.
- Templates compilados: janela, sidebar e diálogo de download carregados.
- Rascunhos por conversa, modelo selecionado e reconexão temporária verificados.
- Cancelamento, nova geração, busca, atalhos e confirmação de limpeza verificados.
- Janela de 390px com split view recolhida e sidebar em modo de página verificada.
- Progresso de download e estado de ações verificados com dados simulados.
- Arquivo desktop aprovado por `desktop-file-validate`.
- Instalação em staging, importação do pacote instalado e leitura do GResource verificadas.
- Catálogo Gettext gerado. A ferramenta emitiu avisos sobre a regra ITS de fallback
  e arquivos novos ainda não rastreados no Git; a geração terminou com sucesso.

Neste ambiente, o compilador de recursos foi utilizado a partir do GNOME SDK 50
já instalado. Meson recebeu seu caminho por um arquivo nativo temporário; nenhuma
dependência foi instalada. O build de verificação usa prefixo `/tmp/instances-install`,
e a instalação de staging usa `/tmp/instances-stage`.

Os testes de interface usam uma instância independente e simulam Ollama e systemd.
Não foram executados download ou inferência reais. As capturas de prévia usam
conversas fictícias. Broadway apresentou falhas de reconexão/renderização no
navegador de revisão; as asserções de interface passaram, mas a revisão visual
completa de temas e escalas deve ser feita também no desktop nativo.

Este relatório registra validação técnica do porte; não é certificação HIG,
acessibilidade ou aprovação do GNOME Circle. Autoria, licença, URL, identificador
definitivo e metadados AppStream continuam pendentes conforme solicitado.
