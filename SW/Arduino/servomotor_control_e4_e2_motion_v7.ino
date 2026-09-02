#include <Servo.h>

/*
  Jerber folding-board controller e4/e2 motion V7

  Design rule:
    - e2 behavior is preserved as the baseline.
    - Startup still calls attachAndHomeAll(), so servo torque holds from boot.
    - 1..5, S, F, X, D, H and ? retain the e2 behavior.
    - Only G/g is added for the synchronized showcase sequence used by the display UI.

  Display UI compatibility:
    PROTO:JERBER_E4_E2_MOTION_V7
    G -> synchronized one-shot sequence -> DONE

  V7 motion baseline:
    - Servo start/operate angles are copied exactly from servomotor_control_e2.ino.
    - Manual plate commands 1..5 preserve the original e2 toggle behavior.
    - Servos attach and hold torque from boot, as in e2 (D releases torque).
    - Manual operate hold: 1000 ms.
    - Manual return hold: 1000 ms.
    - Manual return profile: 2 deg / 10 ms.
    - The synchronized G scenario/order and stage waits are preserved.
*/

const int SERVO_COUNT = 8;
const int PLATE_COUNT = 5;

const int servoPins[SERVO_COUNT] = {
  2, 3, 4, 5, 6, 7, 8, 9
};

Servo servos[SERVO_COUNT];

// Unique build identity. The UI checks this as well as PROTO so an older V6/V7
// binary can no longer be mistaken for the sketch you just uploaded.
const char BUILD_ID[] = "JERBER_E4_E2_MOTION_V7_B1_20260817";

// Exact plate-5 targets copied from the user-supplied servomotor_control_e2.ino.
const int E2_P5_PIN8_START = 158;
const int E2_P5_PIN8_OPERATE = 98;
const int E2_P5_PIN9_START = 14;
const int E2_P5_PIN9_OPERATE = 74;

/*
  배열 순서:
  인덱스    0  1  2  3  4  5  6  7
  핀 번호   2  3  4  5  6  7  8  9
*/

int startAngles[SERVO_COUNT] = {
  160, 20, 24, 156, 160, 154, E2_P5_PIN8_START, E2_P5_PIN9_START
};

int operateAngles[SERVO_COUNT] = {
  60, 120, 120, 60, 25, 25, E2_P5_PIN8_OPERATE, E2_P5_PIN9_OPERATE
};

// 현재 각 서보에 마지막으로 명령한 각도
int currentAngles[SERVO_COUNT];

/*
  플레이트와 서보 인덱스 연결

  1번 플레이트: 핀 4, 5 → 서보 인덱스 2, 3
  2번 플레이트: 핀 2, 3 → 서보 인덱스 0, 1
  3번 플레이트: 핀 6    → 서보 인덱스 4
  4번 플레이트: 핀 7    → 서보 인덱스 5
  5번 플레이트: 핀 8, 9 → 서보 인덱스 6, 7

  두 번째 값이 -1이면 단일 서보 플레이트
*/
const int plateServoA[PLATE_COUNT] = {
  2, 0, 4, 5, 6
};

const int plateServoB[PLATE_COUNT] = {
  3, 1, -1, -1, 7
};

// false: 초기 위치, true: 동작 위치
bool plateOperated[PLATE_COUNT] = {
  false, false, false, false, false
};

// 동작 위치에 도착한 후 대기
const unsigned long OPERATE_WAIT_MS = 1000;

// 천천히 복귀한 후 대기
const unsigned long RETURN_WAIT_MS = 1000;

// 다음 플레이트 동작 전 대기
const unsigned long NEXT_WAIT_MS = 500;

// detach 후 다시 연결했을 때 초기 위치 복귀 대기
const unsigned long REATTACH_WAIT_MS = 2000;

/*
  복귀 속도 설정

  2도 이동하고 10ms 대기:
  약 200도/초의 명령 속도

  더 느리게:
  RETURN_STEP_DEGREES = 1
  또는
  RETURN_STEP_DELAY_MS = 20

  더 빠르게:
  RETURN_STEP_DEGREES = 3
*/
const int RETURN_STEP_DEGREES = 2;
const unsigned long RETURN_STEP_DELAY_MS = 10;

// ------------------------------------------------------------
// e4 addition: synchronized G scenario only
// ------------------------------------------------------------
// First 1+2 full-rise hold requested by the user.
const unsigned long SYNC_INITIAL_WAIT_MS = 1000;
// Interlock between plates 1+2 and plate 3/4 motion.
const unsigned long SYNC_INTERLOCK_WAIT_MS = 500;
// Existing showcase settle waits after an auxiliary plate reaches its target.
const unsigned long SYNC_STAGE_WAIT_MS = 650;
const unsigned long SYNC_FINAL_WAIT_MS = 900;

// Smooth multi-plate interpolation used only by G.
const int SYNC_STEP_DEGREES = 2;
const unsigned long SYNC_STEP_DELAY_MS = 10;

enum ControllerState {
  STOPPED_HOLD,
  STARTING_REPEAT,
  RUNNING_REPEAT,
  STARTING_ONE_SHOT,
  RUNNING_ONE_SHOT,
  // e4 addition: G has its own state so F/S keep the original e2 flow.
  STARTING_SYNC_G,
  RUNNING_SYNC_G,
  MANUAL_MOVING,
  DETACHED
};

ControllerState controllerState = STOPPED_HOLD;
unsigned long startingSince = 0;

// Explicit prototypes (Arduino IDE would auto-generate these; keeping them here
// also makes static C++ syntax checking straightforward).
void handleSerialCommands();
void togglePlate(int plateIndex);
void commandPlateOperate(int plateIndex);
bool slowReturnPlate(int plateIndex, ControllerState requiredState);
bool movePlateCycle(int plateIndex, ControllerState requiredState);
void startSequence();
void startOneShotFold();
void startSynchronizedG();
void stopAndHold();
void homeAndHold();
void stopAndDetach();
void attachAndHomeAll();
void resetPlateStates();
bool anyPlateOperated();
void printStatus();
bool waitWhileState(unsigned long waitTime, ControllerState requiredState);
int syncRatioAngle(int servoIndex, float ratio);
void syncSetPlateTarget(int targets[SERVO_COUNT], int plateIndex, float ratio);
bool syncMoveToTargets(const int targets[SERVO_COUNT], ControllerState requiredState);
bool syncMoveRatios(float p1, float p2, float p3, float p4, float p5, ControllerState requiredState);
bool runSynchronizedGSequence(ControllerState requiredState);

void setup() {
  Serial.begin(9600);

  attachAndHomeAll();
  delay(2000);

  Serial.println(F(""));
  Serial.println(F("================================"));
  Serial.println(F("Jerber e4/e2 motion V7 controller ready."));
  Serial.println(F("================================"));
  Serial.println(F("1: Plate 1 toggle - pins 4, 5"));
  Serial.println(F("2: Plate 2 toggle - pins 2, 3"));
  Serial.println(F("3: Plate 3 toggle - pin 6"));
  Serial.println(F("4: Plate 4 toggle - pin 7"));
  Serial.println(F("5: Plate 5 toggle - pins 8, 9"));
  Serial.println(F(""));
  Serial.println(F("S: start repeating automatic sequence"));
  Serial.println(F("F: run one folding sequence, then send DONE"));
  Serial.println(F("G: run synchronized display-UI sequence, then send DONE"));
  Serial.println(F("X: stop and return home"));
  Serial.println(F("D: stop and detach"));
  Serial.println(F("H: return home and hold"));
  Serial.println(F("?: status"));
  Serial.println(F("================================"));
  Serial.println(F("PROTO:JERBER_E4_E2_MOTION_V7"));
  Serial.print(F("BUILD:"));
  Serial.println(BUILD_ID);
  Serial.println(F("E2_P5:PIN8=158->98 PIN9=14->74"));
  Serial.println(F("READY"));
}

void loop() {
  handleSerialCommands();

  // e4 addition: G uses its own one-shot state machine.
  // Existing e2 S/F flow below remains unchanged.
  if (controllerState == STARTING_SYNC_G) {
    if (millis() - startingSince >= REATTACH_WAIT_MS) {
      controllerState = RUNNING_SYNC_G;
      Serial.println(F("FOLDING"));
      Serial.println(F("[G] START synchronized one-shot sequence."));
    }
    delay(5);
    return;
  }

  if (controllerState == RUNNING_SYNC_G) {
    if (!runSynchronizedGSequence(RUNNING_SYNC_G)) {
      return;
    }

    if (controllerState == RUNNING_SYNC_G) {
      controllerState = STOPPED_HOLD;
      resetPlateStates();
      Serial.println(F("[G] DONE synchronized one-shot sequence."));
      Serial.println(F("DONE"));
    }
    return;
  }

  // Detached/manual states may require a home pass before a requested mode starts.
  if (controllerState == STARTING_REPEAT || controllerState == STARTING_ONE_SHOT) {
    if (millis() - startingSince >= REATTACH_WAIT_MS) {
      if (controllerState == STARTING_ONE_SHOT) {
        controllerState = RUNNING_ONE_SHOT;
        Serial.println(F("FOLDING"));
        Serial.println(F("[FOLD] START one-shot sequence."));
      } else {
        controllerState = RUNNING_REPEAT;
        Serial.println(F("[START] Repeating automatic sequence started."));
      }
    }
    delay(5);
    return;
  }

  if (controllerState != RUNNING_REPEAT && controllerState != RUNNING_ONE_SHOT) {
    delay(5);
    return;
  }

  ControllerState requiredState = controllerState;
  for (int plateIndex = 0; plateIndex < PLATE_COUNT; plateIndex++) {
    if (!movePlateCycle(plateIndex, requiredState)) {
      return;
    }
  }

  if (requiredState == RUNNING_ONE_SHOT && controllerState == RUNNING_ONE_SHOT) {
    controllerState = STOPPED_HOLD;
    Serial.println(F("[FOLD] DONE one-shot sequence."));
    Serial.println(F("DONE"));
    return;
  }

  if (controllerState == RUNNING_REPEAT) {
    Serial.println(F("[AUTO] All plate operations complete."));
    waitWhileState(3000, RUNNING_REPEAT);
  }
}

void handleSerialCommands() {
  while (Serial.available() > 0) {
    char command = Serial.read();

    // 엔터, 줄바꿈, 공백 무시
    if (
      command == '\r' ||
      command == '\n' ||
      command == ' '
    ) {
      continue;
    }

    switch (command) {
      case '1':
        togglePlate(0);
        break;

      case '2':
        togglePlate(1);
        break;

      case '3':
        togglePlate(2);
        break;

      case '4':
        togglePlate(3);
        break;

      case '5':
        togglePlate(4);
        break;

      case 'S':
      case 's':
        startSequence();
        break;

      case 'F':
      case 'f':
        startOneShotFold();
        break;

      case 'G':
      case 'g':
        startSynchronizedG();
        break;

      case 'X':
      case 'x':
        stopAndHold();
        break;

      case 'D':
      case 'd':
        stopAndDetach();
        break;

      case 'H':
      case 'h':
        homeAndHold();
        break;

      case '?':
        printStatus();
        break;

      default:
        Serial.print(F("[ERROR] Unknown command: "));
        Serial.println(command);
        break;
    }
  }
}

/*
  숫자 1~5 수동 토글

  초기 위치 상태:
  startAngles → operateAngles

  동작 위치 상태:
  operateAngles → startAngles
  복귀할 때는 천천히 이동
*/
void togglePlate(int plateIndex) {
  if (plateIndex < 0 || plateIndex >= PLATE_COUNT) {
    return;
  }

  if (controllerState == RUNNING_REPEAT || controllerState == RUNNING_ONE_SHOT ||
      controllerState == RUNNING_SYNC_G) {
    Serial.println(
      F("[INFO] Stop automatic sequence before manual control.")
    );
    return;
  }

  if (controllerState == STARTING_REPEAT || controllerState == STARTING_ONE_SHOT ||
      controllerState == STARTING_SYNC_G) {
    Serial.println(
      F("[INFO] Servos are currently returning home.")
    );
    return;
  }

  if (controllerState == MANUAL_MOVING) {
    Serial.println(
      F("[INFO] Another plate is currently moving.")
    );
    return;
  }

  // D 명령으로 detach된 경우 다시 attach하고 초기 위치로 복귀
  if (controllerState == DETACHED) {
    controllerState = MANUAL_MOVING;

    attachAndHomeAll();

    Serial.println(F("[MANUAL] Servos attached."));
    Serial.println(F("[MANUAL] Returning home first."));

    if (!waitWhileState(REATTACH_WAIT_MS, MANUAL_MOVING)) {
      return;
    }
  } else {
    controllerState = MANUAL_MOVING;
  }

  Serial.print(F("[PLATE "));
  Serial.print(plateIndex + 1);
  Serial.print(F("] "));

  // 초기 위치라면 동작 위치로 이동
  if (!plateOperated[plateIndex]) {
    Serial.println(F("Moving to operate position."));

    commandPlateOperate(plateIndex);

    if (!waitWhileState(OPERATE_WAIT_MS, MANUAL_MOVING)) {
      return;
    }

    plateOperated[plateIndex] = true;

    Serial.print(F("[PLATE "));
    Serial.print(plateIndex + 1);
    Serial.println(F("] Operated position reached."));
  }

  // 동작 위치라면 초기 위치로 천천히 복귀
  else {
    Serial.println(F("Returning home slowly."));

    if (!slowReturnPlate(plateIndex, MANUAL_MOVING)) {
      return;
    }

    plateOperated[plateIndex] = false;

    if (!waitWhileState(RETURN_WAIT_MS, MANUAL_MOVING)) {
      return;
    }

    Serial.print(F("[PLATE "));
    Serial.print(plateIndex + 1);
    Serial.println(F("] Home position reached."));
  }

  if (controllerState == MANUAL_MOVING) {
    controllerState = STOPPED_HOLD;
  }
}

/*
  해당 플레이트를 동작 각도로 즉시 명령
*/
void commandPlateOperate(int plateIndex) {
  int servoA = plateServoA[plateIndex];
  int servoB = plateServoB[plateIndex];

  // Keep the e2 write() path exactly. For plate 5 we additionally guard the
  // constants so a later array edit cannot silently change pins 8/9.
  if (plateIndex == 4) {
    servos[6].write(E2_P5_PIN8_OPERATE);   // e2: pin 8 -> 98 deg
    currentAngles[6] = E2_P5_PIN8_OPERATE;
    servos[7].write(E2_P5_PIN9_OPERATE);   // e2: pin 9 -> 74 deg
    currentAngles[7] = E2_P5_PIN9_OPERATE;

    Serial.print(F("[P5-E2] BUILD="));
    Serial.print(BUILD_ID);
    Serial.print(F(" PIN8_TARGET="));
    Serial.print(E2_P5_PIN8_OPERATE);
    Serial.print(F(" PIN8_READ="));
    Serial.print(servos[6].read());
    Serial.print(F(" PIN8_US="));
    Serial.print(servos[6].readMicroseconds());
    Serial.print(F(" PIN9_TARGET="));
    Serial.print(E2_P5_PIN9_OPERATE);
    Serial.print(F(" PIN9_READ="));
    Serial.print(servos[7].read());
    Serial.print(F(" PIN9_US="));
    Serial.println(servos[7].readMicroseconds());
    return;
  }

  servos[servoA].write(operateAngles[servoA]);
  currentAngles[servoA] = operateAngles[servoA];

  if (servoB >= 0) {
    servos[servoB].write(operateAngles[servoB]);
    currentAngles[servoB] = operateAngles[servoB];
  }
}

/*
  플레이트를 초기 위치로 천천히 복귀

  한 쌍의 서보모터는 같은 시간 동안 움직이도록
  진행 비율을 계산하여 동시에 복귀시킨다.
*/
bool slowReturnPlate(
  int plateIndex,
  ControllerState requiredState
) {
  int servoA = plateServoA[plateIndex];
  int servoB = plateServoB[plateIndex];

  int fromA = currentAngles[servoA];
  int toA = startAngles[servoA];
  int deltaA = toA - fromA;

  int fromB = 0;
  int toB = 0;
  int deltaB = 0;

  if (servoB >= 0) {
    fromB = currentAngles[servoB];
    toB = startAngles[servoB];
    deltaB = toB - fromB;
  }

  int maxDistance = abs(deltaA);

  if (servoB >= 0) {
    maxDistance = max(maxDistance, abs(deltaB));
  }

  if (maxDistance == 0) {
    return true;
  }

  int totalSteps =
    (maxDistance + RETURN_STEP_DEGREES - 1) /
    RETURN_STEP_DEGREES;

  for (int step = 1; step <= totalSteps; step++) {
    int nextAngleA =
      fromA + ((long)deltaA * step) / totalSteps;

    servos[servoA].write(nextAngleA);
    currentAngles[servoA] = nextAngleA;

    if (servoB >= 0) {
      int nextAngleB =
        fromB + ((long)deltaB * step) / totalSteps;

      servos[servoB].write(nextAngleB);
      currentAngles[servoB] = nextAngleB;
    }

    if (
      !waitWhileState(
        RETURN_STEP_DELAY_MS,
        requiredState
      )
    ) {
      return false;
    }
  }

  // 계산 오차 방지를 위해 마지막에 정확한 초기 각도 명령
  servos[servoA].write(toA);
  currentAngles[servoA] = toA;

  if (servoB >= 0) {
    servos[servoB].write(toB);
    currentAngles[servoB] = toB;
  }

  return true;
}

/*
  S 명령 자동 시퀀스에서 사용

  동작 위치까지 빠르게 이동한 후
  초기 위치로 천천히 복귀
*/
bool movePlateCycle(int plateIndex, ControllerState requiredState) {
  if (controllerState != requiredState) {
    return false;
  }

  Serial.print(F("[AUTO] Plate "));
  Serial.print(plateIndex + 1);
  Serial.println(F(" operating."));

  commandPlateOperate(plateIndex);

  if (!waitWhileState(OPERATE_WAIT_MS, requiredState)) {
    return false;
  }

  plateOperated[plateIndex] = true;

  Serial.print(F("[AUTO] Plate "));
  Serial.print(plateIndex + 1);
  Serial.println(F(" returning slowly."));

  if (!slowReturnPlate(plateIndex, requiredState)) {
    return false;
  }

  plateOperated[plateIndex] = false;

  if (!waitWhileState(RETURN_WAIT_MS, requiredState)) {
    return false;
  }

  return waitWhileState(NEXT_WAIT_MS, requiredState);
}

void startSequence() {
  if (controllerState == RUNNING_REPEAT) {
    Serial.println(F("[INFO] Repeating automatic sequence is already running."));
    return;
  }
  if (controllerState == RUNNING_ONE_SHOT) {
    Serial.println(F("[INFO] One-shot fold is running. Use X/D/H to interrupt."));
    return;
  }
  if (controllerState == RUNNING_SYNC_G || controllerState == STARTING_SYNC_G) {
    Serial.println(F("[INFO] Synchronized G sequence is running. Use X/D/H to interrupt."));
    return;
  }
  if (controllerState == STARTING_REPEAT || controllerState == STARTING_ONE_SHOT) {
    Serial.println(F("[INFO] Servos are returning home."));
    return;
  }
  if (controllerState == MANUAL_MOVING) {
    Serial.println(F("[INFO] A plate is currently moving."));
    return;
  }

  if (controllerState == DETACHED || anyPlateOperated()) {
    attachAndHomeAll();
    controllerState = STARTING_REPEAT;
    startingSince = millis();
    Serial.println(F("[STARTING] Returning all plates home for repeating mode."));
    return;
  }

  controllerState = RUNNING_REPEAT;
  Serial.println(F("[START] Repeating automatic sequence started."));
}

void startOneShotFold() {
  if (controllerState == RUNNING_SYNC_G || controllerState == STARTING_SYNC_G) {
    Serial.println(F("[INFO] Synchronized G sequence is running. Use X/D/H to interrupt."));
    return;
  }
  if (controllerState == RUNNING_ONE_SHOT || controllerState == STARTING_ONE_SHOT) {
    Serial.println(F("[INFO] One-shot fold is already running."));
    return;
  }
  if (controllerState == RUNNING_REPEAT || controllerState == STARTING_REPEAT) {
    Serial.println(F("[INFO] Stop repeating mode with X before one-shot F."));
    return;
  }
  if (controllerState == MANUAL_MOVING) {
    Serial.println(F("[INFO] A plate is currently moving."));
    return;
  }

  if (controllerState == DETACHED || anyPlateOperated()) {
    attachAndHomeAll();
    controllerState = STARTING_ONE_SHOT;
    startingSince = millis();
    Serial.println(F("[FOLD] Returning all plates home before one-shot sequence."));
    return;
  }

  controllerState = RUNNING_ONE_SHOT;
  Serial.println(F("FOLDING"));
  Serial.println(F("[FOLD] START one-shot sequence."));
}


// ------------------------------------------------------------
// e4 addition: synchronized G scenario
// ------------------------------------------------------------
int syncRatioAngle(int servoIndex, float ratio) {
  ratio = constrain(ratio, 0.0f, 1.0f);
  return (int)round(
    startAngles[servoIndex] +
    (operateAngles[servoIndex] - startAngles[servoIndex]) * ratio
  );
}

void syncSetPlateTarget(
  int targets[SERVO_COUNT],
  int plateIndex,
  float ratio
) {
  int servoA = plateServoA[plateIndex];
  int servoB = plateServoB[plateIndex];

  targets[servoA] = syncRatioAngle(servoA, ratio);
  if (servoB >= 0) {
    targets[servoB] = syncRatioAngle(servoB, ratio);
  }
}

bool syncMoveToTargets(
  const int targets[SERVO_COUNT],
  ControllerState requiredState
) {
  int from[SERVO_COUNT];
  int maxDistance = 0;

  for (int i = 0; i < SERVO_COUNT; i++) {
    from[i] = currentAngles[i];
    maxDistance = max(maxDistance, abs(targets[i] - from[i]));
  }

  if (maxDistance == 0) {
    return true;
  }

  int totalSteps =
    (maxDistance + SYNC_STEP_DEGREES - 1) /
    SYNC_STEP_DEGREES;

  for (int step = 1; step <= totalSteps; step++) {
    for (int i = 0; i < SERVO_COUNT; i++) {
      int nextAngle =
        from[i] +
        ((long)(targets[i] - from[i]) * step) /
        totalSteps;

      servos[i].write(nextAngle);
      currentAngles[i] = nextAngle;
    }

    if (!waitWhileState(SYNC_STEP_DELAY_MS, requiredState)) {
      return false;
    }
  }

  for (int i = 0; i < SERVO_COUNT; i++) {
    servos[i].write(targets[i]);
    currentAngles[i] = targets[i];
  }

  return true;
}

bool syncMoveRatios(
  float p1,
  float p2,
  float p3,
  float p4,
  float p5,
  ControllerState requiredState
) {
  float ratios[PLATE_COUNT] = {p1, p2, p3, p4, p5};
  int targets[SERVO_COUNT];

  for (int i = 0; i < SERVO_COUNT; i++) {
    targets[i] = currentAngles[i];
  }

  for (int plate = 0; plate < PLATE_COUNT; plate++) {
    syncSetPlateTarget(targets, plate, ratios[plate]);
  }

  return syncMoveToTargets(targets, requiredState);
}

bool runSynchronizedGSequence(ControllerState requiredState) {
  // 1) Plates 1+2 rise fully, then hold for 1.0 s.
  Serial.println(F("[SYNC_G] STAGE 1/7 P12_FULL · plates 1+2 -> 100%"));
  if (!syncMoveRatios(1.0, 1.0, 0.0, 0.0, 0.0, requiredState)) return false;
  if (!waitWhileState(SYNC_INITIAL_WAIT_MS, requiredState)) return false;

  // 2) Plates 1+2 descend to 50%; 0.5 s later plate 3 rises.
  Serial.println(F("[SYNC_G] STAGE 2A/7 P12_HALF_WAIT_P3 · plates 1+2 -> 50%"));
  if (!syncMoveRatios(0.5, 0.5, 0.0, 0.0, 0.0, requiredState)) return false;
  if (!waitWhileState(SYNC_INTERLOCK_WAIT_MS, requiredState)) return false;
  Serial.println(F("[SYNC_G] STAGE 2B/7 P3_UP_AFTER_DELAY · plate 3 -> 100%"));
  if (!syncMoveRatios(0.5, 0.5, 1.0, 0.0, 0.0, requiredState)) return false;
  if (!waitWhileState(SYNC_STAGE_WAIT_MS, requiredState)) return false;

  // 3) Plate 3 returns; 0.5 s later plates 1+2 rise fully.
  Serial.println(F("[SYNC_G] STAGE 3A/7 P3_DOWN_WAIT_P12 · plate 3 -> HOME"));
  if (!syncMoveRatios(0.5, 0.5, 0.0, 0.0, 0.0, requiredState)) return false;
  if (!waitWhileState(SYNC_INTERLOCK_WAIT_MS, requiredState)) return false;
  Serial.println(F("[SYNC_G] STAGE 3B/7 P12_FULL_AFTER_P3 · plates 1+2 -> 100%"));
  if (!syncMoveRatios(1.0, 1.0, 0.0, 0.0, 0.0, requiredState)) return false;
  if (!waitWhileState(SYNC_STAGE_WAIT_MS, requiredState)) return false;

  // 4) Plates 1+2 descend to 50%; 0.5 s later plate 4 rises.
  Serial.println(F("[SYNC_G] STAGE 4A/7 P12_HALF_WAIT_P4 · plates 1+2 -> 50%"));
  if (!syncMoveRatios(0.5, 0.5, 0.0, 0.0, 0.0, requiredState)) return false;
  if (!waitWhileState(SYNC_INTERLOCK_WAIT_MS, requiredState)) return false;
  Serial.println(F("[SYNC_G] STAGE 4B/7 P4_UP_AFTER_DELAY · plate 4 -> 100%"));
  if (!syncMoveRatios(0.5, 0.5, 0.0, 1.0, 0.0, requiredState)) return false;
  if (!waitWhileState(SYNC_STAGE_WAIT_MS, requiredState)) return false;

  // 5) Plate 4 returns; 0.5 s later plates 1+2 rise fully.
  Serial.println(F("[SYNC_G] STAGE 5A/7 P4_DOWN_WAIT_P12 · plate 4 -> HOME"));
  if (!syncMoveRatios(0.5, 0.5, 0.0, 0.0, 0.0, requiredState)) return false;
  if (!waitWhileState(SYNC_INTERLOCK_WAIT_MS, requiredState)) return false;
  Serial.println(F("[SYNC_G] STAGE 5B/7 P12_FULL_AFTER_P4 · plates 1+2 -> 100%"));
  if (!syncMoveRatios(1.0, 1.0, 0.0, 0.0, 0.0, requiredState)) return false;
  if (!waitWhileState(SYNC_STAGE_WAIT_MS, requiredState)) return false;

  // 6) Hold plates 1+2 up while plate 5 rises.
  Serial.println(F("[SYNC_G] STAGE 6/7 P5_UP_WITH_P12 · plates 1+2 hold + plate 5 -> 100%"));
  if (!syncMoveRatios(1.0, 1.0, 0.0, 0.0, 1.0, requiredState)) return false;
  if (!waitWhileState(SYNC_STAGE_WAIT_MS, requiredState)) return false;

  // 7) Plates 1+2+5 return together.
  Serial.println(F("[SYNC_G] STAGE 7/7 ALL_HOME · all plates -> HOME"));
  if (!syncMoveRatios(0.0, 0.0, 0.0, 0.0, 0.0, requiredState)) return false;
  resetPlateStates();
  return waitWhileState(SYNC_FINAL_WAIT_MS, requiredState);
}

void startSynchronizedG() {
  if (controllerState == RUNNING_SYNC_G || controllerState == STARTING_SYNC_G) {
    Serial.println(F("[INFO] Synchronized G sequence is already running."));
    return;
  }

  if (controllerState == RUNNING_REPEAT || controllerState == STARTING_REPEAT) {
    Serial.println(F("[INFO] Stop repeating S mode with X before G."));
    return;
  }

  if (controllerState == RUNNING_ONE_SHOT || controllerState == STARTING_ONE_SHOT) {
    Serial.println(F("[INFO] One-shot F is running. Use X/D/H to interrupt."));
    return;
  }

  if (controllerState == MANUAL_MOVING) {
    Serial.println(F("[INFO] A plate is currently moving."));
    return;
  }

  // Match e2 start semantics: if detached or a manual plate is left operated,
  // attach/home first and wait the original REATTACH_WAIT_MS.
  if (controllerState == DETACHED || anyPlateOperated()) {
    attachAndHomeAll();
    controllerState = STARTING_SYNC_G;
    startingSince = millis();
    Serial.println(F("[G] Returning all plates home before synchronized sequence."));
    return;
  }

  controllerState = RUNNING_SYNC_G;
  Serial.println(F("FOLDING"));
  Serial.println(F("[G] START synchronized one-shot sequence."));
}

void stopAndHold() {
  controllerState = STOPPED_HOLD;

  /*
    X는 긴급 정지 성격이 있으므로
    모든 서보를 즉시 초기 위치로 명령한다.
  */
  attachAndHomeAll();

  Serial.println(F("[STOP] Sequence stopped."));
  Serial.println(F("[STOP] All plates returned home."));
  Serial.println(F("[STOP] Servo torque is holding."));
}

void homeAndHold() {
  controllerState = STOPPED_HOLD;

  attachAndHomeAll();

  Serial.println(F("[HOME] All plates returned home."));
  Serial.println(F("[HOME] Servo torque is holding."));
}

void stopAndDetach() {
  controllerState = DETACHED;

  for (int i = 0; i < SERVO_COUNT; i++) {
    if (servos[i].attached()) {
      servos[i].detach();
    }
  }

  Serial.println(F("[DETACH] Controller stopped."));
  Serial.println(F("[DETACH] Servo torque released."));
}

void attachAndHomeAll() {
  for (int i = 0; i < SERVO_COUNT; i++) {
    if (!servos[i].attached()) {
      servos[i].attach(servoPins[i]);
    }

    servos[i].write(startAngles[i]);
    currentAngles[i] = startAngles[i];
  }

  resetPlateStates();
}

void resetPlateStates() {
  for (int i = 0; i < PLATE_COUNT; i++) {
    plateOperated[i] = false;
  }
}

bool anyPlateOperated() {
  for (int i = 0; i < PLATE_COUNT; i++) {
    if (plateOperated[i]) {
      return true;
    }
  }

  return false;
}

void printStatus() {
  Serial.print(F("[STATUS] Controller: "));

  switch (controllerState) {
    case STOPPED_HOLD:
      Serial.println(F("STOPPED_HOLD"));
      break;
    case STARTING_REPEAT:
      Serial.println(F("STARTING_REPEAT"));
      break;
    case RUNNING_REPEAT:
      Serial.println(F("RUNNING_REPEAT"));
      break;
    case STARTING_ONE_SHOT:
      Serial.println(F("STARTING_ONE_SHOT"));
      break;
    case RUNNING_ONE_SHOT:
      Serial.println(F("RUNNING_ONE_SHOT"));
      break;
    case STARTING_SYNC_G:
      Serial.println(F("STARTING_SYNC_G"));
      break;
    case RUNNING_SYNC_G:
      Serial.println(F("RUNNING_SYNC_G"));
      break;
    case MANUAL_MOVING:
      Serial.println(F("MANUAL_MOVING"));
      break;
    case DETACHED:
      Serial.println(F("DETACHED"));
      break;
  }

  for (int i = 0; i < PLATE_COUNT; i++) {
    Serial.print(F("[STATUS] Plate "));
    Serial.print(i + 1);
    Serial.print(F(": "));
    if (plateOperated[i]) {
      Serial.println(F("OPERATED"));
    } else {
      Serial.println(F("HOME"));
    }
  }
}

/*
  기다리는 동안에도 약 5ms 간격으로
  X, D, H 등의 정지 명령을 확인한다.
*/
bool waitWhileState(
  unsigned long waitTime,
  ControllerState requiredState
) {
  unsigned long startedAt = millis();

  while (millis() - startedAt < waitTime) {
    handleSerialCommands();

    if (controllerState != requiredState) {
      return false;
    }

    delay(5);
  }

  return true;
}