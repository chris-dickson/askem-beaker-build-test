import json

{
    "policy": result["policy"].tolist(),
    "OptResults": json.loads(json.dumps(result["OptResults"], default=str)),
}