#pragma once

#include "box_network_client.h"
#include "config.h"

class SmartBoxStateMachine {
 public:
  explicit SmartBoxStateMachine(BoxNetworkClient &networkClient);

  void begin();
  void update();

 private:
  BoxNetworkClient &network_;
  unsigned long lastDoorAlertMs_ = 0;
  unsigned long lastSnapshotMs_ = 0;
  bool doorWasOpen_ = false;
};
