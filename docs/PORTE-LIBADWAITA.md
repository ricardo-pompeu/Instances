# Porte do Instances para libadwaita

O projeto enviado já utilizava GTK 4 e libadwaita. O porte mantém a arquitetura
Python e a integração Ollama, substituindo composição visual artesanal por
componentes da biblioteca e completando comportamentos da sessão.

## Componentes e referências

| Área | Implementação no Instances | Referência preservada |
|---|---|---|
| Janela e recursos | `instances/application.py`, `data/ui/window.ui` | `reference/libadwaita/demo/adwaita-demo.c`, `adw-demo-window.ui` |
| Headerbars | `AdwHeaderBar` dentro de `AdwToolbarView` | `demo/adw-demo-window.ui`, `src/adw-header-bar.c` |
| Conversas | `AdwSidebar`, `AdwSidebarSection`, `AdwSidebarItem` | `demo/adw-demo-window.ui`, `src/adw-sidebar.c` |
| Busca | `GtkSearchBar`, `GtkSearchEntry`, `GtkStringFilter` | `demo/adw-demo-window.ui` |
| Modelo | `AdwPreferencesGroup` e `AdwComboRow` | `demo/pages/lists/adw-demo-page-lists.ui` |
| Botões | `GtkButton`, `GtkMenuButton`, `AdwButtonContent` e ações Gio | `demo/pages/buttons/`, `demo/pages/toasts/` |
| Cards | Botões padrão nas sugestões; classe `card` no compositor | `demo/pages/styles/adw-style-demo-dialog.ui`, `doc/style-classes.md` |
| Conexão | `AdwBanner`, estados de ação, `GtkSpinner` | `demo/pages/banners/` |
| Downloads | `GtkProgressBar`, fração publicada pelo controlador | Contrato `/api/pull` original do Instances |
| Navegação adaptativa | `AdwOverlaySplitView` e `AdwBreakpoint` | `demo/pages/split-views/` |
| Área legível | `AdwClamp`, texto com quebra de palavras | `demo/pages/clamp/` |
| Tela inicial | `AdwStatusPage` com sugestões | `demo/pages/welcome/` |
| Feedback | `AdwToastOverlay` e `AdwToast` | `demo/pages/toasts/` |
| Diálogos | `AdwAlertDialog`, `AdwAboutDialog`, `AdwShortcutsDialog` | `demo/pages/alerts/`, `demo/pages/about/`, `demo/shortcuts-dialog.ui` |

Na coluna de referências, os caminhos abreviados `demo/`, `src/` e `doc/`
são relativos a `reference/libadwaita/`.

O runtime adotado é GTK >= 4.22 e libadwaita >= 1.9. A própria libadwaita
1.9 exige GTK >= 4.21.1; para este aplicativo, a verificação usa a versão
estável 4.22 como mínimo.

## Layout

```text
AdwApplicationWindow
└── AdwToastOverlay
    └── AdwOverlaySplitView
        ├── GtkBox (InstancesSidebar)
        │   └── AdwToolbarView
        │       ├── AdwHeaderBar (nova conversa e busca)
        │       ├── GtkSearchBar
        │       └── AdwSidebar → seção → itens das conversas
        └── AdwToolbarView
            ├── AdwHeaderBar (painel, título e menu)
            ├── AdwBanner (problemas de conexão ou ausência de modelos)
            ├── AdwClamp → AdwPreferencesGroup → AdwComboRow
            ├── Progresso do download, enquanto necessário
            ├── GtkStack (tela inicial ou mensagens roláveis)
            └── Barra inferior → AdwClamp → compositor com classe card
```

`AdwOverlaySplitView` mantém o chat acessível ao revelar o painel de conversas
como sobreposição. É uma escolha de composição para esta aplicação. O demo
principal da biblioteca usa `AdwNavigationSplitView` para navegar entre exemplos;
ambos os componentes estão disponíveis e resolvem padrões diferentes.

O breakpoint `max-width: 700sp` recolhe a divisão. A sidebar assume
`AdwSidebarMode.PAGE` quando recolhida e volta ao modo `SIDEBAR` em larguras
maiores. A largura mínima caiu de 560 para 360px e a altura mínima de 720 para
360px. O limite não é uma garantia para qualquer escala de fonte: revise também
com fonte grande e traduções mais longas no ambiente de destino.

As headerbars preservam o gerenciamento automático dos controles da janela,
respeitando a posição configurada pelo sistema. Os botões têm tooltips; o campo
de mensagem tem nome e descrição acessíveis. São cuidados implementados, não
uma certificação de acessibilidade: faça também a inspeção com leitor de tela.

## Estado e comportamento

- Ações Gio são compartilhadas por botões, menu e atalhos.
- Envio só fica habilitado com servidor conectado, modelo disponível e texto.
- Uma nova conversa limpa a área de mensagens. A implementação anterior podia
  manter balões da conversa anterior ao criar uma nova.
- O rascunho pertence à conversa e é restaurado ao trocar de item.
- O seletor bloqueia callbacks durante a substituição do modelo de dados,
  preservando o modelo escolhido pela conversa.
- Sem conexão, o modelo previamente escolhido é preservado para reconexão.
- Limpeza usa diálogo destrutivo e tem Cancelar como resposta padrão.
- Download mostra fração quando disponível e pulsa durante fases indeterminadas.
- Respostas recebem botão de cópia próprio. O menu também copia a última
  resposta concluída da conversa selecionada.
- Streaming solicita linhas HTTP sem aguardar o bloco padrão de 512 bytes.
- A rolagem acompanha a resposta enquanto o usuário está próximo do final;
  callbacks de rolagem são agrupados para evitar um callback por fragmento.
- Os toasts não interpretam como markup o texto recebido do servidor.

## Estilos

O CSS não redefine estilos globais de botões, dropdowns ou sidebars. A biblioteca
fornece classes como `card`, `heading`, `document`, `caption`, `dimmed`, `flat`,
`circular` e `suggested-action`.

A personalização restante consiste no fundo discreto das mensagens do usuário e
na transparência do TextView dentro do compositor. Usa variáveis CSS de tema,
como `--accent-bg-color` e `--card-bg-color`, sem impor uma paleta clara ou escura.

O ícone colorido enviado foi preservado. Um ícone simbólico foi acrescentado para
os contextos que usam representação monocromática.

## Roteiro para continuar estudando

1. Abra `data/ui/window.ui` e identifique cada ramo do layout acima.
2. Leia `_actions()` e `_changed()` em `instances/ui/window.py`.
3. Leia `instances/ui/sidebar.py` junto de `data/ui/sidebar.ui`.
4. Acompanhe `gerar()`, `_fragment()` e `_finished()` no controlador.
5. Compare os templates com as referências da tabela.
6. Teste uma janela estreita, tema escuro e navegação por teclado.

Fontes de design: [GNOME HIG](https://developer.gnome.org/hig/),
[sidebars](https://developer.gnome.org/hig/patterns/nav/sidebars.html),
[headerbars](https://developer.gnome.org/hig/patterns/containers/header-bars.html),
[listas enquadradas](https://developer.gnome.org/hig/patterns/containers/boxed-lists.html).
