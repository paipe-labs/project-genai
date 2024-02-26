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


NODES_DATA_PATH = os.environ.get("NODES_DATA_PATH", "")
DEFAULT_DOCKER_IMAGE = os.environ.get("DEFAULT_DOCKER_IMAGE", "")

app = typer.Typer(no_args_is_help=True, add_completion=False)
docker_client = docker.from_env()


@app.command(help="Create and run a node")
def create_node(platform: str, backend: str, image=DEFAULT_DOCKER_IMAGE, vastai_iid=None):
    if image == "":
        rprint("[red]No image instance passed and no default docker image set.[/red]")
        return

    if platform == "local":
        try:
            container = docker_client.containers.run(
                image=image,
                detach=True,
                environment=["--backend={b}".format(b=backend)],
            )
        except Exception as err:
            rprint(err)
            return

        node_id = container.short_id
    elif platform == "vastai":
        if vastai_iid is None:
            rprint(
                "[red]Creating node in vast.ai with no known instance ID is not supported.",
                "Choose an instance via 'search offers' command and pass it as an argument '--vastai_iid'.[/red]",
            )
            return

        try:
            # TODO: pass backend  --env '--backend=backend'
            result = json.loads(
                subprocess.run(
                    [
                        "vastai",
                        "create",
                        "instance",
                        vastai_iid,
                        "--image={img}".format(img=image),
                    ],
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
            return
        node_id = result["new_contract"]

    else:
        rprint("[red]Platform type not supported: [/red]{p}".format(p=platform))
        return

    with open(NODES_DATA_PATH, "a", newline="") as data_file:
        writer = csv.writer(
            data_file, delimiter=";", quotechar="|", quoting=csv.QUOTE_MINIMAL
        )

        writer.writerow([node_id, platform, backend, image])

    rprint("[green]Created node id:[/green]\n{id}.".format(id=node_id))


@app.command(help="Delete existing running node")
def delete_node(node_id: str):
    nodes_df = pd.read_csv(NODES_DATA_PATH, sep=";")
    node_row = nodes_df[nodes_df["id"] == node_id].iloc[0].values.tolist()
    nodes_df = nodes_df[nodes_df["id"] != node_id]
    nodes_df.to_csv(NODES_DATA_PATH, index=False, sep=";")

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
    with open(NODES_DATA_PATH, "r") as nodes_data:
        nodes_table = prettytable.from_csv(nodes_data)
    print(nodes_table)


if __name__ == "__main__":
    if "NODES_DATA_PATH" not in os.environ:
        rprint(
            "[red]Missing env variable [/red]'NODES_DATA_PATH'[red]: file path for persistent storage of node ids.[/red]"
        )
        sys.exit(1)
    if "CONTAINER_API_KEY" not in os.environ:
        rprint(
            "[red]Missing env variable [/red]'CONTAINER_API_KEY'[red] needed to access vast.ai cli.[/red]"
        )
        sys.exit(1)

    # Initialising the file to store nodes in
    if not os.path.exists(NODES_DATA_PATH):
        with open(NODES_DATA_PATH, "w+") as nodes_file:
            writer = csv.writer(
                nodes_file, delimiter=";", quotechar="|", quoting=csv.QUOTE_MINIMAL
            )
            writer.writerow(["id", "platform", "backend", "image"])

    app()

