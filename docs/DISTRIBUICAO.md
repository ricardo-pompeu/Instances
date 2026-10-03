# Pendências de distribuição

Por solicitação do autor do pedido, estes dados não foram inventados nem definidos:

- Autoria e mantenedores.
- Licença do aplicativo e do ícone enviado.
- URL pública, repositório e endereço para relatar problemas.
- Identificador de aplicação definitivo, associado ao projeto ou domínio escolhido.

`com.example.Instances` serve para desenvolvimento. A aplicação, o recurso,
o desktop e os ícones usam o mesmo identificador provisório.

O arquivo `.desktop`, ícones, launcher, GResource, integração Gettext e instalação
Meson estão presentes. Não foi instalado um arquivo AppStream incompleto: ele deve
ser acrescentado quando autoria, licença e URLs estiverem definidos, incluindo
resumo, descrição, releases e capturas reais da aplicação.

Antes de distribuir:

1. Definir os campos acima e adicionar a licença correspondente.
2. Criar metadados AppStream e validar com `appstreamcli validate --no-net`.
3. Decidir a distribuição e empacotamento. Um Flatpak precisa de acesso à rede
   para a API local; não deve presumir acesso a `systemctl` do host. A integração
   atual foi mantida para execução nativa.
4. Testar o Ollama real: listagem, download, streaming, interrupção e desconexão.
5. Revisar navegação por teclado, leitor de tela, alto contraste, fonte grande,
   tema escuro e traduções no desktop de destino.
6. Verificar os critérios vigentes do GNOME Circle e suas condições de candidatura.

O código da biblioteca em `reference/libadwaita/` conserva sua licença e créditos
originais. Essa licença não deve ser confundida com uma decisão de licença para
o Instances, que permanece pendente.

Referências: [GNOME HIG](https://developer.gnome.org/hig/),
[GNOME Circle](https://circle.gnome.org/) e
[critérios de revisão](https://gitlab.gnome.org/Teams/Releng/AppOrganization/-/blob/main/AppCriteria.md).
