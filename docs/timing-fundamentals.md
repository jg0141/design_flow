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

## 참고 자료

- [Cadence — Verilog HDL and Its Ancestors and Descendants](https://community.cadence.com/cadence_blogs_8/b/breakfast-bytes/posts/verilog-hdl-and-its-ancestors-and-descendants)
- [Synopsys — What is Register-Transfer-Level Design?](https://www.synopsys.com/glossary/what-is-register-transfer-level-design.html)
- [Intel — Metastability Analysis](https://www.intel.com/content/www/us/en/docs/programmable/683068/18-1/metastability-analysis.html)
- [Intel — Timing Analyzer Example: Clock Analysis Equations](https://www.intel.com/content/www/us/en/support/programmable/support-resources/design-examples/quartus/tq-clock.html)
- [Intel — Default Multicycle Analysis](https://www.intel.com/content/www/us/en/docs/programmable/683243/21-3/default-multicycle-analysis.html)
