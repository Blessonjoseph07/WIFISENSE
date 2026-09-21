# Device-Free Human Activity Recognition and Fall Detection Using Wi-Fi Channel State Information (CSI): A Survey and System Architecture

**Blesson Joseph**  
*Department of Computer Applications, Amal Jyothi College of Engineering (Autonomous), Kanjirappally, Kerala, India*  
*Under the Guidance of: Assoc. Prof. Binumon Joseph*  
*Academic Project: Master of Computer Applications (MCA) — Phase 1 Review Paper*  
*Date: September 21, 2026 (Scrum Review 3)*

---

### Abstract
Indoor human activity recognition (HAR) and emergency fall detection are critical components of assisted living and healthcare automation. Traditional approaches relying on optical video surveillance raise severe privacy dilemmas, especially in personal spaces such as bedrooms and bathrooms, while wearable sensor systems suffer from low adherence, battery constraints, and user discomfort. Recently, radio frequency (RF) sensing using commercial off-the-shelf (COTS) Wi-Fi Channel State Information (CSI) has emerged as an unobtrusive, device-free, and privacy-preserving paradigm. 

This paper provides a comprehensive survey of Wi-Fi CSI-based human sensing, detailing physical layer RF propagation characteristics, subcarrier phase/amplitude dynamics, signal de-noising pipelines, and machine learning classification algorithms. Furthermore, this paper presents the architectural mapping of these theoretical principles into the **Wi-Fi Sense Focus** production system—a dual-context platform combining real-time OFDM subcarrier feature processing, non-blocking alert dispatch, multi-tenant role-based access control (RBAC), and subscription-gated family portals.

**Keywords**: *Channel State Information (CSI), Orthogonal Frequency Division Multiplexing (OFDM), Device-Free Sensing, Fall Detection, Privacy-Preserving Healthcare, Wi-Fi Sensing, Smart Elder Care.*

---

## 1. Introduction

As global demographics shift towards an aging population, unassisted living facilities face unprecedented challenges in resident safety. According to the World Health Organization (WHO), falls represent the second leading cause of unintentional injury deaths worldwide, with individuals over 65 suffering the highest incidence of fatal falls. Timely intervention following a fall significantly reduces morbidity and mortality (the "long-lie" effect).

Existing sensing paradigms exhibit critical structural limitations:
1. **Vision-Based Systems**: Optical RGB and infrared cameras achieve high spatial fidelity but severely compromise fundamental privacy rights. Residents vehemently reject camera installation in private spaces (restrooms, bedrooms), exactly where over 70% of non-witnessed falls occur.
2. **Wearable Sensors**: Inertial Measurement Units (IMUs), accelerometers, and smart pendants require active user compliance, routine charging, and correct bodily positioning. Residents suffering from mild cognitive impairment or Alzheimer's disease routinely forget or refuse to wear such devices.
3. **Ambient Floor Sensors**: Pressure mats and acoustic sensors suffer from high false positive rates (e.g., dropping objects or pet motion) and prohibitively high installation and maintenance costs.

Wi-Fi sensing resolves this trilemma by repurposing ubiquitous Wi-Fi RF signals already propagating through physical spaces. Human physical movement modulates the multi-path reflections of electromagnetic waves, inducing measurable perturbations in the physical layer (PHY) Channel State Information (CSI) across distinct subcarrier frequencies.

---

## 2. Theoretical Foundations: RSSI vs. CSI

### 2.1 Limitations of Received Signal Strength Indicator (RSSI)
Early RF sensing attempts utilized Received Signal Strength Indicator (RSSI) values reported by the MAC layer. However, RSSI has proved inadequate for fine-grained activity recognition:
- **Coarse Granularity**: RSSI represents a single scalar value per packet, averaging the total power across the entire channel spectrum.
- **Multipath Vulnerability**: In indoor multipath environments, reflections from walls, furniture, and dynamic objects superimpose destructively or constructively, causing extreme fluctuations (Rayleigh fading) that obscure subtle human motion.
- **Temporal Instability**: Ambient temperature shifts and hardware gain control changes trigger RSSI drift independent of human movement.

### 2.2 Fine-Grained Channel State Information (CSI)
Modern Wi-Fi standards (IEEE 802.11n/ac/ax) utilize **Orthogonal Frequency Division Multiplexing (OFDM)**, dividing the operational channel bandwidth (e.g., 20 MHz or 40 MHz) into dozens of orthogonal subcarriers (e.g., 56 subcarriers for 20 MHz HT channels).

Mathematically, the relationship between transmitted signal $X(f, t)$ and received signal $Y(f, t)$ in the frequency domain is represented as:
$$Y(f, t) = H(f, t) \cdot X(f, t) + N(f, t)$$
where $H(f, t)$ denotes the **Channel Frequency Response (CFR)** or Channel State Information (CSI) matrix, and $N(f, t)$ represents additive white Gaussian noise (AWGN).

The channel response for subcarrier $k$ is represented as a complex number:
$$H_k = |H_k| \cdot e^{j \angle H_k}$$
where $|H_k|$ captures the **subcarrier amplitude**, and $\angle H_k$ captures the **subcarrier phase**.

Because different subcarriers operate on slightly different frequencies, their multipath fading profiles vary independently (frequency diversity). Consequently, human movement across the Fresnel zone between transmitter (TX) and receiver (RX) introduces characteristic phase shifts and amplitude attenuations across the subcarrier spectrum, creating a distinctive RF "signature" for specific postures and events.

---

## 3. Comparative Modality Analysis

| Characteristic | Optical Cameras | Wearable IMU Devices | Radar / mmWave | Wi-Fi CSI Sensing |
| :--- | :---: | :---: | :---: | :---: |
| **Privacy Preservation** | Very Low (Severe breach) | High | High | **Very High (No visual capture)** |
| **User Compliance Required** | None | High (Must wear & charge) | None | **None (Zero device on body)** |
| **Blind Spots / Occlusion** | High (Line-of-sight required) | None | Moderate | **Low (Traverses non-metal walls)** |
| **Low-Light / Night Function** | Poor (Requires IR illumination)| Excellent | Excellent | **Excellent (Unaffected by darkness)** |
| **Hardware / Infrastructure Cost** | High | Moderate per user | High | **Low (COTS Wi-Fi / ESP32 nodes)** |
| **Ambient Non-Intrusiveness** | Low | Low | Moderate | **Maximum** |

---

## 4. CSI Processing & Classification Pipeline

The standard processing pipeline implemented in modern CSI sensing architectures consists of four sequential stages:

```
[Raw 802.11 CSI Packets]
          │
          ▼
┌───────────────────────────────┐
│ 1. Phase Sanitization &       │  --> Linear regression detrending
│    CFO / SFO Cancellation     │
└──────────────┬────────────────┘
          ▼
┌───────────────────────────────┐
│ 2. Signal Denoising &         │  --> Butterworth bandpass (0.3 - 20 Hz)
│    Filtering                  │  --> Hampel identifier for outliers
└──────────────┬────────────────┘
          ▼
┌───────────────────────────────┐
│ 3. Feature Extraction         │  --> Doppler Frequency Shift (DFS)
│    & Statistical Profiling    │  --> Normalized Subcarrier Variance
└──────────────┬────────────────┘
          ▼
┌───────────────────────────────┐
│ 4. Activity Classification &  │  --> State Machine / Classifier
│    Fall Detection Engine      │  --> Immediate Async Escalation
└───────────────────────────────┘
```

### 4.1 Phase Sanitization
Raw CSI phase data extracted from commercial chips (such as the Intel 5300, Atheros AR9300, or Espressif ESP32-S3) is contaminated by hardware timing offsets, including **Carrier Frequency Offset (CFO)** and **Sampling Frequency Offset (SFO)**. These offsets manifest as time-varying linear phase slopes across subcarrier indices.
Linear regression is applied to eliminate the slope and initial offset:
$$\tilde{\angle H}_k = \angle H_k - a \cdot k - b$$
yielding sanitized phase information that reflects genuine spatial propagation delay rather than hardware clock jitter.

### 4.2 Signal Filtering
Human body movements predominantly generate low-frequency Doppler shifts between 0.3 Hz and 20 Hz. High-frequency ambient thermal noise is removed using a Butterworth low-pass filter, while transient transmission errors are removed using a sliding-window Hampel filter.

### 4.3 Feature Representation
Key extracted features include:
- **Normalized Subcarrier Variance**: Quantifies energy distribution shifts across frequency bins.
- **Correlation Coefficient Matrix**: Measures inter-subcarrier cross-correlation, which spikes during coherent body movement.
- **Doppler Frequency Shift (DFS)**: Computed via Short-Time Fourier Transform (STFT) or Discrete Wavelet Transform (DWT), characterizing the velocity profile of the moving reflector.

### 4.4 Fall Detection Dynamics
A human fall exhibits a distinct kinematic profile compared to routine activities (e.g., sitting or walking):
1. **Descent Phase**: Rapid velocity acceleration lasting 0.4–0.8 seconds, causing a steep spike in high-frequency Doppler components across all subcarriers simultaneously.
2. **Impact Phase**: Sharp, high-amplitude energy transient.
3. **Stillness Phase**: Immediate drop in subcarrier variance to near-baseline noise floor, indicative of an incapacitated subject lying motionless on the floor.

---

## 5. Architectural Mapping in Wi-Fi Sense Focus

The **Wi-Fi Sense Focus** project translates these survey principles into a production-grade software platform:

1. **Hardware-Agnostic Ingestion**: The backend exposes an asynchronous REST and WebSocket gateway (`POST /sensing/events` and `/ws/stream`) capable of ingesting 56-element subcarrier vectors with RSSI and sequence validation from distributed ESP32 sensing nodes.
2. **Deterministic Dual-Domain State Engine**:
   - In **CARE** mode, detected events feed into a 4-state alert lifecycle machine (`new` → `acknowledged` → `responding` → `resolved`).
   - In **SPACE** mode, subcarrier variance translates into room occupancy counts, presence heatmaps, and energy mitigation actions (HVAC/lighting).
3. **Non-Blocking Safety Protocol**: Fall detection events spawn detached background tasks for notification delivery, preventing database lockups or HTTP timeout in safety-critical events.
4. **Multi-Tenant Scoping & Privacy Enforcement**: Even within an elder care facility, fine-grained `SharingPolicy` controls ensure family members access only telemetry explicitly authorized by administrators, preserving resident dignity while delivering emergency reassurance.

---

## 6. Conclusion & Future Research Directions

Wi-Fi Channel State Information provides a transformative bridge between continuous healthcare monitoring and individual privacy preservation. By decoupling activity recognition from optical sensors and physical wearables, CSI sensing enables non-intrusive safety nets for vulnerable populations. 

Ongoing development in Wi-Fi Sense Focus will incorporate:
- Adaptive room baseline RF calibration to mitigate static multipath variations caused by furniture rearrangement.
- Multi-person separation algorithms utilizing independent component analysis (ICA) to monitor multiple residents in shared rooms.
- Edge-based neural inference directly on dual-core ESP32-S3 nodes to minimize network transmission latency.

---

## References

1. **Wang, Y., Wu, K., & Ni, L. M.** (2017). "WiFall: Device-free fall detection by wireless networks." *IEEE Transactions on Mobile Computing*, 16(2), 581-594.
2. **Halperin, D., Hu, W., Sheth, A., & Wetherall, D.** (2011). "Tool release: Gathering 802.11n traces with channel state information." *ACM SIGCOMM Computer Communication Review*, 41(1), 53-53.
3. **Wu, C., Yang, Z., Zhou, Z., Liu, X., Liu, Y., & Cao, J.** (2015). "Non-invasive detection of moving and stationary human with WiFi." *IEEE Journal on Selected Areas in Communications*, 33(11), 2329-2342.
4. **Hernandez, S. M., & Bulut, E.** (2020). "WiSentry: Privacy-preserving IoT-enabled human sensing using Wi-Fi channel state information." *IEEE Internet of Things Journal*, 7(12), 11466-11478.
5. **Zhang, J., Wei, B., Hu, W., & Kanhere, S. S.** (2019). "WiFi-based indoor activity recognition: A survey." *IEEE Communications Surveys & Tutorials*, 22(1), 516-545.
6. **Blesson, J., & Joseph, B.** (2026). "Wi-Fi Sense: Architectural Design and Verification for Dual-Context CSI Facility Intelligence." *Amal Jyothi College of Engineering Technical Report Series*.
