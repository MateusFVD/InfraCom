# Entrega 3 – Chat com Sala Única

Esta é a terceira e última etapa do projeto da disciplina de Infraestrutura de Comunicações. Nesta fase, foi desenvolvido um chat de sala única multiusuário, que utiliza o protocolo RDT 3.0 implementado na etapa anterior para garantir uma comunicação confiável sobre UDP.

## 💻 Como Executar

Para rodar o projeto, é necessário um terminal para o servidor e um ou mais terminais para os clientes.

1.  **Inicie o servidor:**

    ```bash
    # No terminal do servidor
    python3 server_chat.py
    ```

    O servidor será iniciado e ficará aguardando conexões de clientes.

2.  **Inicie os clientes:**

    ```bash
    # Em um ou mais terminais de clientes
    python3 test_client.py
    ```

    Cada cliente pedirá um nome de usuário para se conectar ao chat.

## ✨ Funcionalidades e Comandos

O chat implementa as seguintes funcionalidades, acessíveis via comandos no terminal do cliente:

### Comandos Principais

  * **`hi, meu nome eh <nome_usuario>`**: Conecta o usuário à sala de chat com o nome especificado. O servidor notifica a todos quando um novo usuário entra na sala.
  * **`bye`**: Desconecta o usuário do chat. Os outros participantes são notificados da sua saída.
  * **`list`**: Exibe a lista de todos os usuários que estão atualmente conectados à sala.

### Gerenciamento de Amigos

  * **`mylist`**: Mostra a sua lista de contatos pessoal, ou seja, os usuários que você marcou como amigos.
  * **`addtomylist <nome_do_usuario>`**: Adiciona um usuário da sala à sua lista de amigos. A partir desse momento, as mensagens enviadas por esse usuário serão exibidas para você com a tag especial `[ amigo ]`.
  * **`rmvfrommylist <nome_do_usuario>`**: Remove um usuário da sua lista de amigos. Após a remoção, a tag `[ amigo ]` deixa de aparecer nas mensagens dele.

### Moderação

  * **`ban <nome_do_usuario>`**: Inicia uma votação para banir o usuário especificado da sala. O banimento só ocorre se a contagem de votos atingir mais da metade dos clientes conectados. A cada voto, o servidor envia uma mensagem para todos no formato `[ nome_do_usuario] ban x/y`, informando o progresso da votação.

### Comunicação

  * **Comunicação Confiável:** Toda a comunicação entre cliente e servidor utiliza o protocolo **RDT 3.0** para garantir a entrega de mensagens.
  * **Formato das Mensagens:** As mensagens são exibidas no formato padrão, incluindo o endereço do remetente, nome de usuário, a mensagem e a data/hora do servidor:
    ```
    <IP>:<PORTA>/~<nome_usuario>: <mensagem> <hora-data>
    ```

## 👥 Equipe

**Equipe 4 – InfraCom 2025.1**

  * Giovanna de Cassia Silva – [gcs5@cin.ufpe.br](mailto:gcs5@cin.ufpe.br)
  * Luís Paulo Silva Trevisan – [lpst@cin.ufpe.br](mailto:lpst@cin.ufpe.br)
  * Wilton Alves Sales – [was7@cin.ufpe.br](mailto:was7@cin.ufpe.br)
  * Victória Xavier Queiroz – [vxq@cin.ufpe.br](mailto:vxq@cin.ufpe.br)
  * Mateus Freire Vieira Damasceno – [mfvd@cin.ufpe.br](mailto:mfvd@cin.ufpe.br)
