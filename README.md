# python_diagnostic_base_class

Standalone logging + performance + instance-naming base class. Merges the best ideas from [SWADL](https://github.com/akienm/swadl) and [agent_datacenter](https://github.com/akienm/agent_datacenter). No dependency on either.

## Install

```bash
pip install python-diagnostic-base-class
```

## Quick start

```python
from diagnostic_base import DiagnosticBase

class MyDevice(DiagnosticBase):
    def run(self):
        self.info("starting")
        with self.stopwatch("do_work") as t:
            ...  # your work here
        self.logger.perf(f"elapsed={t.elapsed_s:.3f}s")

device = MyDevice(device_id="mydevice", name="device")
device.run()
```

## Features

### Tagged logging (loguru backend)

```python
obj.info("plain log")                    # standard INFO
obj.logger.perf("stopwatch entry")       # INFO + tag=perf
obj.logger.perf.debug("verbose perf")   # DEBUG + tag=perf
```

Tags are created on demand via `__getattr__` — no registration needed.

### Instance naming

Explicit (always works):
```python
sensor = MyDevice(name="left_sensor")
sensor.get_name()  # → "left_sensor"
```

gc auto-discovery (works for module/class-scope variables):
```python
# at module scope — gc finds "my_sensor" in module dict
my_sensor = MyDevice()
my_sensor.get_name()  # → "my_sensor"
```

Hierarchical:
```python
parent = MyDevice(name="rack")
child = MyDevice(name="slot1", parent=parent)
child.get_name()  # → "rack.slot1"
```

### Performance stopwatch + CSV rolling log

```python
with self.stopwatch("page_load") as t:
    load_page()
# writes to datacenter_logs/<device_id>/perf/YYYY-MM-DD.perf.csv
# columns: ts_start, ts_end, device_id, class_name, stopwatch_id, comment, elapsed_s, success
# prunes files older than 10 days on write
```

### Substitution engine

```python
result = MyDevice.resolve_substitutions("{greeting} {target}", {"greeting": "hello", "target": "world"})
# → "hello world"
# nested substitutions resolve up to 20 iterations; unknown keys left intact as {key}
```

### kwargs → attributes

```python
obj = MyDevice(color="blue", count=42)
obj.color   # "blue"
obj.count   # 42
```

### Dump / bannerize

```python
print(obj.bannerize())  # readable banner of public instance state
d = obj.dump()          # dict of public attributes
```

## CSV columns

| Column | Description |
|---|---|
| ts_start | ISO 8601 UTC wall-clock start |
| ts_end | ISO 8601 UTC wall-clock end |
| device_id | from DiagnosticBase(device_id=...) |
| class_name | subclass name |
| stopwatch_id | label passed to stopwatch() |
| comment | optional comment string |
| elapsed_s | float seconds |
| success | True unless an exception escaped the with-block |
