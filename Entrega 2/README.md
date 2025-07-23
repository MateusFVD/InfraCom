# Entrega 2

## RDT_DATA_CHUNK_SIZE
Essa seção explica o cálculo do valor de `40 bytes` adotados para o overhead do JSON.

# **Overhead Estimado para um Pacote de Dados (do Remetente):**

A estrutura do JSON para o pacote de dados é:
``` json
{"seq_num": 0, "data": "seus_dados_aqui"}
```

Vamos somar os caracteres literais e o espaço para os valores:

    `{`: 1 byte

    `"seq_num"`: 9 bytes

    `:` : 2 bytes (dois pontos e um espaço, embora o espaço possa variar dependendo do serializador JSON, é bom ser conservador)

    `0` (para seq_num, que pode ser 0 ou 1): 1 byte

    `, `: 2 bytes (vírgula e um espaço)

    `"data"`: 6 bytes

    `:` : 2 bytes

    `""` (aspas para a string de dados): 2 bytes

    `}`: 1 byte

**Total mínimo de overhead para um pacote de dados**: 1+9+2+1+2+6+2+2+1 = `26 bytes`

# **Overhead Estimado para um Pacote ACK (do Receptor):**

A estrutura do JSON para o pacote ACK é:
``` json
{"type": "ACK", "seq_num": 0}
```

Vamos somar os caracteres literais e o espaço para os valores:

    `{`: 1 byte

    `"type"`: 6 bytes

    `:` : 2 bytes

    `"ACK"`: 5 bytes

    `, `: 2 bytes

    `"seq_num"`: 9 bytes

    `:`` : 2 bytes

    `0` (para seq_num): 1 byte

    `}`: 1 byte

**Total mínimo de overhead para um pacote ACK:** 1+6+2+5+2+9+2+1+1 = `29 bytes`

Como nossa maior estimativa mínima é de `29 bytes` de overhead, decidimos colocar `40 bytes` para haver uma margem de segurança

## 💻 Como Executar

Cada etapa possui sua própria pasta com instruções específicas. Em geral:

```bash
# No terminal do servidor
python3 server_rdt.py

# Em um ou mais terminais de clientes
python3 client_rdt.py
```

> Requisitos: Python 3 instalado

## Sobre 

## 👥 Equipe

**Equipe 4 – InfraCom 2025.1**

- Giovanna de Cassia Silva – [gcs5@cin.ufpe.br](mailto:gcs5@cin.ufpe.br)  
- Luís Paulo Silva Trevisan – [lpst@cin.ufpe.br](mailto:lpst@cin.ufpe.br)  
- Wilton Alves Sales – [was7@cin.ufpe.br](mailto:was7@cin.ufpe.br)  
- Victória Xavier Queiroz – [vxq@cin.ufpe.br](mailto:vxq@cin.ufpe.br)  
- Mateus Freire Vieira Damasceno – [mfvd@cin.ufpe.br](mailto:mfvd@cin.ufpe.br)
