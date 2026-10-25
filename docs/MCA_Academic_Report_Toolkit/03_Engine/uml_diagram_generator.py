"""
High-Resolution UML 2.5 Diagram Generator for Wi-Fi Sense MCA Project Report
Renders all 9 standardized UML diagrams in publication-quality Black & White / Monochrome (300 DPI),
strictly following autonomous college format and academic print specifications.
Accurately reflects the Wi-Fi Sense CSI Sensing, Fall Detection, Multi-Tenant Architecture and Cloud Ingestion Pipeline.
"""

import os
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch, Ellipse, Polygon
import matplotlib.lines as lines

TOOLKIT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUTPUT_DIR = os.path.join(TOOLKIT_DIR, "01_Inputs", "diagrams")
os.makedirs(OUTPUT_DIR, exist_ok=True)

def set_diagram_output_dir(path):
    global OUTPUT_DIR
    OUTPUT_DIR = os.path.abspath(path)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

# ----------------------------------------------------------------------
# Common Drawing Utilities (Academic Black & White / Monochrome)
# ----------------------------------------------------------------------
def init_canvas(title, width=14, height=10):
    fig, ax = plt.subplots(figsize=(width, height), dpi=300)
    ax.set_xlim(0, 1000)
    ax.set_ylim(0, 750)
    ax.axis("off")
    # Background
    bg = patches.Rectangle((0, 0), 1000, 750, fc="#FFFFFF", ec="none")
    ax.add_patch(bg)
    # Header Title
    ax.text(500, 730, title, ha="center", va="center", fontsize=14, fontweight="bold", color="#000000", fontfamily="serif")
    return fig, ax

def draw_actor(ax, x, y, name, color="#000000"):
    """Draws a standard UML stick-figure actor in crisp monochrome."""
    head = patches.Circle((x, y + 25), 8, fc="#FFFFFF", ec=color, lw=1.8, zorder=5)
    ax.add_patch(head)
    ax.plot([x, x], [y + 17, y - 5], color=color, lw=1.8, zorder=5)
    ax.plot([x - 14, x + 14], [y + 9, y + 9], color=color, lw=1.8, zorder=5)
    ax.plot([x, x - 12], [y - 5, y - 24], color=color, lw=1.8, zorder=5)
    ax.plot([x, x + 12], [y - 5, y - 24], color=color, lw=1.8, zorder=5)
    ax.text(x, y - 36, name, ha="center", va="top", fontsize=8.5, fontweight="bold", color=color, fontfamily="serif", wrap=True)

def draw_use_case(ax, x, y, w, h, text, fc="#FFFFFF", ec="#000000"):
    """Draws a standard UML use case ellipse in monochrome."""
    ellipse = Ellipse((x, y), w, h, fc=fc, ec=ec, lw=1.4, zorder=4)
    ax.add_patch(ellipse)
    ax.text(x, y, text, ha="center", va="center", fontsize=8, color="#000000", fontfamily="serif", zorder=5, multialignment="center")

def draw_box(ax, x, y, w, h, title="", subtitle="", fc="#FFFFFF", ec="#000000", lw=1.4, rx=4):
    """Draws a rounded rectangular box in monochrome."""
    box = FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad=0,rounding_size={rx}", fc=fc, ec=ec, lw=lw, zorder=3)
    ax.add_patch(box)
    if title and subtitle:
        ax.text(x + w / 2, y + h * 0.65, title, ha="center", va="center", fontsize=8.5, fontweight="bold", color="#000000", fontfamily="serif", zorder=4)
        ax.text(x + w / 2, y + h * 0.32, subtitle, ha="center", va="center", fontsize=7.5, color="#333333", fontfamily="serif", zorder=4, multialignment="center")
    elif title:
        ax.text(x + w / 2, y + h / 2, title, ha="center", va="center", fontsize=8.5, fontweight="bold", color="#000000", fontfamily="serif", zorder=4, multialignment="center")

def draw_arrow(ax, x1, y1, x2, y2, label="", color="#000000", style="->", ls="-", lw=1.2, label_offset=(0, 0)):
    """Draws a directional connection or message arrow in monochrome."""
    ax.annotate(
        "",
        xy=(x2, y2),
        xytext=(x1, y1),
        arrowprops=dict(arrowstyle=style, color=color, linestyle=ls, lw=lw, shrinkA=3, shrinkB=3),
        zorder=6
    )
    if label:
        mid_x = (x1 + x2) / 2 + label_offset[0]
        mid_y = (y1 + y2) / 2 + label_offset[1]
        ax.text(mid_x, mid_y, label, ha="center", va="center", fontsize=7.5, color="#000000", fontfamily="serif",
                bbox=dict(boxstyle="square,pad=0.15", fc="#FFFFFF", ec="none", alpha=0.9), zorder=7)

def save_fig(fig, filename):
    filepath = os.path.join(OUTPUT_DIR, filename)
    fig.savefig(filepath, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"--> Saved monochrome diagram: {filepath} ({os.path.getsize(filepath):,} bytes)")

# ----------------------------------------------------------------------
# 4.2.1 USE CASE DIAGRAM (Monochrome)
# ----------------------------------------------------------------------
def generate_diagram_01_use_case():
    """Generates Figure 4.1: Use Case Diagram for Wi-Fi Sense Ecosystem."""
    fig, ax = init_canvas("Figure 4.1: Use Case Diagram for Wi-Fi Sense Ecosystem")
    
    # Boundary Box
    boundary = FancyBboxPatch((150, 40), 700, 660, boxstyle="round,pad=0,rounding_size=10", fc="#FAFAFA", ec="#000000", lw=1.8, zorder=1)
    ax.add_patch(boundary)
    ax.text(170, 680, "Wi-Fi Sense: Sensing and Intelligence Platform — System Boundary", fontsize=10, fontweight="bold", color="#000000", fontfamily="serif")
    
    # Actors
    draw_actor(ax, 70, 520, "Caregiver /\nNurse", color="#000000")
    draw_actor(ax, 70, 240, "Family Member /\nDoctor", color="#000000")
    draw_actor(ax, 925, 520, "Facility Manager /\nSystem Admin", color="#000000")
    draw_actor(ax, 925, 240, "ESP32 IoT Node\n(Transmitter/Receiver)", color="#000000")
    
    # Use Cases - Left Column (Clinical & Family)
    uc_left = [
        (280, 630, 210, 34, "Authenticate (Multi-Role JWT)"),
        (280, 565, 210, 34, "Monitor Real-Time Occupancy"),
        (280, 500, 210, 34, "Receive Fall Detection Siren"),
        (280, 435, 210, 34, "Acknowledge / Resolve Alert"),
        (280, 370, 210, 34, "View Resident Activity Timeline"),
        (280, 305, 210, 34, "Inspect Vital Signs Telemetry"),
        (280, 240, 210, 34, "Request Data Sharing Access"),
        (280, 175, 210, 34, "View Historical Health Trends"),
    ]
    for x, y, w, h, text in uc_left:
        draw_use_case(ax, x, y, w, h, text)
        
    # Use Cases - Right Column (Admin & Hardware)
    uc_right = [
        (720, 630, 210, 34, "Manage Organizations & Buildings"),
        (720, 565, 210, 34, "Configure Floor Plans & Rooms"),
        (720, 500, 210, 34, "Provision & Calibrate ESP32 Nodes"),
        (720, 435, 210, 34, "Inspect Fault Tracer Diagnostics"),
        (720, 370, 210, 34, "Stream Raw CSI Byte Packets"),
        (720, 305, 210, 34, "Execute Baseline Calibration"),
        (720, 240, 210, 34, "Classify Human Activity (HAR)"),
        (720, 175, 210, 34, "Audit Security & Access Logs"),
    ]
    for x, y, w, h, text in uc_right:
        draw_use_case(ax, x, y, w, h, text)
        
    # Core Shared Use Case
    draw_use_case(ax, 500, 400, 170, 38, "Live CSI Waveform\n& Waterfall Display")

    # Connect Caregiver (70, 520) to uc_left[:5]
    for _, y, _, _, _ in uc_left[:5]:
        ax.plot([70, 175], [520, y], color="#000000", lw=1.1, zorder=3)
    ax.plot([70, 415], [520, 400], color="#000000", lw=1.1, zorder=3)

    # Connect Family/Doctor (70, 240) to uc_left[4:]
    for _, y, _, _, _ in uc_left[4:]:
        ax.plot([70, 175], [240, y], color="#000000", lw=1.1, zorder=3)

    # Connect Admin (925, 520) to uc_right[:5] + uc_right[7:]
    for _, y, _, _, _ in uc_right[:4]:
        ax.plot([925, 825], [520, y], color="#000000", lw=1.1, zorder=3)
    ax.plot([925, 825], [520, uc_right[7][1]], color="#000000", lw=1.1, zorder=3)
    ax.plot([925, 585], [520, 400], color="#000000", lw=1.1, zorder=3)

    # Connect ESP32 Hardware (925, 240) to uc_right[4:7]
    for _, y, _, _, _ in uc_right[4:7]:
        ax.plot([925, 825], [240, y], color="#000000", lw=1.1, zorder=3)

    # Relationships
    draw_arrow(ax, 280, 483, 280, 452, "<<include>>", style="->", ls="--", label_offset=(-34, 0))
    draw_arrow(ax, 720, 483, 720, 452, "<<extend>>", style="->", ls="--", label_offset=(34, 0))
    draw_arrow(ax, 720, 353, 720, 322, "<<include>>", style="->", ls="--", label_offset=(34, 0))

    save_fig(fig, "uml_01_use_case.png")

# ----------------------------------------------------------------------
# 4.2.2 SEQUENCE DIAGRAM (Monochrome)
# ----------------------------------------------------------------------
def generate_diagram_02_sequence():
    """Generates Figure 4.2: Sequence Diagram for Real-Time CSI Sensing & Fall Detection."""
    fig, ax = init_canvas("Figure 4.2: Sequence Diagram for CSI Packet Ingestion, Inference, and Fall Alert Dispatch", width=15, height=10.5)
    
    lifelines = [
        (70, ":ESP32Node\n(CSI Receiver)"),
        (200, ":SerialBridge\n(PySerial Gateway)"),
        (340, ":FastAPIServer\n(/sensing/ingest)"),
        (490, ":SignalProcessor\n(Hampel & PCA)"),
        (640, ":InferenceEngine\n(Activity Classifier)"),
        (780, ":SupabasePostgres\n(Relational DB)"),
        (920, ":CaregiverUI\n(React Live Monitor)"),
    ]
    
    for x, label in lifelines:
        draw_box(ax, x - 55, 665, 110, 38, label, fc="#FFFFFF", ec="#000000", lw=1.4, rx=3)
        ax.plot([x, x], [665, 55], color="#555555", lw=1.2, ls="--", zorder=2)
        draw_box(ax, x - 45, 30, 90, 24, "", fc="#FFFFFF", ec="#000000", lw=1, rx=2)
        ax.text(x, 42, label.split("\n")[0], ha="center", va="center", fontsize=6.5, color="#000000", fontweight="bold", fontfamily="serif")

    def draw_act(x, y_top, y_bot):
        rect = patches.Rectangle((x - 6, y_bot), 12, y_top - y_bot, fc="#FFFFFF", ec="#000000", lw=1.2, zorder=4)
        ax.add_patch(rect)

    draw_act(70, 645, 590)
    draw_act(200, 635, 560)
    draw_act(340, 620, 110)
    draw_act(490, 595, 510)
    draw_act(640, 530, 440)
    draw_act(780, 460, 360)
    draw_act(920, 390, 100)

    messages = [
        (70, 200, 635, "1: captureRawCSI(subcarriers=64, rssi=-42dBm)", True),
        (200, 340, 615, "2: POST /sensing/ingest (token, csi_matrix)", True),
        (340, 490, 590, "3: sanitizeAndFilter(phase_diff, amplitude)", True),
        (490, 340, 560, "4: returnSanitizedMatrix(variance, snr)", False),
        (340, 640, 535, "5: predictActivity(sliding_window=50)", True),
        (640, 640, 500, "6: detectSuddenVarianceDrop() -> Fall_Candidate", True, 25),
        (640, 340, 470, "7: returnActivity(Fall_Detected, conf=0.96)", False),
        (340, 780, 445, "8: INSERT INTO alerts (room_id, type='Fall_Detected')", True),
        (780, 340, 415, "9: confirmTransaction(alert_id='ALT-8921')", False),
        (340, 920, 385, "10: broadcastWebSocket(room='104', siren=TRUE)", True),
        (920, 920, 345, "11: triggerAudioAlarm & highlightRoomRed()", True, 25),
        (920, 340, 295, "12: POST /alerts/8921/ack (user_id='nurse_mary')", True),
        (340, 780, 260, "13: UPDATE alerts SET status='investigating'", True),
        (780, 340, 225, "14: ok()", False),
        (340, 920, 185, "15: pushStatusUpdate(status='investigating')", False),
    ]

    for item in messages:
        if len(item) == 5:
            x1, x2, y, text, is_sync = item
            self_loop = 0
        else:
            x1, x2, y, text, is_sync, self_loop = item

        if self_loop:
            ax.plot([x1, x1 + self_loop, x1 + self_loop, x1], [y, y, y - 18, y - 18], color="#000000", lw=1.2, zorder=6)
            ax.annotate("", xy=(x1, y - 18), xytext=(x1 + 6, y - 18), arrowprops=dict(arrowstyle="->", color="#000000", lw=1.2), zorder=6)
            ax.text(x1 + self_loop + 5, y - 9, text, ha="left", va="center", fontsize=7.5, color="#000000", fontfamily="serif")
        else:
            style = "->"
            ls = "-" if is_sync else "--"
            draw_arrow(ax, x1, y, x2, y, text, style=style, ls=ls, label_offset=(0, 7))

    save_fig(fig, "uml_02_sequence.png")

# ----------------------------------------------------------------------
# 4.2.3 STATE CHART DIAGRAM (Monochrome)
# ----------------------------------------------------------------------
def generate_diagram_03_state():
    """Generates Figure 4.3: State Chart Diagram for Room Sensing & Fall Incident Lifecycle."""
    fig, ax = init_canvas("Figure 4.3: State Machine Diagram for Room Sensing and Emergency Incident Lifecycle")
    
    # Initial State
    ax.add_patch(patches.Circle((60, 480), 10, fc="#000000", ec="#000000", zorder=5))
    ax.annotate("", xy=(120, 480), xytext=(70, 480), arrowprops=dict(arrowstyle="->", color="#000000", lw=1.4))
    ax.text(95, 492, "power_on", ha="center", fontsize=7.5, fontfamily="serif")

    # States
    states = [
        (120, 450, 130, 60, "UNCONFIGURED", "Node Registered;\nWaiting Baseline"),
        (310, 450, 130, 60, "EMPTY_BASELINE", "Room Unoccupied;\nNoise Filtered"),
        (510, 450, 140, 60, "OCCUPIED_NORMAL", "Human Presence;\nWalking / Sitting"),
        (720, 450, 150, 60, "HIGH_VARIANCE_EVENT", "Rapid RF Doppler;\nMovement Spike"),
        (720, 240, 150, 65, "CRITICAL_FALL_CONFIRMED", "Sudden Inactivity;\nConfidence >= 0.85"),
        (480, 240, 150, 65, "ALERT_DISPATCHED", "Siren Active;\nSMS & Socket Sent"),
        (240, 240, 140, 65, "ACKNOWLEDGED", "Staff Responding;\nSiren Silenced"),
        (240, 80, 140, 60, "RESOLVED_AUDITED", "Incident Resolved;\nAudit Log Created"),
    ]

    for x, y, w, h, name, sub in states:
        draw_box(ax, x, y, w, h, name, sub, fc="#FFFFFF", ec="#000000", lw=1.4, rx=8)

    # Transitions
    draw_arrow(ax, 250, 480, 310, 480, "calibrate_baseline()", label_offset=(0, 8))
    draw_arrow(ax, 440, 480, 510, 480, "motion_detected (SNR > 6dB)", label_offset=(0, 8))
    draw_arrow(ax, 580, 450, 580, 400, "", style="-")
    ax.plot([580, 375, 375], [400, 400, 450], color="#000000", lw=1.2, ls="--")
    ax.annotate("", xy=(375, 450), xytext=(375, 435), arrowprops=dict(arrowstyle="->", color="#000000", lw=1.2))
    ax.text(480, 388, "room_vacated (inactivity > 10m)", ha="center", fontsize=7.5, fontfamily="serif")

    draw_arrow(ax, 650, 480, 720, 480, "variance_spike > thresh", label_offset=(0, 8))
    draw_arrow(ax, 795, 450, 795, 305, "post_fall_silence detected", label_offset=(48, 0))
    draw_arrow(ax, 720, 272, 630, 272, "generate_alert()", label_offset=(0, 8))
    draw_arrow(ax, 480, 272, 380, 272, "caregiver_ack()", label_offset=(0, 8))
    draw_arrow(ax, 310, 240, 310, 140, "mark_resolved()", label_offset=(42, 0))
    
    # Return to baseline
    ax.plot([240, 180, 180, 310], [110, 110, 480, 480], color="#000000", lw=1.2, ls="--")
    ax.annotate("", xy=(310, 480), xytext=(290, 480), arrowprops=dict(arrowstyle="->", color="#000000", lw=1.2))
    ax.text(180, 300, "return_to_monitoring", rotation=90, ha="right", fontsize=7.5, fontfamily="serif")

    # False alarm transition
    draw_arrow(ax, 740, 450, 630, 460, "false_trigger (sitting)", ls=":", label_offset=(0, -10))

    save_fig(fig, "uml_03_state.png")

# ----------------------------------------------------------------------
# 4.2.4 ACTIVITY DIAGRAM (Monochrome)
# ----------------------------------------------------------------------
def generate_diagram_04_activity():
    """Generates Figure 4.4: Activity Diagram for CSI Ingestion & Fall Inference Pipeline."""
    fig, ax = init_canvas("Figure 4.4: Activity Diagram for Ingestion Pipeline and Fall Inference Workflow")
    
    # Swimlane Dividers
    ax.plot([330, 330], [50, 700], color="#000000", lw=1.4)
    ax.plot([660, 660], [50, 700], color="#000000", lw=1.4)
    ax.text(165, 685, "EDGE SENSING LAYER (ESP32 / Serial Bridge)", ha="center", fontsize=8.5, fontweight="bold", fontfamily="serif")
    ax.text(495, 685, "CLOUD INFERENCE ENGINE (FastAPI / WiFall)", ha="center", fontsize=8.5, fontweight="bold", fontfamily="serif")
    ax.text(830, 685, "MONITORING & ALERT CLIENT (React UI)", ha="center", fontsize=8.5, fontweight="bold", fontfamily="serif")

    # Initial Node
    ax.add_patch(patches.Circle((165, 650), 9, fc="#000000", ec="#000000", zorder=5))
    draw_arrow(ax, 165, 641, 165, 615)

    # Actions in Swimlane 1
    draw_box(ax, 85, 575, 160, 40, "Capture Raw CSI Packets\n(64 Orthogonal Subcarriers)", rx=6)
    draw_arrow(ax, 165, 575, 165, 540)
    draw_box(ax, 85, 500, 160, 40, "Serial Framing & UART\nBuffer (921600 Baud)", rx=6)
    draw_arrow(ax, 165, 500, 165, 465)
    draw_box(ax, 85, 425, 160, 40, "Transmit Ingest HTTP POST\n(/sensing/ingest)", rx=6)
    draw_arrow(ax, 245, 445, 415, 445, "CSI Stream")

    # Actions in Swimlane 2
    draw_box(ax, 415, 425, 160, 40, "Phase Sanitization &\nHampel Outlier Removal", rx=6)
    draw_arrow(ax, 495, 425, 495, 390)
    draw_box(ax, 415, 350, 160, 40, "Subtract Empty Baseline &\nCompute RF Doppler Shift", rx=6)
    draw_arrow(ax, 495, 350, 495, 315)
    draw_box(ax, 415, 275, 160, 40, "Activity Classifier ML\n(WiFall / Threshold Logic)", rx=6)
    draw_arrow(ax, 495, 275, 495, 240)

    # Decision Diamond in Swimlane 2
    diamond = Polygon([[495, 240], [535, 215], [495, 190], [455, 215]], closed=True, fc="#FFFFFF", ec="#000000", lw=1.4)
    ax.add_patch(diamond)
    ax.text(495, 215, "Fall?", ha="center", va="center", fontsize=7.5, fontweight="bold", fontfamily="serif")

    # Branch No
    draw_arrow(ax, 455, 215, 380, 215, "[No: Normal Motion]", label_offset=(0, 8))
    ax.plot([380, 380], [215, 140], color="#000000", lw=1.2)
    draw_box(ax, 380, 115, 150, 35, "Update Room Status:\nEmpty / Walking / Sitting", rx=6)

    # Branch Yes
    draw_arrow(ax, 535, 215, 750, 215, "[Yes: Fall Detected]", label_offset=(0, 8))

    # Actions in Swimlane 3
    draw_box(ax, 750, 195, 160, 40, "Persist Critical Alert &\nDispatch WebSocket Siren", rx=6)
    draw_arrow(ax, 830, 195, 830, 160)
    draw_box(ax, 750, 120, 160, 40, "Audio Siren & Red Beacon\non Nurse Duty Console", rx=6)
    draw_arrow(ax, 830, 120, 830, 85)

    # Final Node in Swimlane 3
    ax.add_patch(patches.Circle((830, 75), 10, fc="#FFFFFF", ec="#000000", lw=1.4, zorder=5))
    ax.add_patch(patches.Circle((830, 75), 6, fc="#000000", ec="#000000", zorder=6))

    save_fig(fig, "uml_04_activity.png")

# ----------------------------------------------------------------------
# 4.2.5 CLASS DIAGRAM (Monochrome)
# ----------------------------------------------------------------------
def generate_diagram_05_class():
    """Generates Figure 4.5: Class Diagram for Wi-Fi Sense SQLModel Relational Entities."""
    fig, ax = init_canvas("Figure 4.5: Class Diagram for System Relational Architecture and Sensing Models", width=15, height=10.5)

    def draw_class(x, y, w, h, name, attrs, methods):
        # Outer box
        draw_box(ax, x, y, w, h, rx=0)
        # Header partition
        header_h = 24
        ax.plot([x, x + w], [y + h - header_h, y + h - header_h], color="#000000", lw=1.2)
        ax.text(x + w / 2, y + h - 12, name, ha="center", va="center", fontsize=8, fontweight="bold", fontfamily="serif")
        
        # Attributes partition
        attr_h = (len(attrs) * 12) + 6
        ax.plot([x, x + w], [y + h - header_h - attr_h, y + h - header_h - attr_h], color="#000000", lw=1.2)
        y_curr = y + h - header_h - 10
        for a in attrs:
            ax.text(x + 6, y_curr, a, ha="left", va="center", fontsize=6.8, fontfamily="serif")
            y_curr -= 12

        # Methods partition
        y_curr = y + h - header_h - attr_h - 10
        for m in methods:
            ax.text(x + 6, y_curr, m, ha="left", va="center", fontsize=6.8, fontfamily="serif")
            y_curr -= 12

    # Classes:
    # 1. User
    draw_class(50, 480, 160, 160, "User", [
        "- id: UUID [PK]",
        "- email: EmailStr",
        "- password_hash: str",
        "- role_id: int [FK]",
        "- is_active: bool",
        "- organization_id: UUID"
    ], [
        "+ authenticate(pw): bool",
        "+ get_permissions(): List"
    ])

    # 2. Organization
    draw_class(270, 480, 160, 140, "Organization", [
        "- id: UUID [PK]",
        "- name: str",
        "- type: OrgType",
        "- contact_email: str"
    ], [
        "+ add_facility_manager()",
        "+ get_buildings(): List"
    ])

    # 3. Building & Floor
    draw_class(490, 480, 160, 140, "Building", [
        "- id: UUID [PK]",
        "- organization_id: UUID",
        "- name: str",
        "- address: str"
    ], [
        "+ list_floors(): List",
        "+ compute_occupancy()"
    ])

    # 4. Room
    draw_class(710, 480, 170, 170, "Room", [
        "- id: UUID [PK]",
        "- floor_id: UUID [FK]",
        "- room_number: str",
        "- baseline_matrix: JSON",
        "- dimensions_metadata: JSON",
        "- current_activity: str"
    ], [
        "+ update_occupancy()",
        "+ is_occupied(): bool",
        "+ get_active_nodes()"
    ])

    # 5. Device (ESP32 Node)
    draw_class(710, 240, 170, 170, "Device", [
        "- id: UUID [PK]",
        "- room_id: UUID [FK]",
        "- mac_address: str",
        "- node_role: NodeRole",
        "- status: str",
        "- api_token: str"
    ], [
        "+ verify_token(t): bool",
        "+ record_heartbeat()",
        "+ update_fault_status()"
    ])

    # 6. SensingEvent
    draw_class(490, 240, 160, 160, "SensingEvent", [
        "- id: UUID [PK]",
        "- room_id: UUID [FK]",
        "- device_id: UUID [FK]",
        "- activity_id: int [FK]",
        "- model_confidence: float",
        "- timestamp: datetime"
    ], [
        "+ is_emergency(): bool",
        "+ extract_amplitudes()"
    ])

    # 7. Alert
    draw_class(270, 240, 160, 160, "Alert", [
        "- id: UUID [PK]",
        "- room_id: UUID [FK]",
        "- event_type: str",
        "- severity: SeverityLevel",
        "- status: AlertStatus",
        "- acknowledged_by: UUID"
    ], [
        "+ acknowledge(user_id)",
        "+ resolve(resolution_notes)"
    ])

    # 8. HealthRecord
    draw_class(50, 240, 160, 150, "HealthRecord", [
        "- id: UUID [PK]",
        "- resident_id: UUID [FK]",
        "- heart_rate_est: float",
        "- breathing_rate_est: float",
        "- timestamp: datetime"
    ], [
        "+ check_vital_anomalies()"
    ])

    # Associations
    draw_arrow(ax, 210, 550, 270, 550, "1..* owns 1", style="-")
    draw_arrow(ax, 430, 550, 490, 550, "1 contains 1..*", style="-")
    draw_arrow(ax, 650, 550, 710, 550, "1 has 1..*", style="-")
    draw_arrow(ax, 795, 480, 795, 410, "1 monitors 1..*", style="-")
    draw_arrow(ax, 710, 320, 650, 320, "1 emits 0..*", style="-")
    draw_arrow(ax, 490, 320, 430, 320, "triggers 0..1", style="-")
    draw_arrow(ax, 270, 320, 210, 320, "tracks 0..*", style="-")

    save_fig(fig, "uml_05_class.png")

# ----------------------------------------------------------------------
# 4.2.6 OBJECT DIAGRAM (Monochrome)
# ----------------------------------------------------------------------
def generate_diagram_06_object():
    """Generates Figure 4.6: Object Diagram for Runtime Sensing Instance Topology."""
    fig, ax = init_canvas("Figure 4.6: Object Diagram for Active Room Telemetry and Fall Incident Snapshot")

    def draw_obj(x, y, w, h, obj_id, attrs):
        draw_box(ax, x, y, w, h, rx=2)
        ax.text(x + w / 2, y + h - 14, obj_id, ha="center", va="center", fontsize=8, fontweight="bold", fontfamily="serif")
        # underline instance name
        ax.plot([x + 8, x + w - 8], [y + h - 20, y + h - 20], color="#000000", lw=1)
        y_curr = y + h - 34
        for a in attrs:
            ax.text(x + 6, y_curr, a, ha="left", va="center", fontsize=6.8, fontfamily="serif")
            y_curr -= 12

    # Instances
    draw_obj(50, 480, 180, 120, "stMaryFacility : Organization", [
        "name = 'St. Mary Care Home'",
        "type = ELDER_CARE",
        "location = 'Kanjirappally'"
    ])

    draw_obj(280, 480, 180, 120, "buildingA : Building", [
        "name = 'Wing A - Assisted Living'",
        "total_floors = 3"
    ])

    draw_obj(510, 480, 200, 130, "room104 : Room", [
        "room_number = '104'",
        "resident_name = 'Abraham V.'",
        "current_activity = 'Fall_Detected'",
        "occupancy_status = OCCUPIED"
    ])

    draw_obj(760, 480, 190, 130, "nodeRx104 : Device", [
        "mac = '7c:4f:ad:26:05:78'",
        "role = CSI_RECEIVER",
        "status = 'ONLINE'",
        "baud_rate = 921600"
    ])

    draw_obj(760, 230, 190, 130, "event9012 : SensingEvent", [
        "activity = 'Fall_Detected'",
        "confidence = 0.96",
        "rssi = -42 dBm",
        "timestamp = '14:22:04 UTC'"
    ])

    draw_obj(510, 230, 200, 130, "alert41 : Alert", [
        "event_type = 'Fall_Detected'",
        "severity = CRITICAL",
        "status = 'INVESTIGATING'",
        "ack_by = 'nurse_mary'"
    ])

    draw_obj(280, 230, 180, 120, "maryCaregiver : User", [
        "email = 'mary@wifisense.com'",
        "role = 'caregiver'",
        "on_duty = TRUE"
    ])

    draw_obj(50, 230, 180, 120, "nurseStation : ClientUI", [
        "device = 'Station Tablet 01'",
        "alarm_sound = ACTIVE",
        "active_view = 'dashboard'"
    ])

    # Links
    ax.plot([230, 280], [540, 540], color="#000000", lw=1.2)
    ax.plot([460, 510], [540, 540], color="#000000", lw=1.2)
    ax.plot([710, 760], [540, 540], color="#000000", lw=1.2)
    ax.plot([855, 855], [480, 360], color="#000000", lw=1.2)
    ax.plot([760, 710], [295, 295], color="#000000", lw=1.2)
    ax.plot([510, 460], [295, 295], color="#000000", lw=1.2)
    ax.plot([280, 230], [295, 295], color="#000000", lw=1.2)

    save_fig(fig, "uml_06_object.png")

# ----------------------------------------------------------------------
# 4.2.7 COMPONENT DIAGRAM (Monochrome)
# ----------------------------------------------------------------------
def generate_diagram_07_component():
    """Generates Figure 4.7: Component Diagram for Wi-Fi Sense Software Subsystems."""
    fig, ax = init_canvas("Figure 4.7: Component Diagram for System Architecture and Interface Contracts")

    def draw_comp(x, y, w, h, name, sub=""):
        draw_box(ax, x, y, w, h, rx=2)
        # Small component tabs on left edge
        draw_box(ax, x - 8, y + h - 16, 16, 8, rx=0)
        draw_box(ax, x - 8, y + h - 30, 16, 8, rx=0)
        ax.text(x + w / 2, y + h / 2 + 5, f"<<component>>\n{name}", ha="center", va="center", fontsize=8, fontweight="bold", fontfamily="serif")
        if sub:
            ax.text(x + w / 2, y + 14, sub, ha="center", va="center", fontsize=7, color="#444444", fontfamily="serif")

    # Layer 1: Hardware Firmware & Serial
    draw_comp(60, 460, 170, 90, "ESP32 CSI Firmware", "C++ / ESP-IDF SDK")
    draw_comp(270, 460, 180, 90, "Serial Ingestion Bridge", "tools/csi_serial_bridge.py")

    # Layer 2: Core Backend Engine
    draw_comp(500, 460, 190, 90, "FastAPI Ingestion Gateway", "Routers: /sensing & /auth")
    draw_comp(740, 460, 190, 90, "WiFall Inference Engine", "SciPy, PCA & ML Classifier")

    # Layer 3: Persistence & Client
    draw_comp(270, 220, 180, 90, "SQLModel ORM Subsystem", "Entity Relational Mappings")
    draw_comp(500, 220, 190, 90, "PostgreSQL Database", "Supabase AWS Managed Store")
    draw_comp(740, 220, 190, 90, "React 18 Dashboard", "Vite, Tailwind & Canvas Waveforms")

    # Interfaces & Connectors
    draw_arrow(ax, 230, 505, 270, 505, "UART / 921600", style="->")
    draw_arrow(ax, 450, 505, 500, 505, "HTTP POST JSON", style="->")
    draw_arrow(ax, 690, 505, 740, 505, "CSI Matrix Array", style="->")
    draw_arrow(ax, 595, 460, 595, 310, "Persistence", style="->")
    draw_arrow(ax, 450, 265, 500, 265, "SQLAlchemy Pools", style="->")
    draw_arrow(ax, 690, 265, 740, 265, "WebSocket / REST", style="<-")

    save_fig(fig, "uml_07_component.png")

# ----------------------------------------------------------------------
# 4.2.8 DEPLOYMENT DIAGRAM (Monochrome)
# ----------------------------------------------------------------------
def generate_diagram_08_deployment():
    """Generates Figure 4.8: Deployment Diagram for Distributed Hardware & Cloud Infrastructure."""
    fig, ax = init_canvas("Figure 4.8: Deployment Diagram for Edge Hardware, Render Backend, and Supabase Cloud")

    def draw_node(x, y, w, h, name, sub="", artifacts=[]):
        # 3D Node isometric box
        draw_box(ax, x, y, w, h, rx=2)
        ax.plot([x, x + 15], [y + h, y + h + 15], color="#000000", lw=1.2)
        ax.plot([x + w, x + w + 15], [y + h, y + h + 15], color="#000000", lw=1.2)
        ax.plot([x + w, x + w + 15], [y, y + 15], color="#000000", lw=1.2)
        ax.plot([x + 15, x + w + 15], [y + h + 15, y + h + 15], color="#000000", lw=1.2)
        ax.plot([x + w + 15, x + w + 15], [y + 15, y + h + 15], color="#000000", lw=1.2)
        
        ax.text(x + w / 2, y + h - 14, f"<<device / node>>\n{name}", ha="center", va="center", fontsize=8, fontweight="bold", fontfamily="serif")
        if sub:
            ax.text(x + w / 2, y + h - 34, sub, ha="center", va="center", fontsize=7, color="#333333", fontfamily="serif")
        
        y_art = y + h - 52
        for art in artifacts:
            draw_box(ax, x + 12, y_art - 18, w - 24, 20, f"<<artifact>> {art}", rx=0)
            y_art -= 26

    # Node 1: Edge Sensing Node
    draw_node(40, 420, 200, 180, "ESP32-S3 Microcontroller", "Physical Room Sensor Node", [
        "firmware.bin",
        "FreeRTOS CSI Task",
        "Wi-Fi Promiscuous Sniffer"
    ])

    # Node 2: Local Host PC
    draw_node(270, 420, 200, 180, "Gateway Host Machine", "Local USB Serial Bridge", [
        "csi_serial_bridge.py",
        "PySerial 3.5 Daemon"
    ])

    # Node 3: Cloud Backend Server
    draw_node(500, 420, 210, 190, "Render Linux Container", "Python 3.10 ASGI Runtime", [
        "FastAPI Service (Uvicorn)",
        "SQLModel / SQLAlchemy",
        "WiFall Inference Engine"
    ])

    # Node 4: Cloud Database
    draw_node(740, 420, 210, 190, "Supabase Managed Host", "AWS Region ap-south-1 (Mumbai)", [
        "PostgreSQL 17 Instance",
        "Connection Pooler",
        "Row Level Policies"
    ])

    # Node 5: Client Browser
    draw_node(380, 120, 250, 160, "Client Workstation / Tablet", "Modern Web Browser", [
        "React 18 SPA (Vite)",
        "Live Subcarrier Canvas",
        "Audio Siren Synthesizer"
    ])

    # Deployment Connections
    draw_arrow(ax, 240, 510, 270, 510, "USB COM4 / UART", style="-")
    draw_arrow(ax, 470, 510, 500, 510, "HTTPS WAN", style="-")
    draw_arrow(ax, 710, 510, 740, 510, "TCP 5432 / TLS", style="-")
    draw_arrow(ax, 605, 420, 530, 280, "WSS / HTTPS", style="-")

    save_fig(fig, "uml_08_deployment.png")

# ----------------------------------------------------------------------
# 4.2.9 COLLABORATION DIAGRAM (Monochrome)
# ----------------------------------------------------------------------
def generate_diagram_09_collaboration():
    """Generates Figure 4.9: Collaboration Diagram for Emergency Fall Response Protocol."""
    fig, ax = init_canvas("Figure 4.9: Collaboration Diagram for Emergency Fall Detection & Response Protocol")

    # Objects in hexagonal layout
    draw_box(ax, 60, 460, 160, 60, "1: :ESP32Node", "CSI Receiver Node", rx=4)
    draw_box(ax, 320, 560, 180, 60, "2: :SerialBridge", "Gateway Ingest Daemon", rx=4)
    draw_box(ax, 620, 560, 180, 60, "3: :FastAPIServer", "Cloud ASGI Router", rx=4)
    draw_box(ax, 760, 360, 180, 60, "4: :InferenceModel", "WiFall Classifier", rx=4)
    draw_box(ax, 480, 220, 180, 60, "5: :SupabaseDB", "PostgreSQL Engine", rx=4)
    draw_box(ax, 160, 220, 180, 60, "6: :CaregiverClient", "Duty Console UI", rx=4)

    # Connections with numbered message sequencing
    ax.plot([220, 320], [490, 590], color="#000000", lw=1.2)
    ax.text(250, 560, "1: sendRawBytes()\n-->", fontsize=7.5, fontfamily="serif")

    ax.plot([500, 620], [590, 590], color="#000000", lw=1.2)
    ax.text(560, 605, "2: postPayload()\n-->", ha="center", fontsize=7.5, fontfamily="serif")

    ax.plot([710, 850], [560, 420], color="#000000", lw=1.2)
    ax.text(800, 510, "3: classifyFeatures()\n-->", fontsize=7.5, fontfamily="serif")

    ax.plot([850, 570], [360, 280], color="#000000", lw=1.2)
    ax.text(730, 305, "4: recordIncident()\n-->", fontsize=7.5, fontfamily="serif")

    ax.plot([480, 340], [250, 250], color="#000000", lw=1.2)
    ax.text(410, 265, "5: broadcastAlarm()\n<--", ha="center", fontsize=7.5, fontfamily="serif")

    ax.plot([250, 140], [280, 460], color="#000000", lw=1.2)
    ax.text(170, 360, "6: silenceSiren()\n-->", fontsize=7.5, fontfamily="serif")

    save_fig(fig, "uml_09_collaboration.png")

# ----------------------------------------------------------------------
# Master Orchestration
# ----------------------------------------------------------------------
def generate_all_diagrams():
    print("=" * 70)
    print("GENERATING 9 PUBLICATION-GRADE MONOCHROME UML 2.5 DIAGRAMS (300 DPI)")
    print(f"Target Output Directory: {OUTPUT_DIR}")
    print("=" * 70)
    generate_diagram_01_use_case()
    generate_diagram_02_sequence()
    generate_diagram_03_state()
    generate_diagram_04_activity()
    generate_diagram_05_class()
    generate_diagram_06_object()
    generate_diagram_07_component()
    generate_diagram_08_deployment()
    generate_diagram_09_collaboration()
    print("=" * 70)
    print("ALL 9 MONOCHROME UML DIAGRAMS GENERATED SUCCESSFULLY")
    print("=" * 70)

if __name__ == "__main__":
    generate_all_diagrams()
