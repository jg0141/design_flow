# Timing 기초 이론 — Verilog, RTL, Pipeline, Setup/Hold

Verilog → RTL → Pipeline → Clock/Data → Setup/Hold → Clock skew 순서로 정리한다.
설명은 특별히 언급하지 않는 한 같은 clock의 rising edge로 동작하는 D Flip-Flop(FF) 사이의 경로를 기준으로 한다. 수치 예제는 교육용이며 특정 프로젝트의 실제 library 값이 아니다.

## 1. What is Verilog?

Verilog는 hardware의 구조와 동작을 코드로 기술하는 HDL(Hardware Description Language)이다.
“hardware를 software로 바꾼다”보다는 “hardware를 언어로 표현한다”가 정확하다.

Verilog로 simulation을 수행하며, 합성 가능한 코드는 synthesis를 통해 cell과 연결 구조인 gate-level netlist로 변환한다.
처음 개발한 곳은 Gateway Design Automation이고 이후 Cadence가 인수했다. 따라서 “Cadence가 처음 제작했다”는 설명은 수정한다.

Verilog는 작성 언어이고 RTL은 설계를 표현하는 추상화 수준이다. Verilog로 RTL, gate-level 구조, testbench 등을 작성할 수 있으며 모든 Verilog 구문이 합성 가능한 것은 아니다.

## 2. What is RTL?

RTL(Register Transfer Level)은 register에 저장되는 상태, register 사이의 data 이동, 그 사이에서 수행되는 연산을 표현하는 설계 추상화 수준이다.

**Launch FF의 Q → Combinational logic 및 배선 → Capture FF의 D**

- Register: data/state를 저장한다.
- Combinational logic: 현재 input 값에 따라 연산 결과를 만든다.
- Clock: synchronous circuit에서 상태를 갱신할 기준 시점을 제공한다.

단순히 “저장 장치 사이의 data 이동”뿐 아니라 **이동하는 data에 어떤 연산을 수행하고 언제 저장하는지**까지 포함한다.

## 3. Why do we need RTL?

### RTL이 필요한 이유

수많은 transistor를 직접 기술하지 않고 register·연산·data 흐름으로 복잡한 기능을 설계하고 검증하기 위해 사용한다.
Synthesis를 통해 해당 기능을 library cell로 구현할 수 있다.

### Register를 사용하는 이유

상태를 저장하고, clock을 기준으로 data를 다음 단계에 전달하기 위해 사용한다.

Combinational logic은 input이 바뀌자마자 정답을 내놓지 않는다. Propagation delay가 존재하며, 경로별 delay 차이 때문에 계산 중 일시적인 glitch가 생길 수도 있다.
Register는 결과가 안정된 시점에 capture하고, 다음 상태 갱신까지 값을 보존하는 역할을 한다.

다음 설명은 구분해야 한다.

- Register가 없는 combinational circuit도 정상적인 회로다.
- “RTL을 사용하지 않으면 input 변화 때문에 MOSFET이 고장 난다”는 설명은 잘못됐다.
- Glitch나 timing violation이 곧 MOSFET의 물리적 고장을 의미하지 않는다.
- Timing 문제는 잘못된 값의 capture나 metastability 등으로 이어질 수 있다.
- RTL을 작성했다는 사실만으로 실제 회로의 timing이 만족되는 것은 아니다.
- Register를 추가했다고 비동기 input의 metastability 문제가 자동으로 해결되는 것도 아니다. Clock Domain Crossing(CDC)에 맞는 구조가 필요하다.

### Verilog의 4-state 값

| 값 | 의미 |
|---|---|
| 0 | Logic low |
| 1 | Logic high |
| X | Unknown |
| Z | High impedance |

X와 Z는 같은 의미가 아니다. 또한 실제 analog metastability와 simulation의 X를 동일한 것으로 보면 안 된다.

## 4. What is Pipeline?

Pipeline은 긴 처리를 여러 stage로 나누고, stage 사이에 register를 두어 **서로 다른 data를 동시에 처리하는 구조**다.
하나의 data가 모든 stage를 동시에 통과하는 것은 아니다.

3-stage pipeline의 예:

| 처리 구간 | Stage 1 | Stage 2 | Stage 3 |
|---|---|---|---|
| 첫 번째 cycle | A | — | — |
| 두 번째 cycle | B | A | — |
| 세 번째 cycle | C | B | A |
| 네 번째 cycle | D | C | B |

- **Latency**: data 하나가 들어와 결과가 나올 때까지 걸리는 시간.
- **Throughput**: 단위 시간당 처리하는 data 수.

각 stage가 매 cycle 새 data를 받을 수 있고 stall이 없다면, pipeline이 채워진 후에는 매 cycle 결과 하나를 얻을 수 있다.
Pipeline은 stage당 combinational logic을 줄여 clock period를 줄일 여지를 주지만 data 하나의 latency가 반드시 감소하는 것은 아니다.
추가 register에 따른 area, clock power, clock-to-Q 및 setup overhead도 고려한다.

## 5. How do registers work with clock and data?

```verilog
always @(posedge clk) begin
    q1 <= din;
    q2 <= q1;
end
```

각 rising edge에서:

1. q1은 해당 edge의 din 값을 capture한다.
2. q2는 해당 edge에서 갱신되기 전 q1 값을 capture한다.

같은 edge에서 din이 q1과 q2를 한 번에 통과하는 것이 아니다.
Nonblocking assignment(`<=`)는 이러한 register의 동시 상태 갱신을 표현한다.

실제 FF에서는 clock edge 이후 **clock-to-Q delay(tCQ)**가 지나야 Q가 갱신된다.
그 data가 combinational logic과 배선을 통과해 다음 FF의 D에 도착한다.

동일 clock·동일 edge의 일반적인 register-to-register 경로에서는 현재 edge에 launch된 data를 다음 edge에서 capture하도록 설계한다. 현재 edge에서는 이전 cycle에 전달된 값을 capture한다.

## 6. Data와 clock이 같은 시점에 변하면?

정확히는 **capture FF의 clock edge 주변에서 D가 변하면 저장 결과를 보장하기 어려워질 수 있다**는 뜻이다.

| 항목 | 의미 |
|---|---|
| Setup time | Capture edge 이전에 D가 안정되어 있어야 하는 시간 |
| Hold time | Capture edge 이후에도 D가 유지되어야 하는 시간 |
| Clock-to-Q delay | Clock edge 이후 Q가 유효한 값으로 바뀌는 데 걸리는 시간 |

Setup/Hold 요구를 위반하면 이전 값과 새 값 중 무엇을 capture할지 보장하기 어렵고 metastability가 발생할 가능성이 있다.
Violation이 발생할 때마다 반드시 metastability가 발생하는 것은 아니다.

### Library timing과 timing check의 차이

- **Library setup/hold time**: FF cell이 요구하는 timing 조건.
- **Setup/Hold check**: 실제 data arrival와 clock arrival가 해당 조건을 만족하는지 확인하는 분석.

Library timing은 cell 내부 구조와 Process/Voltage/Temperature(PVT), data/clock transition 등의 조건에 따라 달라진다.
위의 “edge 전/후” 설명은 기본 개념이며, 실제 library에는 내부 data/clock delay 관계에 따른 음수 setup 또는 hold 값도 있을 수 있으므로 report와 library 정의를 따른다.

일반적인 RTL simulation은 실제 cell·배선 delay나 analog metastability를 그대로 재현하지 않는다.
RTL simulation pass만으로 timing을 보장할 수 없으며, 구현된 netlist·library·SDC·배선 정보를 이용한 Static Timing Analysis(STA)가 필요하다.
Timing simulation도 보완적으로 사용할 수 있지만 analog metastability 자체를 정확히 재현하는 것은 아니다.

## 7. Clock latency와 Clock skew

| 항목 | 의미 |
|---|---|
| Clock latency | Clock source에서 FF clock pin까지 도착하는 데 걸리는 시간 |
| Clock skew | Launch FF와 Capture FF 사이의 clock 도착 시간 차이 |

두 FF에 clock이 똑같이 늦게 도착하는 경우와 capture 쪽 clock만 더 늦게 도착하는 경우는 다르다.

이 문서에서는 같은 nominal edge의 clock latency를 기준으로 다음과 같이 정의한다.

```text
tSkew = tCaptureClock − tLaunchClock
```

- Positive skew: capture clock이 launch clock보다 늦게 도착.
- Negative skew: capture clock이 launch clock보다 먼저 도착.

## 8. Setup/Hold 조건식

아래 식은 같은 clock, 같은 active edge, 기본 single-cycle 경로에서 uncertainty와 variation 등을 생략한 교육용 식이다.
tData에는 combinational cell delay와 data net delay를 포함한다.

### Setup: data가 너무 늦게 도착하지 않는가?

```text
tCQ,max + tData,max + tSetup ≤ Tclk + tSkew
Setup slack = Tclk + tSkew − tSetup − tCQ,max − tData,max
```

다음 capture edge의 setup 요구를 만족해야 한다.
이 단순 모델에서 positive skew는 setup에 유리하다.

### Hold: 새 data가 너무 빨리 도착하지 않는가?

```text
tCQ,min + tData,min ≥ tSkew + tHold
Hold slack = tCQ,min + tData,min − tSkew − tHold
```

현재 capture edge의 hold window 동안 기존 D 값이 유지돼야 한다.
이 단순 모델에서 positive skew는 hold에 불리하다.

### Hold violation 예제

| 항목 | 예제 값 |
|---|---:|
| tCQ,min | 30 ps |
| tData,min | 20 ps |
| tSkew | +60 ps |
| tHold | 10 ps |

Launch clock을 0 ps로 놓으면 새 data는 50 ps에 도착하지만, capture FF의 기존 data는 70 ps까지 유지돼야 한다.

```text
Hold slack = 30 + 20 − 60 − 10 = −20 ps
```

따라서 hold violation이다.

실제 STA에서는 early/late clock 및 data 조건, uncertainty, variation, 공통 clock 경로 pessimism 보정 등 해당 flow의 설정을 함께 반영한다.

## 9. Deep submicron과 Hold violation

“data 경로가 빨라지는데 clock skew는 남아서 hold가 어려워진다”는 직관은 도움이 된다.
다만 “data net delay skew가 계속 줄어든다”는 문장 대신 **“짧은 data 경로의 minimum delay가 작아질 수 있다”**로 표현한다.

> 공정 미세화로 짧은 data 경로의 minimum delay가 작아질 수 있는 반면, clock skew와 variation을 완전히 없앨 수는 없으므로 hold margin이 부족해질 수 있다. 다만 모든 data 경로의 delay가 미세화에 따라 일률적으로 감소하는 것은 아니며, 실제 library·배선·corner 조건으로 확인해야 한다.

배선 RC와 load 등의 영향도 있으므로 공정 미세화만으로 violation 발생 여부를 판단하지 않는다.
Setup/Hold 요구는 deep submicron 때문에 새로 생긴 것이 아니라 FF 자체에 원래 필요한 조건이다.

같은 clock·같은 edge의 기본 hold 식에는 clock period가 없으므로 **주파수를 낮추는 것만으로 일반적인 hold violation을 해결할 수 없다.**
Hold 개선에서는 data path의 minimum delay 증가나 불리한 skew 완화 등을 검토하며, 변경 후 setup도 다시 확인한다.

## 10. RTL 설계 원칙의 정확한 표현

| 기존 표현 | 수정한 표현 |
|---|---|
| 동일 clock source는 동시에 동작한다. | 같은 clock·같은 active edge를 사용하는 FF는 RTL에서 같은 논리적 시점에 상태를 갱신하는 것으로 모델링한다. 실제 회로에는 clock skew가 존재한다. |
| RTL은 반드시 한 cycle에 동작을 마무리해야 한다. | 기본 single-cycle path는 launch 이후 다음 capture edge의 setup 요구를 만족해야 한다. 전체 기능은 pipeline이나 multi-cycle 구조로 여러 cycle에 걸쳐 수행할 수 있다. |

같은 clock source라도 divider, phase shift, 반대 edge 등을 사용하면 capture 관계가 달라진다.
다른 clock domain 사이의 data 전달은 CDC 관점에서 별도 검토해야 한다.

Multi-cycle 연산을 설계했다는 사실과 SDC에 `set_multicycle_path`를 설정하는 것은 별개의 판단이다.
실제 enable/capture 동작이 여러 cycle을 허용하는지 확인해야 하며, timing violation을 감추기 위한 exception을 설정해서는 안 된다.
기능상 multicycle이 맞더라도 setup/hold edge 관계를 함께 검토한다.

## 11. Timing 설명의 핵심 연결

**RTL 기능 설계 → Synthesis로 cell 구현 → SDC로 동작 조건 지정 → STA로 Setup/Hold 확인**

- RTL: 어떤 상태와 연산이 필요한가?
- Library: 선택한 FF와 combinational cell의 실제 timing 특성은 무엇인가?
- SDC: clock과 interface, mode 및 timing 관계는 무엇인가?
- STA: 해당 조건에서 data가 필요한 시점에 도착하고 유지되는가?

Setup은 “이번에 보낸 data가 다음 capture에 늦지 않는가”, hold는 “새 data가 너무 빨리 도착해 현재 capture를 방해하지 않는가”를 확인한다.


## 12. Negative delay와 상대적인 시간

“RTL에서 minus delay가 존재한다”보다는 **STA report의 음수 값이 어떤 항목인지 먼저 구분한다**고 정리한다.

| 항목 | 음수의 의미 |
|---|---|
| 기준 에지에 대한 상대 시각 | 기준 에지보다 먼저 발생 |
| Clock skew | 이 문서의 정의에서는 Capture clock latency가 Launch clock latency보다 작음 |
| Setup/Hold slack | Timing requirement를 만족하지 못함 |
| Library Setup/Hold time | 셀 내부의 data와 clock 전달 관계에 따라 음수 constraint가 가능 |

Capture 기준 에지가 10 ns이고 data arrival가 8 ns이면 상대 시각은 8 − 10 = −2 ns이다. 기준보다 2 ns 먼저 도착했다는 뜻이며 실제 전파 시간이 음수라는 뜻은 아니다. 이 값 자체를 negative slack으로 해석해서도 안 된다.

“모든 EDA check tool은 endpoint로 결과를 분석한다”는 과도한 일반화다. **STA의 Setup/Hold 검사는 endpoint의 required time과 data arrival time을 비교하며, startpoint·data path·Launch/Capture clock path를 함께 고려한다.**

## 13. Timing Exception과 CDC

| 개념 | 정의 |
|---|---|
| Timing Exception | 기본 timing 분석 규칙을 특정 경로에 대해 변경하는 제약 |
| Multicycle Path | 실제 동작이 허용하는 여러 cycle의 Launch/Capture 관계를 지정하는 경로 |
| CDC (Clock Domain Crossing) | 서로 다른 clock domain 사이로 신호가 전달되는 것 |

같은 clock domain에도 multicycle path가 존재할 수 있다. CDC라고 반드시 multicycle을 적용하는 것은 아니다.

- Synchronous clocks: 주기·위상 관계를 정의하여 STA로 분석한다. 기능상 필요할 때 multicycle을 적용한다.
- Asynchronous clocks: synchronizer, handshake, asynchronous FIFO 등 전달 방식에 맞는 CDC 구조와 검증이 필요하다. Multicycle로 metastability를 해결할 수 없다.
- False path와 asynchronous clock group 등으로 일반적인 timing 분석을 제외하는 판단은 CDC 구조의 안전성 검증과 별개다.

RTL designer가 Clock enable이나 제어 로직을 이용해 특정 data를 여러 cycle 후에 capture하도록 설계할 수 있다. STA tool은 그 기능적 의도를 자동으로 모두 추론하지 못하므로 SDC로 실제 허용 관계를 전달한다.

PrimeTime은 제약에 따라 검사한다. Synthesis/P&R tool은 제약을 목표로 최적화한다. 불필요하게 엄격한 제약은 의도와 다른 violation을 만들거나, 불필요한 cell upsizing 및 buffer 삽입으로 area/power를 증가시킬 수 있다. 반대로 근거 없는 exception은 실제 오류를 가릴 수 있다.

## 14. Launch/Capture, Data delay, Clock delay

| 항목 | 의미 |
|---|---|
| Launch FF | CLKA의 active edge에서 data를 내보내는 FF |
| Capture FF | CLKB의 active edge에서 data를 저장하는 FF |
| Clock-to-Q delay | Launch FF의 clock edge 이후 Q가 바뀌는 데 걸리는 시간 |
| Data delay | 여기서는 Q에서 조합논리·배선을 거쳐 Capture D까지 전달되는 지연 |
| Clock delay | Clock이 각 FF의 clock pin까지 전달되는 지연 |

Data arrival에는 Launch edge time, Launch clock latency, clock-to-Q, data path delay가 반영된다. Setup은 capture 전에 data가 충분히 일찍 도착하는지, Hold는 capture 주변에서 기존 data가 충분히 유지되는지 검사한다.

Multicycle은 **비교하는 Launch/Capture 에지 관계**를 바꾼다. 실제 clock 파형, data delay, register 수, library Setup/Hold 값을 직접 변경하지 않는다.

## 15. set_multicycle_path 문법과 기본값

정확한 명령 이름은 `set_multicycle_path`이다. `set_multi_cycle`이 아니다.

```tcl
# 아래 핀 이름은 예시다. 실제 netlist 이름으로 바꿔야 한다.
set_multicycle_path 1 -setup -end \
    -from [get_pins U_LAUNCH/CK] -to [get_pins U_CAPTURE/D]

set_multicycle_path 0 -hold -start \
    -from [get_pins U_LAUNCH/CK] -to [get_pins U_CAPTURE/D]
```

| 옵션 | 의미 |
|---|---|
| -from / -to | 적용할 경로 선택 |
| -setup | Setup 검사 관계 지정 |
| -hold | Hold 검사 관계 조정 |
| -start | Launch clock 주기로 Launch 에지 이동 |
| -end | Capture clock 주기로 Capture 에지 이동 |

PrimeTime에서 Setup 기준 기본값은 -end, Hold 기준 기본값은 -start이다. 기본 Setup multiplier는 1, Hold multiplier는 0이다. 기본 동작을 얻기 위해 위 두 명령을 반드시 작성할 필요는 없지만 옵션을 명시하면 의도가 분명해진다. 다른 tool의 기본값은 해당 tool 문서를 확인한다.

**Hold 0은 library Hold time이 0이라는 뜻이 아니다.** Multicycle에 의한 Hold 에지 조정값이다. Setup 관계를 먼저 바꾸면 Hold 0 상태에서도 도출되는 Hold 관계가 달라질 수 있다.

## 16. 동일한 10 ns clock: Setup 2 / Hold 1

두 FF가 동일한 rising-edge clock으로 동작하고 실제 제어 로직이 2-cycle 전달을 허용한다고 가정한다. 수치는 강의 사진에서 판독한 값이 아닌 교육용 예제다.

기본 Setup 관계는 Launch 0 ns → Capture 10 ns이다. 다음 제약은 Capture 에지를 20 ns로 이동시킨다.

```tcl
set_multicycle_path 2 -setup -end \
    -from [get_cells U_A] -to [get_cells U_B]
```

Setup만 변경하면 그에 따라 Hold 관계도 바뀌어 한 cycle의 불필요한 minimum delay 요구가 생길 수 있다. 원래 Hold 관계를 유지하려는 경우 다음을 추가한다.

```tcl
set_multicycle_path 1 -hold -end \
    -from [get_cells U_A] -to [get_cells U_B]
```

| 적용 제약 | Setup 비교 에지 | Hold 비교 에지 |
|---|---|---|
| 기본값 | Launch 0 → Capture 10 ns | Launch 0 → Capture 0 ns |
| Setup 2 -end만 적용 | Launch 0 → Capture 20 ns | Launch 0 → Capture 10 ns |
| Hold 1 -end 추가 | Launch 0 → Capture 20 ns | Launch 0 → Capture 0 ns |

이 표는 에지 관계만 나타내며 library requirement, clock latency, uncertainty 등은 별도로 반영한다. 같은 주기에서는 Hold에 -start를 사용해도 동등한 간격을 만들 수 있지만, 이동하는 에지는 Launch 에지이므로 표의 절대 에지 시각과는 구분한다.

**Setup N / Hold N−1**은 Setup 변경에 따라 이동한 Hold 관계를 의도에 맞게 조정하는 흔한 조합이다. **Hold 1을 “한 cycle 동안 data를 유지하라”로 해석하면 안 된다.** 서로 다른 주기에서는 기준 옵션과 실제 edge 관계를 반드시 함께 확인한다.

## 17. 서로 다른 주기: -start / -end

| 검사 | -start: Launch 에지 | -end: Capture 에지 |
|---|---|---|
| Setup multiplier N | (N−1) × Launch period만큼 이전으로 | (N−1) × Capture period만큼 이후로 |
| Hold multiplier M | M × Launch period만큼 이후로 | M × Capture period만큼 이전으로 |

Setup 이동량은 기본 Setup 관계 기준이고, Hold 이동량은 Setup 설정으로 도출된 Hold 관계 기준이다.

CLKA가 5 ns, CLKB가 10 ns인 예제:

| 제약 | 기본 Setup 관계에서 변경되는 시간 |
|---|---|
| 2 -setup -start | Launch 에지를 5 ns 이전으로 이동 |
| 2 -setup -end | Capture 에지를 10 ns 이후로 이동 |

이는 추가 여유의 차이를 설명하는 예제다. 서로 다른 clock 사이의 최종 허용 시간을 multiplier × period만으로 단정하면 안 된다. 기본 edge 관계와 위상도 고려해야 한다.

빠른 clock의 cycle 단위로 표현하려는 경우:

| 전달 방향 | 빠른 clock 기준 |
|---|---|
| Fast → Slow | -start |
| Slow → Fast | -end |

**항상 빠른 clock을 기준으로 해야 한다는 규칙은 아니다.** 먼저 실제 RTL의 유효 Launch/Capture 에지를 정하고, 그 관계를 표현할 기준과 multiplier를 선택한다. Fast → Slow라도 매 fast edge에 새로운 data를 내보낸다면 단순히 주파수 비율만 보고 긴 data delay를 허용할 수 없다.

강의 사진에서는 CLKA/CLKB 파형과 Setup/Hold 옵션을 확인할 수 있으나 반사 때문에 정확한 주기·위상·일부 숫자는 확정하지 않는다.

## 18. PrimeTime에서 적용 후 확인

```tcl
# Setup 경로 확인
report_timing -from [get_cells U_A] -to [get_cells U_B] \
    -delay_type max -path_type full_clock_expanded

# Hold 경로 확인
report_timing -from [get_cells U_A] -to [get_cells U_B] \
    -delay_type min -path_type full_clock_expanded
```

1. 실제 RTL의 enable/capture 조건이 여러 cycle을 허용하는지 확인한다.
2. 실제 경로와 clock period·waveform·관계를 확인한다.
3. 해당 경로에만 exception을 지정한다. Clock 전체를 -from/-to로 선택하면 의도보다 넓게 적용될 수 있다.
4. Setup/Hold report에서 Launch/Capture edge time과 경로가 의도대로 선택됐는지 확인한다.
5. Data arrival time, data required time, slack을 함께 확인한다.

**Setup violation이 있다는 이유만으로 multicycle을 추가하지 않는다.** STA에 전달하는 것은 실제 설계가 허용하는 timing 관계다.

## 19. Synchronous/Asynchronous clock과 PLL

Synchronous는 두 clock의 상대적인 주기·위상 관계를 예측할 수 있는 경우다. Asynchronous는 유효한 에지 관계를 보장할 수 없는 경우다. PLL 개수나 source 이름만으로 판단하지 않는다.

| 명령 | 역할 |
|---|---|
| create_clock | 분석의 기준 clock 정의 |
| create_generated_clock | 기존 master clock과의 분주·배주·위상 이동 등 파생 관계 정의 |

PLL 출력도 generated clock으로 정의할 수 있다. Block-level 분석에서 PLL 출력을 분석 시작점으로 삼는다면 primary clock으로 모델링할 수도 있다. 이때 상위 clock과의 관계가 필요한 분석인지 검토한다. 두 clock에 각각 create_clock을 사용해도 자동으로 asynchronous가 되는 것은 아니다.

```tcl
# 교육용 예제. 시간 단위가 ns이고 실제 이름이 일치할 때의 형태.
create_clock -name CLK -period 10 [get_ports clk]
create_generated_clock -name CLK_DIV2 \
    -source [get_ports clk] -divide_by 2 [get_pins U_DIV/Q]
```

실제 SDC 반영 전 확인: PLL 입력/출력 위치, 배주·분주 비율, 출력 위상 관계, mode, master/generated clock 연결. 원래 메모의 “둘 다 create_clock & async”는 clock 구조가 없으므로 확정하지 않는다.

## 20. False path, Max/Min delay와 metastability

set_false_path와 set_max_delay는 같은 명령이 아니다.

| 명령 | 역할 |
|---|---|
| set_false_path | 선택한 경로의 해당 timing check를 제외 |
| set_max_delay | 최대 delay requirement 지정 |
| set_min_delay | 최소 delay requirement 지정 |

어느 명령도 metastability를 직접 보존하거나 제거하지 않는다. Synchronizer는 metastability가 후단으로 전달될 확률을 낮추기 위한 구조다. 일반적인 2-FF synchronizer에서 첫 번째 FF → 두 번째 FF는 수신 clock domain의 synchronous 경로이므로 정상 timing 분석을 유지한다.

두 FF 사이의 clock-to-Q 및 data delay가 작아지면 다음 FF가 sample하기 전 resolution time 확보에 유리하다. MTBF는 resolution time, clock/data 활동률, 셀 특성 등에 영향을 받는다. 단순 2-FF 구조는 임의의 multi-bit bus나 짧은 pulse 전달을 모두 보장하지 않는다.

Async 입력 → 첫 번째 FF의 예외와, 첫 번째 FF → 두 번째 FF의 timing requirement를 구분한다. Async CDC 경로에도 물리적 전달 시간 제한이 필요하면 max-delay 제약을 검토할 수 있다. 같은 경로에 넓은 false-path/async clock-group을 함께 적용하면 max-delay 분석이 가려질 수 있다. 실제 tool의 exception 우선순위를 확인한다.

-datapath_only 같은 옵션과 Hold 처리 방식은 tool·버전에 따라 다르므로 AMD 예제를 PrimeTime에 그대로 옮기지 않는다.

## 21. Clock skew, Data skew와 max/min delay

동일한 경로·동일 조건·동일 시간 단위에 set_max_delay 0과 set_min_delay 1을 적용하는 것은 일반적인 skew 최소화 방법이 아니다. 일반적인 같은 경로 delay 모델에서는 최대값 ≤ 0, 최소값 ≥ 1이라는 모순된 요구가 된다.

set_max_delay 0을 특수한 최적화 목표로 사용하는 script가 있을 수는 있지만 cell을 일렬로 배치하거나 skew를 최소화한다는 보장은 없다. set_min_delay는 너무 짧은 경로에 delay 추가를 요구할 수 있다.

| 목적 | 검토 대상 |
|---|---|
| Clock 도착 시각 차이 감소 | CTS의 skew 목표, clock routing, clock latency |
| 여러 data bit의 상대 도착 시간 차이 제한 | Tool이 지원하는 bus-skew/data-check 제약, 배선 |
| Synchronizer FF 사이의 data delay 감소 | 정상 timing 분석, 적절한 delay 목표, 배치·배선 및 synchronizer 속성 |

Bus skew는 여러 경로의 상대적인 도착 시간 차이다. 한 경로의 max/min delay와 동일한 개념이 아니다. Pre-CTS의 ideal clock만으로 post-CTS 실제 skew가 검증되지는 않는다.

실제 script에서 두 명령의 -from/-to/-through, 적용 mode, 시간 단위를 확인하기 전에는 해당 숫자를 적용하지 않는다.

## 22. NAND tree: Functional/Test mode 예외

“Test용 NAND tree이므로 당연히 false path”로 결론 내리지 않는다. Functional mode에서 활성화되지 않거나 기능적으로 유효하지 않은 경로라는 근거를 먼저 확인한다.

```tcl
# 예시: test_mode=0이 실제 functional mode인 경우에만 사용
set_case_analysis 0 [get_ports test_mode]

# 아래 hierarchy/pin 이름은 확인되지 않은 예시
set nand_pins [get_pins {I_PAD/*/*_NAND_*/PO}]
sizeof_collection $nand_pins
get_object_name $nand_pins

# 매칭된 핀과 해당 경로의 기능을 확인한 뒤에만 적용
# set_false_path -through $nand_pins
```

get_pins 결과가 비어 있거나 예상보다 넓은지 확인한다. -through는 해당 핀을 통과하는 경로에 영향을 주므로 필요하면 -from/-to도 지정한다. Case analysis로 비활성화된 경로에는 추가 exception이 불필요할 수 있다.

Functional mode에서 제외한 test 경로라도 실제 검사해야 하는 test-mode 요구가 있다면 별도 mode SDC에서 검증한다. 현재 NAND-tree report와 netlist가 없으므로 실제 false-path 대상은 확정하지 않는다.

## 23. Async reset: Recovery/Removal

정확한 용어는 Recovery와 Removal이다.

| 검사 | 의미 |
|---|---|
| Recovery | Reset 해제가 유효 clock edge보다 충분히 먼저 일어나는가 |
| Removal | Clock edge 이후 필요한 시간 동안 reset이 유지되는가 |

Async reset도 deassertion 시점에는 metastability와 FF 간 해제 불일치 문제가 생길 수 있다. 흔히 asynchronous assertion / synchronous deassertion 구조를 사용하며 domain별 reset 구조를 검토한다.

```tcl
# 아래의 포괄적인 예외는 구조 확인 없이 적용하지 않는다.
# set_false_path -from [get_ports rst]
```

확인할 내용:
- Reset 생성 위치와 각 수신 clock domain.
- Reset synchronizer 및 해제 방식.
- 외부 async 구간 중 예외가 필요한 범위.
- Synchronizer 이후 내부 reset 경로의 Recovery/Removal requirement.

“P&R 전에 Recovery/Removal violation이 안 나오게 한다”는 이유로 경로 전체를 자르지 않는다. 예외는 검증 방법과 회로 구조를 근거로 결정하며, 검사를 숨기는 것이 안전한 reset 동작을 보장하지 않는다.

## 24. Multicycle 에지 관계를 그려 보는 연습

실제 강의 사진의 주기·위상은 확정하지 않는다. 아래는 동일한 rising-edge 10 ns clock을 쓰고 실제 제어 로직이 2-cycle 전달을 허용하는 교육용 예제다.

| 설정 | Launch | Setup Capture | Hold Capture |
|---|---|---|---|
| 기본 | 0 ns | 10 ns | 0 ns |
| Setup 2 -end | 0 ns | 20 ns | 10 ns |
| Setup 2 -end + Hold 1 -end | 0 ns | 20 ns | 0 ns |

에지 사이에 data 경로를 연결해 보고, Capture FF가 10 ns의 중간 결과를 유효한 결과로 사용하지 않는 이유를 RTL enable/프로토콜로 설명한다. Hold 표는 에지 관계이며 library Hold time은 별도로 반영한다.

주기가 다르면:
1. 두 clock의 period와 waveform을 적는다.
2. 기본 Setup/Hold 에지 관계를 찾는다.
3. -start면 Launch, -end면 Capture clock 주기로 에지를 이동한다.
4. Setup과 Hold를 함께 계산한다.
5. PrimeTime report의 edge time과 비교한다.

배수나 주파수 비율만 보고 multicycle을 지정하지 않는다. 기본 예제의 Tcl 명령과 상세 설명은 16–18번 항목을 참고한다.

## 25. SDC update → pre-STA 작업 순서

1. Clock 구조: PLL 입력·출력·분주 위치, period/waveform, synchronous/asynchronous 관계 정리.
2. Mode 설정: functional/test 선택 신호와 set_case_analysis 검토.
3. Multicycle: 실제 enable 및 유효 Launch/Capture 에지 관계 확인.
4. CDC 제약: synchronizer/handshake/FIFO 구조와 예외 범위 검토.
5. Delay/skew: 어떤 경로를 어떤 단위·목적으로 제한하는지 확인.
6. NAND tree: mode와 실제 report를 근거로 필요한 예외만 적용.
7. Reset: 해제 방식과 Recovery/Removal 검증 범위 확인.
8. Pre-STA: clock 정의, missing constraint, unconstrained path, exception 적용 범위, Setup/Hold 및 Recovery/Removal 확인.

```tcl
# PrimeTime 기본 확인 예제
report_units
report_clock
check_timing
report_exceptions
report_timing -delay_type max -path_type full_clock_expanded
report_timing -delay_type min -path_type full_clock_expanded
```

기본 report_timing만으로 모든 Recovery/Removal check가 검증됐다고 결론 내리지 않는다. 해당 tool 버전의 check-type 보고 옵션과 분석 coverage를 함께 확인한다.

필요한 실제 input: 최신 SDC, PLL/clock 구조, max/min-delay 원문, NAND-tree timing report와 해당 netlist, reset 구조. 현재 추가한 것은 학습 및 검토 지침이며 실제 프로젝트 SDC 수정본이나 pre-STA 실행 결과가 아니다.

## 참고 자료

- [Cadence — Verilog HDL and Its Ancestors and Descendants](https://community.cadence.com/cadence_blogs_8/b/breakfast-bytes/posts/verilog-hdl-and-its-ancestors-and-descendants)
- [Synopsys — What is Register-Transfer-Level Design?](https://www.synopsys.com/glossary/what-is-register-transfer-level-design.html)
- [Intel — Metastability Analysis](https://www.intel.com/content/www/us/en/docs/programmable/683068/18-1/metastability-analysis.html)
- [Intel — Timing Analyzer Example: Clock Analysis Equations](https://www.intel.com/content/www/us/en/support/programmable/support-resources/design-examples/quartus/tq-clock.html)
- [Intel — Default Multicycle Analysis](https://www.intel.com/content/www/us/en/docs/programmable/683243/21-3/default-multicycle-analysis.html)

- [AMD UG903 — set_multicycle_path Syntax](https://docs.amd.com/r/2023.1-English/ug903-vivado-using-constraints/set_multicycle_path-Syntax)
- [AMD UG903 — Multicycle Paths](https://docs.amd.com/r/2025.1-English/ug903-vivado-using-constraints/Multicycle-Paths)
- [AMD UG903 — Fast-to-Slow Setup/Hold Example](https://docs.amd.com/r/2021.2-English/ug903-vivado-using-constraints/Example-Setup-3-start/Hold-2)

- [AMD — Synchronous Clocks](https://docs.amd.com/r/en-US/ug903-vivado-using-constraints/Synchronous-Clocks)
- [AMD — Constraining Asynchronous Signals](https://docs.amd.com/r/2021.2-English/ug903-vivado-using-constraints/Constraining-Asynchronous-Signals)
- [AMD — Clock Exceptions Precedence Over set_max_delay](https://docs.amd.com/r/en-US/2020.2-English/ug1387-acap-hardware-ip-platform-dev-methodology/Clock-Exceptions-Precedence-Over-set_max_delay)
- [Intel — Recovery and Removal Timing Violation Warnings](https://www.intel.com/content/www/us/en/docs/programmable/683241/25-1/recovery-and-removal-timing-violation.html)
