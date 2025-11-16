import json

def is_json(myjson):
  try:
    json.loads(myjson)
  except ValueError as e:
    return False
  return True

def singleton(cls):
    instances = {}

    def get_instance(*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]

    return get_instance
  
rpc_functions: dict = {}
def register_rpc(name: str = ""): 
    def decorator(func):
        key = name or func.__name__
        rpc_functions[key] = func
        return func
    return decorator