#pragma once

#include <Arduino.h>

// REVIEW EVERY VALUE BEFORE CONNECTING ACTUATOR POWER.
constexpr uint8_t PCA9685_ADDRESS = 0x40;
constexpr uint16_t PCA9685_FREQUENCY_HZ = 50;

// The PCA9685 is dedicated to servo channels 0..7.
constexpr uint16_t SERVO_MIN_TICKS[8] = {110, 110, 110, 110, 110, 110, 110, 110};
constexpr uint16_t SERVO_MAX_TICKS[8] = {510, 510, 510, 510, 510, 510, 510, 510};
constexpr uint8_t SERVO_SAFE_DEGREES[8] = {90, 80, 100, 90, 90, 90, 90, 90};

// STEP and DIR for X, Y, curtain. These use ordinary digital outputs so four
// PWM-capable pins remain available for the two DRV8871 drivers.
constexpr uint8_t STEPPER_STEP_PIN[3] = {2, 7, 11};
constexpr uint8_t STEPPER_DIR_PIN[3] = {4, 10, 12};

// Shared A4988 ENABLE connection for all three drivers. ENABLE is active-low:
// LOW energizes the drivers; HIGH disables their outputs.
constexpr uint8_t STEPPER_ENABLE_PIN = 13;

// Physical E-stop should also interrupt actuator power. Input is normally closed
// to ground; HIGH means open circuit / stop requested.
constexpr uint8_t ESTOP_PIN = 8;

// Bare DRV8871 two-input interface. Both pins for each motor receive PWM.
// Motor 0 (left): IN1=D3, IN2=D5. Motor 1 (right): IN1=D6, IN2=D9.
constexpr uint8_t DC_IN1_PIN[2] = {3, 6};
constexpr uint8_t DC_IN2_PIN[2] = {5, 9};

// Encoder A/B pins. These aliases must support interrupts on the selected core.
constexpr uint8_t ENCODER_A_PIN[2] = {A0, A2};
constexpr uint8_t ENCODER_B_PIN[2] = {A1, A3};

// SM16823E RGB front-light chain. D19 is also labeled A5/PC0 on UNO Q.
// Set STAGE_LIGHT_COUNT to 5 if the finished daisy chain contains five modules.
constexpr uint8_t STAGE_LIGHT_DATA_PIN = 19;
constexpr uint8_t STAGE_LIGHT_COUNT = 6;
// SM16823E gain range is 1..16. Start conservatively and raise only after
// checking the module current, cooling, and power-supply capacity.
constexpr uint8_t STAGE_LIGHT_CURRENT_GAIN = 4;

constexpr uint32_t COMMAND_WATCHDOG_MS = 2000;
constexpr int32_t DC_POSITION_TOLERANCE = 4;
constexpr int32_t DC_KP_NUMERATOR = 1;
constexpr int32_t DC_KP_DENOMINATOR = 4;
