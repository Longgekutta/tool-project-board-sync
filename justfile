default:
    @python main.py health

setup:
    @python main.py setup

test:
    @python main.py test

health:
    @python main.py health

clean:
    @python main.py clean

sync target="." project="PVT_kwDOB12345":
    @python main.py sync --target {{target}} --project-id {{project}}

status target=".":
    @python main.py status --target {{target}}
