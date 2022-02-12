import os
import random

import requests

from log import color, logger
from util import get_now, make_sure_dir_exists, show_progress


def download_file(url: str, download_dir=".cached/downloads", filename="", connect_timeout=10) -> str:
    download_dir = os.path.realpath(download_dir)
    filename = filename or os.path.basename(url)

    start_time = get_now()

    target_file_path = os.path.join(download_dir, filename)

    logger.info(f"开始下载 {url} 到 {target_file_path}")
    response = requests.get(url, stream=True, timeout=connect_timeout)

    if response.status_code != 200:
        raise Exception(f"下载失败，状态码 {response.status_code}")

    make_sure_dir_exists(download_dir)

    with open(target_file_path, "wb") as f:
        total_length = response.headers.get("content-length")

        if total_length is None:  # no content length header
            f.write(response.content)
        else:
            dl = 0
            total_length = int(total_length)
            for data in response.iter_content(chunk_size=4096):
                # filter out keep-alive new lines
                if not data:
                    continue

                f.write(data)

                dl += len(data)
                show_progress(filename, total_length, dl)

    end_time = get_now()

    logger.info(color("bold_yellow") + f"下载完成，耗时 {end_time - start_time}")

    return target_file_path


def download_latest_github_release(download_dir: str) -> str:
    release_file_path = "fzls/djc_helper/releases/latest/download/djc_helper.7z"

    # 先加入比较快的几个镜像
    urls = [
        f"https://pd.zwc365.com/seturl/https://github.com/{release_file_path}",
        f"https://gh.xiu.workers.dev/https://github.com/{release_file_path}",
        f"https://gh.api.99988866.xyz/https://github.com/{release_file_path}",
        f"https://github.rc1844.workers.dev/{release_file_path}",
        f"https://ghgo.feizhuqwq.workers.dev/https://github.com/{release_file_path}",
        f"https://git.yumenaka.net/https://github.com/{release_file_path}",
        f"https://ghproxy.com/https://github.com/{release_file_path}",
    ]
    # 随机乱序，确保均匀分布请求
    random.shuffle(urls)

    # 最后加入几个慢的镜像和源站
    urls.extend(
        [
            f"https://download.fastgit.org/{release_file_path}",
            f"https://github.com/{release_file_path}",
        ]
    )

    # 开始依次下载，直到成功下载
    for idx, url in enumerate(urls):
        try:
            return download_file(url, download_dir)
        except Exception as e:
            logger.error(f"{idx + 1}/{len(urls)}: 下载失败，异常内容： {e}，将继续尝试下一个github镜像")
            logger.debug("详细异常信息", exc_info=e)
            continue

    raise Exception("所有镜像都下载失败")


if __name__ == "__main__":
    download_latest_github_release(".cached/downloads")