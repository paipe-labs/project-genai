import docker
import typing


docker_client = docker.from_env()


def create_node(backend: str, image: str, prov_script: str) -> str:
    container = docker_client.containers.run(
        image=image,
        environment=[
            "BACKEND_SERVER={b}".format(b=backend),
            "PROVISIONING_SCRIPT={script}".format(script=prov_script),
        ],
        detach=True,
    )
    return container.short_id


def delete_node(node_id: str):
    container = docker_client.containers.get(node_id)
    container.kill()
