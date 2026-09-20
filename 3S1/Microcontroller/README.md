# 01076050 — Microcontroller Application And Development; 01076051 — Microcontroller Project

**Archive:** `3S1/Microcontroller`

[All courses](../../COURSE_MAP.md) · [Semester overview](../README.md) · [Academic portfolio](https://tart-ratha-portfolio.ratha-tart.chatgpt.site/academic.html)

## What is here

STM32 lab source includes initialization, GPIO, interrupt handlers, startup code, and hardware abstraction layer configuration.

## Build progress

Component work that preceded the assembled vehicle: the steel chassis, a stepper motor driven from the board with joystick input, the hub-motor wheels, and a driver board with soldered power devices.

![Chassis frame, stepper motor and joystick wiring, hub motor wheels, and a soldered driver board](../../assets/microcontroller-build.jpg)

## Result

The finished vehicle, built on a corrugated-panel body over the hub-motor drive wheels from the progress photos above. Control hardware is mounted on the upper deck, with an intake funnel at the front.

![Completed vehicle on the laboratory floor, showing the hub-motor drive wheels, panelled body, intake funnel, and deck-mounted controls](../../assets/microcontroller-vehicle-final.jpg)

Looking down on the deck, the control layout is visible end to end:

![Top-down view of the control deck showing the ultrasonic sensor, battery, joystick, emergency stop, switchgear, and breadboard wiring](../../assets/microcontroller-vehicle-layout.jpg)

| Component | Role |
|---|---|
| Hub-motor wheels | Direct drive, one per side, carried over from the progress build |
| Ultrasonic sensor on a card mount | Forward range sensing |
| Arcade joystick | Manual directional input |
| Red mushroom button | Emergency stop |
| Panel switch and contactor block | Main power switching |
| Rotary potentiometer | Analogue set-point input |
| Lithium battery pack | Onboard power |
| Breadboard and loom | Signal routing between the board, sensor, and drivers |
| Intake funnel | Front-mounted collection mouth |

These photographs record the delivered hardware; the control firmware is the STM32 source in [`Lab`](Lab/).

## Skills demonstrated

**Embedded C** · **STM32** · **HAL** · **GPIO** · **Interrupt handling**

Keywords describe the preserved work, not sole authorship of team exercises or mastery of every technology.

## Start here

Read each Lab/Core/Src/main.c with its matching headers. Hardware and toolchain configuration are required.

## Browse

- [Lab](Lab/)

## Course context

Shared material for these courses; individual files are not allocated to separate course codes.

This is an academic archive, not one installable application. Check each exercise’s dependencies and hardware requirements.
