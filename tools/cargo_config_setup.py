# -*- coding: utf-8 -*-
"""cargo_config_setup.py — 写 ~/.cargo/config.toml（crates.io 走 rsproxy 镜像）。"""
import os

CONF = """[source.crates-io]
replace-with = "rsproxy"

[source.rsproxy]
registry = "sparse+https://rsproxy.cn/index/"

[registries.rsproxy]
index = "sparse+https://rsproxy.cn/index/"

[net]
git-fetch-with-cli = true
"""

out = os.path.join(os.path.expanduser("~"), ".cargo", "config.toml")
os.makedirs(os.path.dirname(out), exist_ok=True)
with open(out, "w", encoding="utf-8", newline="\n") as f:
    f.write(CONF)
print("written:", out)
