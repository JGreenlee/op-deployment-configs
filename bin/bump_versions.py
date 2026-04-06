import json
import os

# get a list of all programs from the configs directory
configs = [
    c for c in os.listdir('configs')
    if not c.startswith('stage-')
    and not c.startswith('dev-')
]

# or, specify programs manually:
# programs = [
#     'denver-casr.nrel-op.json',
#     'nrel-commute.nrel-op.json',
#     'open-access.nrel-op.json',
#     'ride2own.nrel-op.json',
#     'smart-commute-ebike.nrel-op.json',
#     # ...
# ]

for config in configs:
    with open(os.path.join("configs", config), "r") as f:
        data = json.load(f)
    data["version"] += 1
    with open(os.path.join("configs", config, ), "w", encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
        f.write("\n")
    print(f"Updated version in {config} to {data['version']}")
