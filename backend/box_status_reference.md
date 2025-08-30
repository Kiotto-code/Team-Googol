# Box Status Reference - Simplified for 1-Item Boxes

## Box Status (Logical State)
The `status` field represents the logical/workflow state of the box:

### Available States:
- `"available"` - Box is empty and ready to receive 1 item
- `"full"` - Box contains 1 item (at capacity)
- `"collect_request"` - Box is full and requesting collection
- `"maintenance"` - Box is under maintenance
- `"offline"` - Box is not operational

## Door Status (Physical State)
The `door_status` field represents the physical state of the box door:

### Available States:
- `"closed"` - Door is closed
- `"open"` - Door is open

## Typical State Combinations

### Normal Operation:
- `status="available"` + `door_status="closed"` - Empty, ready for 1 item
- `status="full"` + `door_status="closed"` - Contains 1 item, door closed

### Collection Process:
- `status="collect_request"` + `door_status="closed"` - Full, requesting collection
- `status="collect_request"` + `door_status="open"` - Full, door open for collection
- `status="available"` + `door_status="closed"` - Empty after collection

### Special States:
- `status="maintenance"` + `door_status="closed"` - Under maintenance
- `status="offline"` + `door_status="closed"` - System offline

## State Transitions (Simplified)

### Item Collection Flow:
1. `available/closed` → `full/closed` (item deposited)
2. `full/closed` → `collect_request/closed` (auto-request collection)
3. `collect_request/closed` → `collect_request/open` (door opens for collection)
4. `collect_request/open` → `available/closed` (item collected, door closes)
