#pragma once

// Arduino-ESP32 3.x ships a core "Network" library that defines networking
// event types consumed by <WiFi.h>.  Older revisions of this project shipped a
// sketch-local Network.h which shadowed the core header on case-insensitive
// filesystems and triggered the compiler errors reported by users.  Keep this
// shim so that any stale include still forwards to the core definitions while
// exposing the updated Smart Box networking helpers.

#include <Network.h>
#include "box_network.h"

using LookupResult = BoxLookupResult;
using SmartBoxNetworkClient = BoxNetworkClient;

