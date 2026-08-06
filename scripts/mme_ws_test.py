import websocket
import json
import time

WS_URL = "ws://localhost:9000/"

ws = websocket.WebSocket()
ws.connect(WS_URL)

print("Connected to Amarisoft MME WebSocket")

def recv_message(expected):
    while True:
        msg = json.loads(ws.recv())
        if msg.get("message") == expected:
            return msg

try:
    while True:
        # ---------- UE STATE ----------
        ws.send(json.dumps({"message": "ue_get"}))
        ue_reply = recv_message("ue_get")

        print("\n==== CORE UE STATE ====")

        active_ues = 0
        total_sessions = 0

        for ue in ue_reply.get("ue_list", []):
            if ue.get("registered"):
                active_ues += 1

            print(
                "IMSI:", ue.get("imsi"),
                "| IMEISV:", ue.get("imeisv"),
                "| Registered:", ue.get("registered"),
                "| AMF_UE_ID:", ue.get("amf_ue_id")
            )

            for b in ue.get("bearers", []):
                total_sessions += 1
                print(
                    "  PDU Session:", b.get("pdu_session_id"),
                    "| DNN:", b.get("apn"),
                    "| Slice (SST):", b.get("sst"),
                    "| QFI:", b.get("qos_flow_id"),
                    "| IP:", b.get("ip")
                )

        # ---------- STATS ----------
        ws.send(json.dumps({"message": "stats"}))
        stats_reply = recv_message("stats")

        counters = stats_reply.get("counters", {}).get("messages", {})
        pdn_list = stats_reply.get("pdn_list", [])

        print("\n==== CORE LOAD INDICATORS ====")
        print("Active UEs:", active_ues)
        print("Total PDU Sessions:", total_sessions)

        print("\n-- Control-plane signalling --")
        print("NAS Registration Requests:",
              counters.get("5gs_nas_registration_request", 0))
        print("NAS Service Requests:",
              counters.get("5gs_nas_service_request", 0))
        print("PDU Session Establishments:",
              counters.get("5gs_nas_pdu_session_establishment_request", 0))
        print("PDU Session Releases:",
              counters.get("5gs_nas_pdu_session_release_request", 0))

        print("\n-- User-plane traffic (per DNN) --")
        for pdn in pdn_list:
            print(
                "DNN:", pdn.get("access_point_name"),
                "| UL bytes:", pdn.get("ul_bytes"),
                "| DL bytes:", pdn.get("dl_bytes")
            )

        time.sleep(3)

except KeyboardInterrupt:
    print("\nStopping client")
    ws.close()
