# Publicar Instances no GitHub

- Nome do repositório sugerido: `instances`.
- Nome do aplicativo: **Instances**; em português: **Instâncias**.
- Descrição sugerida: `Aplicativo GNOME para conversar com modelos locais do Ollama, desenvolvido em Python, GTK 4 e libadwaita.`
- Tópicos sugeridos: `gnome`, `gtk4`, `libadwaita`, `python`, `ollama`, `local-ai`.
- Comando para executar: `python3 -m instances`.
- ID provisório: `com.example.Instances`.

## Preparar um repositório próprio

A pasta de trabalho original ainda contém o histórico Git e o remoto da biblioteca
libadwaita. Use o ZIP `dist/Instances.zip` para iniciar um histórico do aplicativo
em outra pasta. Ele inclui a referência libadwaita com seus créditos e licenças,
mas exclui `.git`, configurações privadas, caches e builds.

Extraia o ZIP em uma pasta nova (o arquivo contém uma pasta `Instances/`):

```bash
unzip /home/ricardo/Projetos/libadwaita/dist/Instances.zip -d "$HOME/Projetos"
cd "$HOME/Projetos/Instances"
git init -b main
git add .
git status
git commit -m "Initial commit: Instances"
```

Se já existir uma pasta `Instances`, escolha outro diretório para a extração.
Se o Git pedir identidade, configure `git config user.name "SEU NOME"` e
`git config user.email "SEU EMAIL"` nesta pasta e repita o commit. Você pode usar
o endereço noreply fornecido pelo GitHub nas configurações da sua conta.

## Enviar

No GitHub, crie um repositório vazio chamado `instances`, escolhendo a visibilidade.
Não adicione README, licença nem .gitignore no formulário, pois o projeto já traz
os arquivos existentes e a licença continua pendente.

Substitua `SEU_USUARIO` pelo seu usuário ou organização:

```bash
git remote add origin https://github.com/SEU_USUARIO/instances.git
git push -u origin main
```

Autentique-se usando GitHub CLI (`gh auth login`, depois `gh auth setup-git`)
ou um token pessoal pelo gerenciador de credenciais. Não insira tokens nos arquivos
ou no endereço do remoto. A senha da conta não é usada para Git via HTTPS.

Para atualizações posteriores, nessa nova pasta:

```bash
git add .
git diff --cached
git commit -m "Descreva a alteração"
git push
```

## Pendências para distribuição

Autoria, licença e URL pública continuam pendentes por escolha do usuário.
Depois de criar o repositório, registre a URL real e defina o ID definitivo,
por exemplo `io.github.SEU_USUARIO.Instances`, atualizando de forma consistente
recursos, configuração, arquivo desktop e ícones. O exemplo não é um ID já configurado.
Consulte [DISTRIBUICAO.md](DISTRIBUICAO.md) para AppStream, empacotamento e GNOME Circle.
O envio do código ao GitHub não publica automaticamente um Flatpak nem uma release.

Documentação oficial: [Adicionar código local ao GitHub](https://docs.github.com/en/migrations/importing-source-code/using-the-command-line-to-import-source-code/adding-locally-hosted-code-to-github?platform=linux).
