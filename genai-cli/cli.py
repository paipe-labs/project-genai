import typer
import typing
import os
import csv
import sys
import json
import prettytable
from rich import print as rprint
import subprocess
import docker
import pandas as pd


NODES_DATA_FILE = os.environ.get("NODES_DATA_FILE", "")

DEFAULT_DOCKER_IMAGE = os.environ.get("DEFAULT_DOCKER_IMAGE", "")
DEFAULT_PROV_SCRIPT = os.environ.get(
    "PROVISIONING_SCRIPT",
    "https://raw.githubusercontent.com/ai-dock/comfyui/main/config/provisioning/default.sh",
)

VASTAI_CREATE_CMD = """vastai create instance {id} --image {image} --env '-e BACKEND_SERVER={backend} -e PROVISIONING_SCRIPT="{prov_script}' --onstart-cmd "env | grep _ >> /etc/environment; /opt/ai-dock/bin/init.sh & npx ts-node public/run.js -b ${{BACKEND_SERVER}} -t comfyUI -i ${{DIRECT_ADDRESS}}:${{COMFYUI_PORT}};"
"""


app = typer.Typer(no_args_is_help=True, add_completion=False)
docker_client = docker.from_env()


@app.command(help="Create and run a node")
def create_node(
    platform: str,
    backend: str,
    image=DEFAULT_DOCKER_IMAGE,
    prov_script=DEFAULT_PROV_SCRIPT,
    vastai_iid=None,
):
    if image == "":
        rprint("[red]No image instance passed and no default docker image set.[/red]")
        return

    if platform == "local":
        try:
            container = docker_client.containers.run(
                image=image,
                command=["--backend {b}".format(b=backend)],
                environment=[
                    "BACKEND_SERVER={b}".format(b=backend),
                    "PROVISIONING_SCRIPT={script}".format(script=prov_script),
                ],
                detach=True,
            )
        except Exception as err:
            rprint(err)
            return

        node_id = container.short_id
    elif platform == "vastai":
        if vastai_iid is None:
            rprint(
                "[red]Creating node in vast.ai with no known instance ID is not supported.",
                "Choose an instance via 'search offers' command and pass its ID as an argument '--vastai_iid'.[/red]",
            )
            return

        try:
            result = json.loads(
                subprocess.run(
                    VASTAI_CREATE_CMD.format(
                        id=vastai_iid,
                        image=image,
                        backend=backend,
                        prov_script=prov_script,
                    ).split(),
                    check=True,
                    capture_output=True,
                ).stdout
            )
        except subprocess.CalledProcessError as err:
            rprint(err)

        if result["success"] is False:
            rprint(
                "[red]Creation failed. Instance id used:[/red] {id}".format(
                    id=vastai_iid
                )
            )

            # TODO: print vastai answer
            return
        node_id = result["new_contract"]

    else:
        rprint("[red]Platform type not supported: [/red]{p}".format(p=platform))
        return

    with open(NODES_DATA_FILE, "a", newline="") as data_file:
        writer = csv.writer(
            data_file, delimiter=";", quotechar="|", quoting=csv.QUOTE_MINIMAL
        )

        writer.writerow([node_id, platform, backend, image])

    rprint("[green]Created node id:[/green]\n{id}.".format(id=node_id))


@app.command(help="Delete existing running node")
def delete_node(node_id: str):
    nodes_df = pd.read_csv(NODES_DATA_FILE, sep=";")
    node_row = nodes_df[nodes_df["id"] == node_id].iloc[0].values.tolist()
    nodes_df = nodes_df[nodes_df["id"] != node_id]
    nodes_df.to_csv(NODES_DATA_FILE, index=False, sep=";")

    if node_row[1] == "local":
        try:
            container = docker_client.containers.get(node_id)
            container.kill()
        except Exception as err:
            rprint(err)

    elif node_row[1] == "vastai":
        try:
            result = json.loads(
                subprocess.run(
                    ["vastai", "destroy", "instance", node_id],
                    check=True,
                    capture_output=True,
                ).stdout
            )
        except subprocess.CalledProcessError as err:
            rprint(err)

        # TODO process output if any, else check exit status
    else:
        rprint("[red]Platform not supported: {p}.[/red]".format(p=node_row[1]))
        return

    rprint("[green]Deleted node id:\n{id}.[/green]".format(id=node_id))


# @app.command()
# def run_node(node_id: int):
#     pass

# @app.command()
# def stop_node(node_id: int):
#     pass


@app.command("list", help="List currently running nodes")
def list_nodes():
    with open(NODES_DATA_FILE, "r") as nodes_data:
        nodes_table = prettytable.from_csv(nodes_data)
    print(nodes_table)


if __name__ == "__main__":
    if "NODES_DATA_FILE" not in os.environ:
        rprint(
            "[red]Missing env variable [/red]'NODES_DATA_FILE'[red]: file path for persistent storage of node ids.[/red]"
        )
        sys.exit(1)

    # Initialising the file to store nodes in
    if not os.path.exists(NODES_DATA_FILE):
        with open(NODES_DATA_FILE, "w+") as nodes_file:
            writer = csv.writer(
                nodes_file, delimiter=";", quotechar="|", quoting=csv.QUOTE_MINIMAL
            )
            writer.writerow(["id", "platform", "backend", "image"])

    app()
