# Instances — Instâncias

Aplicativo GNOME para conversar com modelos locais do Ollama, feito com
Python, GTK 4 e libadwaita. O Instances é o projeto principal desta pasta.

## Executar

```bash
python3 -m instances
```

Também é possível usar `python3 main.py`. Execute a partir desta pasta.
O aplicativo usa o Ollama em `http://127.0.0.1:11434`.

Requisitos: Python >= 3.10, GTK >= 4.22, **libadwaita >= 1.9**, PyGObject
com os typelibs GTK/Adw e Requests >= 2.28, < 3. O porte usa `AdwSidebar`,
disponível desde libadwaita 1.9; não exige a versão alpha da biblioteca de referência.

No Fedora:

```bash
sudo dnf install python3-gobject python3-requests gtk4 libadwaita \
    meson ninja-build glib2-devel gettext
```

O Ollama é instalado separadamente. Quando a API não está disponível,
o Instances preserva a tentativa de iniciar `ollama.service` do projeto original.
Essa operação ocorre fora da thread da interface e pode solicitar autorização
gráfica do sistema. Com a API já disponível, não executa `systemctl`.

## Funcionalidades

- Conversas independentes, com título automático e rascunho por conversa.
- Sidebar nativa com busca e adaptação para janelas estreitas.
- Seleção e atualização dos modelos instalados.
- Download de modelos pelo nome, com barra de progresso.
- Respostas em streaming, interrupção e continuação da conversa.
- Cópia de cada resposta e da última resposta concluída.
- Sugestões na tela inicial, diálogos de confirmação, Sobre e atalhos.
- Feedback de conexão com banner, indicadores de atividade e toasts.
- Cores, controles e métricas fornecidos pela libadwaita.

**As conversas e os rascunhos existem apenas durante a sessão.** Não há
persistência em disco. Uma geração interrompida conserva a pergunta no
histórico; a resposta parcial é exibida, mas não é enviada ao modelo como
resposta concluída. Download e inferência são operações do servidor Ollama.
Não há cancelamento de download nesta versão.

## Atalhos

| Ação | Atalho |
|---|---|
| Nova conversa | Ctrl+N |
| Enviar | Ctrl+Enter |
| Interromper resposta | Ctrl+. |
| Buscar conversas | Ctrl+F |
| Mostrar ou ocultar conversas | F9 |
| Abrir menu | F10 |
| Mostrar atalhos | Ctrl+? |
| Fechar janela | Ctrl+W |
| Sair | Ctrl+Q |

## Estrutura

```text
instances/                  Aplicativo Python
  application.py          Ciclo de vida e ações da aplicação
  controller.py           Estado e operações assíncronas
  conversations.py        Conversas, mensagens e rascunhos
  ollama.py               HTTP, streaming e cancelamento
  service.py              Integração com o serviço local
  resources.py            Templates, estilos e traduções
  ui/                     Janela, sidebar e diálogo de download
data/
  ui/                     Templates GtkBuilder
  style.css               Estilos restritos ao conteúdo da conversa
  icons/                  Ícone original do Instances
  instances.gresource.xml    Recursos incorporados
  instances.in              Launcher configurado pelo Meson
po/                       Infraestrutura Gettext
tests/                    Testes do estado e do contrato HTTP
tools/                    Verificação do runtime, teste GTK e prévia visual
docs/                     Guia do porte e pendências de distribuição
reference/libadwaita/      Biblioteca e Adwaita Demo originais para estudo
```

O código original da biblioteca foi movido para `reference/libadwaita/`,
incluindo o manifesto do demo que já tinha alterações locais. O ZIP enviado
não foi modificado. A aplicação depende do runtime instalado, e não compila
nem incorpora essa biblioteca de referência.

A interface apresenta o estado do controlador. HTTP e início do serviço
ocorrem em threads de trabalho; atualizações da interface são entregues pela
thread principal do GLib. Cada geração possui uma identificação para descartar
callbacks antigos e callbacks recebidos depois do encerramento.

Veja [o guia do porte](docs/PORTE-LIBADWAITA.md) para relacionar cada componente
com o exemplo correspondente do Adwaita Demo.

## Compilar, testar e instalar

Requer Meson, Ninja, `glib-compile-resources` e Gettext.

```bash
meson setup build --prefix="$HOME/.local"
meson compile -C build
meson test -C build --print-errorlogs
meson devenv -C build instances
```

Execute os comandos seguintes apenas se o anterior terminar com sucesso.
Se o build já existir, use `meson setup --reconfigure build` e informe o prefixo
desejado. O launcher do build utiliza os recursos compilados em `meson devenv`.

Para instalar, depois de fechar o aplicativo:

```bash
meson install -C build
"$HOME/.local/bin/instances"
```

O executável é instalado em `bin/`, os módulos privados e GResource em
`share/instances/`, o ícone em `share/icons/hicolor/` e o arquivo desktop em
`share/applications/`. Também há um ícone simbólico para o aplicativo.

A instalação pode ser verificada em staging:

```bash
meson install -C build --destdir /tmp/instances-stage
```

O staging não altera os caminhos finais do launcher. Para executar inteiramente
em `/tmp`, configure outro build com `--prefix=/tmp/instances-install`.

## Verificação sem compilar

```bash
python3 tools/check_runtime.py
python3 -m unittest discover -s tests -v
PYTHONPATH=. python3 tools/ui_smoke.py
```

O teste GTK precisa de um display. Sem display, retorna código 77 e o Meson
registra o teste como ignorado. Ele usa dados simulados e não inicia Ollama,
`systemctl` nem downloads. Verifica templates, ações, rascunhos, seleção de
modelos, cancelamento, diálogos, busca e adaptação para uma janela de 390px.

Para uma prévia com dados fictícios:

```bash
python3 tools/ui_preview.py
python3 tools/ui_preview.py --empty
python3 tools/ui_preview.py --narrow
python3 tools/ui_preview.py --dark
```

As opções podem ser combinadas. A prévia não faz chamadas de rede. Usa uma
instância independente para não interferir em um Instances já aberto.

## Traduções e distribuição

Os textos originais estão em português e marcados para Gettext. Gere o catálogo:

```bash
meson compile -C build instances-pot
```

Adicione traduções em `po/<idioma>.po` e registre os idiomas em `po/LINGUAS`.
Ao editar os catálogos portugueses, atualize também os arquivos usados na execução direta:

```bash
msgfmt po/pt.po -o data/locale/pt/LC_MESSAGES/instances.mo
msgfmt po/pt_BR.po -o data/locale/pt_BR/LC_MESSAGES/instances.mo
```
O nome aparece como **Instâncias** em português (`pt` e `pt_BR`) e **Instances** nos demais idiomas. Os demais textos permanecem em português nesta versão.

Conforme solicitado, **autoria, licença e endereço público permanecem pendentes**.
O identificador `com.example.Instances` também é provisório. A versão é `0.1`.
Esses campos e os metadados AppStream precisam ser concluídos para a distribuição do aplicativo.
A adoção dos componentes nativos não equivale a aprovação no GNOME Circle;
consulte [as pendências de distribuição](docs/DISTRIBUICAO.md).

## Publicar no GitHub

Consulte [o guia de publicação](docs/GITHUB.md).
