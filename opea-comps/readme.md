## Running Ollama Third Party

### Install Docker
To run docker without root:
```sh
sudo groupadd docker
sudo usermod -aG docker $USER
newgrp docker
```

### Get LLM model ID
[Ollama Library](https://ollama.com/library)

### Get Host IP 
```sh
sudo apt install net-tools
ifconfig
```
Or try `$(hostname -I | awk '{print $1}')`

HOST_IP=$(hostname -I | awk '{print $1}') NO_PROXY=localhost LLM_ENDPOINT_PORT=8008 LLM_MODEL_ID="llama3.2:1b" docker compose up

Use [Ollama API](https://github.com/ollama/ollama/blob/main/docs/api.md) to make calls once the server is running.

### Pull a model
```sh
curl http://localhost:8008/api/pull -d '{
  "model": "llama3.2:1b"
}'
```


### Generate a request
```sh
curl http://localhost:8008/api/generate -d '{
  "model": "llama3.2:1b",
  "prompt": "Why is the sky blue?"
}'
```