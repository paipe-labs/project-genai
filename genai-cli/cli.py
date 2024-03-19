import typer
import typing
import os
import csv
import sys
import re
import prettytable
from rich import print as rprint
import subprocess
import docker
import pandas as pd


NODES_DATA_FILE = os.environ.get("NODES_DATA_FILE", "")
DEFAULT_DOCKER_IMAGE = os.environ.get("DEFAULT_DOCKER_IMAGE", "")
DEFAULT_PROV_SCRIPT = os.environ.get("DEFAULT_PROV_SCRIPT", "")

VASTAI_CREATE_CMD = """vastai create instance {id} --image {image} --env '-e BACKEND_SERVER={backend} -e PROVISIONING_SCRIPT="{prov_script}" ' --onstart-cmd 'env | grep _ >> /etc/environment; /opt/ai-dock/bin/init.sh & npx ts-node public/run.js -b {backend} -t comfyUI -i ${{DIRECT_ADDRESS}}:${{COMFYUI_PORT}};'"""


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
        rprint("[red]No image instance passed and DEFAULT_DOCKER_IMAGE not set.[/red]")
        return
    if prov_script == "":
        rprint("[red]DEFAULT_PROV_SCRIPT environment variable not set.[/red]")
        return

    if platform == "local":
        try:
            container = docker_client.containers.run(
                image=image,
                environment=[
                    "BACKEND_SERVER={b}".format(b=backend),
                    "PROVISIONING_SCRIPT={script}".format(script=prov_script),
                ],
                detach=True,
            )
            node_id = container.short_id
        except Exception as err:
            rprint(err)
            return

    elif platform == "vastai":
        if vastai_iid is None:
            rprint(
                "[red]Creating node in vast.ai with no known instance ID is not supported.",
                "Choose an instance via 'vastai search offers' command and pass its ID as an argument '--vastai-iid'[/red]",
            )
            return

        try:
            result = subprocess.run(
                VASTAI_CREATE_CMD.format(
                    id=vastai_iid, image=image, backend=backend, prov_script=prov_script
                ),
                check=True,
                capture_output=True,
                shell=True,
            ).stdout.decode()

            nums = re.findall(r"\d+", result)
            if result.startswith("Started") and len(nums) == 1:
                node_id = nums[0]
            else:
                rprint(
                    "[red]Creation failed. Instance id used:[/red] {id}\n".format(
                        id=vastai_iid
                    ),
                    result,
                )
                return
        except Exception as err:
            rprint(
                "[red]Creation failed. Instance id used:[/red] {id}\n".format(
                    id=vastai_iid
                ),
                err,
            )
            return

    else:
        rprint("[red]Platform type not supported: [/red]{p}".format(p=platform))
        return

    with open(NODES_DATA_FILE, "a", newline="") as data_file:
        writer = csv.writer(
            data_file, delimiter=",", quotechar="|", quoting=csv.QUOTE_MINIMAL
        )

        writer.writerow([node_id, platform, backend, image])

    rprint("[green]Created node id:[/green]\n{id}".format(id=node_id))


@app.command(help="Delete existing running node")
def delete_node(node_id: str):
    nodes_df = pd.read_csv(NODES_DATA_FILE, sep=",", dtype={"id": "string"})
    nodes_row = nodes_df[nodes_df["id"] == node_id]
    if nodes_row.shape[0] == 0:
        rprint(
            "[red]Unable to delete node {id}: no data found in file. Has it been created through the cli tool?[/red]".format(
                id=node_id
            )
        )
        return

    node_row = nodes_row.iloc[0].values.tolist()
    if node_row[1] == "local":
        try:
            container = docker_client.containers.get(node_id)
            container.kill()
        except Exception as err:
            rprint("[red]Deletion failed[/red]\n", err)
            return

    elif node_row[1] == "vastai":
        try:
            result = subprocess.run(
                ["vastai", "destroy", "instance", node_id],
                check=True,
                capture_output=True,
            ).stdout.decode()

            if not result.startswith("destroying instance"):
                rprint("[red]Deletion failed[/red]\n", result)
                return

        except Exception as err:
            rprint("[red]Deletion failed[/red]\n", err)
            return
    else:
        rprint("[red]Platform not supported: {p}[/red]".format(p=node_row[1]))
        return

    nodes_df = nodes_df[nodes_df["id"] != node_id]
    nodes_df.to_csv(NODES_DATA_FILE, index=False, sep=",")
    rprint("[green]Deleted node id:\n{id}[/green]".format(id=node_id))


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

    # Initialising the file to store nodes data in
    if os.stat(NODES_DATA_FILE).st_size == 0:
        with open(NODES_DATA_FILE, "w+") as nodes_file:
            writer = csv.writer(
                nodes_file, delimiter=",", quotechar="|", quoting=csv.QUOTE_MINIMAL
            )
            writer.writerow(["id", "platform", "backend", "image"])

    app()
