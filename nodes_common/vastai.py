from typing import Optional
import re
import subprocess

VASTAI_CREATE_CMD = """vastai create instance {id} --image {image} --env '-e BACKEND_SERVER={backend} -e PROVISIONING_SCRIPT="{prov_script}" ' --onstart-cmd 'env | grep _ >> /etc/environment; /opt/ai-dock/bin/init.sh & npx ts-node public/run.js -b {backend} -t comfyUI -i ${{DIRECT_ADDRESS}}:${{COMFYUI_PORT}};'"""


def create_node(
        backend: str,
        image: str,
        prov_script: str,
        vastai_iid: Optional[str]):
    if vastai_iid is None:
        try:
            vastai_iid = get_cheapest_vastai_gpu_instance()
        except:
            raise Exception("Unable to pick the vastai_iid")

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
        raise Exception(
            f"Creation failed. Instance id used: {vastai_iid}" + result)
    return node_id


def delete_node(node_id: str):
    try:
        result = subprocess.run(
            ["vastai", "destroy", "instance", node_id],
            check=True,
            capture_output=True,
        ).stdout.decode()

        if not result.startswith("destroying instance"):
            raise Exception(result)
    except Exception as err:
        raise Exception(
            f"Deletion failed for node with id: {node_id}\n" + err)


def get_cheapest_vastai_gpu_instance() -> str:
    result = subprocess.run("vastai search offers 'num_gpus>=1 rentable=True' -o 'dph' | head -n 2",
                            check=True, capture_output=True, shell=True).stdout.decode()
    return result.split('\n')[1].split(' ')[0]
