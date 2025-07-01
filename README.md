# InfraCom

Projeto desenvolvido para a disciplina **Infraestrutura de Comunicações - 2025.1**. Consiste na construção de um chat com sala única utilizando Python e comunicação via UDP, dividido em três etapas com complexidade crescente.

## 📦 Objetivo

Projeto de chat com sala única em Python usando UDP. Inclui envio e devolução de arquivos, implementação do protocolo RDT 3.0 para transferência confiável e chat multiusuário com comandos via terminal: conexão, lista de usuários, amigos, banimento e mais.

## 🛠️ Tecnologias e Ferramentas

- Python 3.x
- Biblioteca `socket` para comunicação via UDP
- Terminal/linha de comando para interface do usuário

## 📚 Etapas do Projeto

### ✅ Etapa 1 – Transferência de Arquivos com UDP
- Comunicação com UDP utilizando `socket`.
- Envio e devolução de arquivos em pacotes de até 1024 bytes.
- Alteração do nome do arquivo no retorno.

### ✅ Etapa 2 – Transferência Confiável (RDT 3.0)
- Implementação do protocolo RDT 3.0.
- Simulação de perdas com timeout e retransmissão.
- Transmissão confiável feita na aplicação sobre UDP.

### ✅ Etapa 3 – Chat com Sala Única
- Chat multiusuário com comandos via terminal.
- Comandos: conexão, sair, listar usuários, adicionar/remover amigos, banir usuários.
- Formatação padrão das mensagens exibidas:
  ```
  <IP>:<PORTA>/~<nome_usuario>: <mensagem> <hora-data>
  ```

## 💻 Como Executar

Cada etapa possui sua própria pasta com instruções específicas. Em geral:

```bash
# No terminal do servidor
python3 server.py

# Em um ou mais terminais de clientes
python3 client.py
```

> Requisitos: Python 3 instalado

## 📁 Estrutura do Repositório

```
InfraCom/
├── etapa1/           # UDP - envio/devolução de arquivos
├── etapa2/           # UDP + RDT 3.0 confiável
├── etapa3/           # Chat multiusuário funcional
└── README.md         # Este arquivo
```

## 👥 Equipe

**Equipe 4 – InfraCom 2025.1**

- Giovanna de Cassia Silva – [gcs5@cin.ufpe.br](mailto:gcs5@cin.ufpe.br)  
- Luís Paulo Silva Trevisan – [lpst@cin.ufpe.br](mailto:lpst@cin.ufpe.br)  
- Wilton Alves Sales – [was7@cin.ufpe.br](mailto:was7@cin.ufpe.br)  
- Victória Xavier Queiroz – [vxq@cin.ufpe.br](mailto:vxq@cin.ufpe.br)  
- Mateus Freire Vieira Damasceno – [mfvd@cin.ufpe.br](mailto:mfvd@cin.ufpe.br)

## 📌 Observações

- Cada entrega deve conter seu próprio `README.md` com instruções específicas.
- Comentários no código são obrigatórios.
- Funcionalidades e comandos devem seguir rigorosamente as regras do enunciado.
