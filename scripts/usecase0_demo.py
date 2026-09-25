"""Read-only connectivity demo; safe to import."""
from pathlib import Path
import json
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from controller.amarisoft_api import AmarisoftAPI


def main():
    api = AmarisoftAPI()
    try:
        api.connect()
        print(json.dumps(api.send({'message':'ue_get'}),indent=2))
    finally:
        api.disconnect()


if __name__ == '__main__':
    main()
