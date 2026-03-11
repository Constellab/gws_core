# Refactor: Centralized ID Replacement for Scenario Import

## Problem

During scenario import, the `KEEP_ID` vs `NEW_ID` mode logic is scattered across multiple loaders and factories. Each component independently checks the mode and conditionally copies or generates IDs. This makes the code harder to follow and maintain.

### Current ID Handling Locations

| Object           | Where ID is handled                                      | KEEP_ID behavior               | NEW_ID behavior         |
|------------------|----------------------------------------------------------|--------------------------------|-------------------------|
| Scenario         | `scenario_loader.py:60-61`                               | `scenario.id = zip_scenario.id`| Auto-generated UUID     |
| ProcessModel     | `process_factory.py:349-350`                             | `process_model.id = dto.id`   | Auto-generated UUID     |
| Resource (model) | `resource_loader.py:114-115`                             | `resource_model_id = zip.id`  | `None` (auto-generated) |
| Resource (uid)   | `resource_loader.py:127-129`                             | Keeps original                | New UUID generated      |

## Proposed Refactor

### Core Idea

Always load everything with original IDs (remove `copy_id`/`copy_ids` from all loaders). Then, if `NEW_ID` mode is selected, build an `old_id -> new_id` mapping and replace IDs in-memory **before saving** to the database.

### New Flow

```
1. ScenarioLoader loads scenario, protocol, processes, resource models
   -> All objects keep their ORIGINAL IDs from the export
   -> No copy_id branching in loaders

2. If mode == NEW_ID:
   a. Build ID mapping dict:
      - scenario: old_id -> new_uuid
      - each process_model: old_id -> new_uuid
      - each resource_model: old_id -> new_uuid
   b. Apply mapping to all in-memory objects (see "What Needs Mapping" below)

3. Save everything to DB
```

### What Needs ID Mapping (NEW_ID mode only)

When replacing IDs, these are ALL the cross-references that must be updated:

#### Objects with their own ID
- **Scenario.id** -> new UUID
- **ProcessModel.id** (for all tasks and sub-protocols, recursively) -> new UUID
- **ResourceModel.id** -> new UUID
- **Resource.uid** (internal resource uid) -> new UUID

#### Cross-references (FK / string references)
- **Port resource_ids** (`port._resource_id`): old resource_model_id -> new resource_model_id
  - Set via `Port.load_from_dto()` from `PortDTO.resource_id`
  - Located in all input/output ports of all processes
- **InputTask config** (`"resource_id"` config param): old resource_model_id -> new resource_model_id
  - Stored as a string in `process_model.config` under key `"resource_id"`
- **ResourceModel.parent_resource_id**: old resource_model_id -> new resource_model_id (for children resources)
- **ResourceModel.task_model** FK: old process_id -> new process_id
  - Handled via `ResourceModelLoader` `task_model` parameter

#### References that do NOT need mapping
- **Connectors**: reference processes by `instance_name`, not by ID
- **Interfaces / Outerfaces**: reference processes by `process_instance_name`, not by ID
- **ProtocolModel.processes dict**: keyed by `instance_name`, not by ID
- **ProgressBar**: created at runtime, not during import

### Implementation

#### 1. New class: `ScenarioIdMapper`

```python
class ScenarioIdMapper:
    """Generates new IDs and replaces all cross-references in-memory."""

    _id_mapping: dict[str, str]  # old_id -> new_id

    def __init__(self):
        self._id_mapping = {}

    def generate_new_id(self, old_id: str) -> str:
        new_id = str(uuid4())
        self._id_mapping[old_id] = new_id
        return new_id

    def get_new_id(self, old_id: str | None) -> str | None:
        if old_id is None:
            return None
        return self._id_mapping.get(old_id, old_id)

    def apply_to_scenario(self, scenario: Scenario) -> None:
        scenario.id = self.generate_new_id(scenario.id)

    def apply_to_protocol(self, protocol: ProtocolModel) -> None:
        """Recursively replace IDs in protocol and all sub-processes."""
        protocol.id = self.generate_new_id(protocol.id)
        for process in protocol.processes.values():
            if isinstance(process, ProtocolModel):
                self.apply_to_protocol(process)
            else:
                process.id = self.generate_new_id(process.id)

    def apply_to_resource_models(self, resource_models: dict[str, ResourceModel]) -> dict[str, ResourceModel]:
        """Replace resource model IDs. Returns new dict with updated keys."""
        new_dict = {}
        for old_id, model in resource_models.items():
            model.id = self.generate_new_id(old_id)
            model.parent_resource_id = self.get_new_id(model.parent_resource_id)
            new_dict[old_id] = model  # keep old_id as key for lookup during download
        return new_dict

    def apply_to_ports(self, protocol: ProtocolModel) -> None:
        """Replace resource_ids in all ports recursively."""
        for process in protocol.processes.values():
            for port in process.inputs.ports.values():
                port.set_resource_model_id(self.get_new_id(port.get_resource_model_id()))
            for port in process.outputs.ports.values():
                port.set_resource_model_id(self.get_new_id(port.get_resource_model_id()))
            if isinstance(process, ProtocolModel):
                self.apply_to_ports(process)

    def apply_to_input_task_configs(self, protocol: ProtocolModel) -> None:
        """Replace resource_id in InputTask config values."""
        for process in protocol.processes.values():
            if process.is_input_task():
                old_resource_id = process.get_config_value("resource_id")
                process.set_config_value("resource_id", self.get_new_id(old_resource_id))
            if isinstance(process, ProtocolModel):
                self.apply_to_input_task_configs(process)
```

#### 2. Remove `copy_id` from loaders

**`process_factory.py`**: Remove `copy_id` parameter from `_init_process_model_from_config_dto`, `create_task_model_from_config_dto`, `create_empty_protocol_model_from_config_dto`. Always copy the ID from DTO.

**`protocol_graph_factory.py`**: Remove `copy_ids` field from `ProtocolGraphFactoryFromConfig`.

**`scenario_loader.py`**: Remove the `if self._mode == ShareEntityCreateMode.KEEP_ID` check for scenario ID. Always set `scenario.id = zip_scenario.id`.

**`resource_loader.py`**: Always set `resource_model_id = zip_resource.id`. Remove the NEW_ID uid regeneration.

#### 3. Call `ScenarioIdMapper` in `ScenarioDownloader`

In `build_scenario` (and `update_scenario`), after loading but before saving:

```python
if create_mode == ShareEntityCreateMode.NEW_ID:
    id_mapper = ScenarioIdMapper()
    id_mapper.apply_to_scenario(scenario)
    id_mapper.apply_to_protocol(protocol_model)
    id_mapper.apply_to_resource_models(metadata_resource_models)
    id_mapper.apply_to_ports(protocol_model)
    id_mapper.apply_to_input_task_configs(protocol_model)
```

### Files to Modify

| File | Change |
|------|--------|
| `process/process_factory.py` | Remove `copy_id` param, always copy ID |
| `protocol/protocol_graph_factory.py` | Remove `copy_ids` field |
| `scenario/scenario_loader.py` | Always set scenario.id, remove mode branching |
| `resource/resource_loader.py` | Always set resource_model_id and keep uid |
| `scenario/task/scenario_downloader.py` | Add `ScenarioIdMapper` call before save |
| NEW: `scenario/scenario_id_mapper.py` | New class with all ID replacement logic |

### Benefits

- **Loaders become pure**: no mode awareness, always load with original IDs
- **Single source of truth**: all ID replacement in one class
- **Easier to audit**: one place to check for missing cross-references
- **Explicit mapping**: `old_id -> new_id` dict is traceable for debugging

### Risks

- Must enumerate ALL cross-references. Missing one means dangling reference at save time (FK constraint error, so it fails loudly)
- Resource uid (internal to the Resource object, used for in-memory tracking) needs careful handling during resource content loading
