import base64
import socket
from freebox_api import Freepybox

async def get_freebox_share_path(fbx: Freepybox, file_path, path_to_share):
    host = fbx._access.base_url.removeprefix("https://").split(":")[0]
    for share_to_try in await fbx._access.get("share_link"):
        share_path = base64.b64decode(share_to_try["path"]).decode()
        if (path_to_share.rstrip("/") + "/").startswith(share_path.rstrip("/") + "/"):
            share = share_to_try
            break
    else:
        share = await fbx._access.post(
            "share_link/",
            {"path": base64.b64encode(path_to_share.encode()).decode(), "expire": 0, "full_url": ""},
        )
    path = base64.b64decode(share["path"].encode()).decode()
    url = share["fullurl"]
    try:
        ip = socket.gethostbyname(host)
    except OSError:
        pass
    else:
        url = url.replace(ip, host, 1)
    return url.rstrip("/") + "/" + file_path.removeprefix(path + "/")
