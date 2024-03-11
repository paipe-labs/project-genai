# CLI

[Github Issue](https://github.com/paipe-labs/project-genai/issues/23)

### Usage:

#### 1. Set environment variables (accessed at build time)

##### Obligatory
- `CLI_NODES_DATA_FILE` - absolute path to a local ***existing*** file for saving nodes data
	
    This file must be either empty (the cli will initialise it itself) or a correct csv file in the format that cli works with. 
    The current header (first row) looks as follows:

	`id,platform,backend,image`

##### Optional

- `NODES_DATA_FILE` - file for saving nodes data in the container
    - default: '/cli/nodes.csv'
- `DEFAULT_DOCKER_IMAGE` - default image to use if no other image is passed to `create-node` command
    - default: 'vvauijij/genai-node-comfyui'
- `DEFAULT_PROV_SCRIPT`
	- default: 'https://raw.githubusercontent.com/ai-dock/comfyui/main/config/provisioning/default.sh'
- `VASTAI_API_KEY` - vast.ai account API Key for vastai cli integration
    - default: (none)

#### 2. Build image

```bash
docker compose up
```
#### 3. Run

Each command can be run with `--help` option.

- `create-node <platform> <backend> --image=<image>`
	- current platforms supported: local, vastai
```bash
docker compose run genai-cli create-node local ws://apiv2.paipe.io:8080

docker compose run genai-cli create-node vastai ws://apiv2.paipe.io:8080 --vastai-iid=7520880
```
- `delete-node <node_id>` - deletes a node created via the local instance of the cli tool (as it has access only to those nodes stored in the local `CLI_NODES_DATA_FILE`)
```bash
docker compose run genai-cli delete-node 34918273
```
- `list` - lists nodes created via the local instance of the cli tool
```bash
docker compose run genai-cli list
```

