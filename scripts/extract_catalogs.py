#!/usr/bin/env python3
"""Extract all catalog data from l2_*.py files into catalogs.json."""

import sys
import json
import importlib
import inspect
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

l2_dir = Path(__file__).parent.parent / "wish_engine"
output = l2_dir / "catalogs.json"

catalogs = {}

for f in sorted(l2_dir.glob("l2_*.py")):
    if f.name == "l2_fulfiller.py":
        continue  # skip base class

    module_name = f"wish_engine.{f.stem}"
    catalog_name = f.stem.replace("l2_", "")

    try:
        mod = importlib.import_module(module_name)
    except Exception as e:
        print(f"SKIP {module_name}: {e}")
        continue

    # Find catalog variable: any module-level list of dicts with "title" key
    items = None
    var_name = None
    for name, obj in inspect.getmembers(mod):
        if (
            isinstance(obj, list)
            and len(obj) > 0
            and isinstance(obj[0], dict)
            and "title" in obj[0]
        ):
            items = obj
            var_name = name
            break

    # Find fulfiller class name
    class_name = None
    for name, obj in inspect.getmembers(mod, inspect.isclass):
        if name.endswith("Fulfiller") and obj.__module__ == module_name:
            class_name = name
            break

    if items:
        catalogs[catalog_name] = {
            "module": module_name,
            "class": class_name or "Unknown",
            "variable": var_name,
            "item_count": len(items),
            "items": items,
        }
        print(f"OK {catalog_name}: {len(items)} items, class={class_name}, var={var_name}")
    else:
        print(f"NO CATALOG {catalog_name}: no list[dict] with 'title' found")

# Write
with open(output, "w") as fout:
    json.dump(catalogs, fout, indent=2, ensure_ascii=False)

print(f"\nExtracted {len(catalogs)} catalogs to {output}")
print(f"Total items: {sum(c['item_count'] for c in catalogs.values())}")
