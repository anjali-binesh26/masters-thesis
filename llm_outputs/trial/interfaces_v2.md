This analysis provides a comprehensive map of the interfaces available for managing, configuring, and monitoring the Amarisoft LTE and NR Core Network (LTEMME).

## System Overview
The system is a Linux-based core network implementation. It is managed through three primary planes: a **static configuration plane** (files), a **programmatic management plane** (WebSocket API), and a **manual monitoring plane** (CLI Monitor).

---

## 1. Configuration Interface (Static)
Used for initial provisioning and persistent system settings. Changes here typically require a process restart to take effect unless modified via the Remote API.

*   **Interface Name:** System Configuration File
*   **Type:** Configuration File (JSON-like syntax)
*   **Access Details:** Path typically `/config/mme.cfg` (or as specified during startup: `./ltemme config/mme.cfg`).
*   **Parameters:** 
    *   **Global Settings:** `plmn` (String), `mme_code` (Integer), `mme_group_id` (Integer), `com_addr` (String: IP/Port for API).
    *   **Logging:** `log_filename` (String), `log_options` (String: e.g., `"all.level=debug"`).
    *   **Network Provisioning:** `pdn_list` (Array of Objects), `ue_db` (Included file), `nssai` (Array).
    *   **API Security:** `com_auth` (Object: `passfile`, `password`, `unsecure`).
*   **Response / Output:** The system initializes its internal state based on these values upon startup.
*   **Authentication:** OS-level file system permissions.
*   **Example:**
    ```json
    {
      "plmn": "00101",
      "com_addr": "[::]:9000",
      "log_options": "all.level=debug",
      "pdn_list": [{ "access_point_name": "internet", "pdn_type": "ipv4" }]
    }
    ```

---

## 2. Programmatic Management Interface (Remote API)
The primary interface for external controllers to manage the network in real-time.

*   **Interface Name:** Remote API
*   **Type:** WebSocket (RFC 6455)
*   **Access Details:** `ws://<com_addr>` (Default port 9000).
*   **Authentication:** 
    *   **Optional:** If `com_auth` is configured, the server sends an `authenticate` message with a `challenge` string.
    *   **Requirement:** The client must respond with an `authenticate` message containing a `res` value calculated as `HMAC-SHA256("<type>:<password>:<name>", "<challenge>")`.
*   **General Message Format:** All messages are strict JSON. 
    *   **Request:** `{"message": "command_name", "message_id": "unique_id", ...params}`
    *   **Response:** `{"message": "command_name", "message_id": "unique_id", ...results}`

### 2.1 Configuration & System Management
| Interface Name | Parameters (Inputs) | Response / Effect |
| :--- | :--- | :--- |
| `config_get` | None | Returns the current full system configuration as a JSON object. |
| `config_set` | Any valid config property (e.g., `relative_capacity`, `log_options`) | Updates the running configuration. |
| `stats` | None | Returns CPU load and counters for messages/errors. |
| `help` | None | Lists all available API messages. |
| `quit` | None | Terminates the LTEMME process. |

### 2.2 Subscriber & Device Management (UE/ME)
| Interface Name | Parameters (Inputs) | Response / Effect |
| :--- | :--- | :--- |
| `ue_get` | `imsi` (Opt), `nai` (Opt), `imei` (Opt), `type` (Opt) | Returns a list of current UEs and their session states. |
| `ue_add` | `ue_db` (Array of UE config objects) | Adds new subscribers to the active database. |
| `ue_del` | `imsi` (Req) or `nai` (Req) | Removes a subscriber from the database. |
| `ue_detach` | `imsi` (Req), `cause` (Opt) | Forces a UE to detach from the network. |
| `me_add` | `whitelist`, `blacklist`, `greylist` | Manages the ME (Mobile Equipment) identity database. |

### 2.3 Session & Bearer Control
| Interface Name | Parameters (Inputs) | Response / Effect |
| :--- | :--- | :--- |
| `ue_activate_dedicated_bearer` | `imsi`, `apn`, `qci`, `gbr` (Opt) | Triggers a network-initiated dedicated bearer activation. |
| `ue_modify_bearer` | `imsi`, `erab_id`, `qos` (Opt) | Modifies existing bearer QoS parameters. |
| `ue_deactivate_bearer` | `imsi`, `erab_id` (Req) | Tears down a specific bearer. |

### 2.4 Monitoring & Logging
| Interface Name | Parameters (Inputs) | Response / Effect |
| :--- | :--- | :--- |
| `log_get` | `min` (int), `max` (int), `layers` (obj) | Retrieves a slice of system logs from the memory buffer. |
| `log_set` | `log` (string), `layer` (string), `level` (string) | Manually injects a log entry into the system. |
| `log_reset` | None | Clears the internal log buffer. |

### 2.5 Network Interface Control (Connectivity)
The API allows forcing connections/disconnections to external network functions (HSS, EIR, etc.).
*   **Commands:** `s6connect`/`s6disconnect`, `s13connect`/`s13disconnect`, `n8connect`/`n8disconnect`, etc.
*   **Parameters:** Typically `addr` (String: IP/Port).
*   **Effect:** Forces the SCTP/TCP handshake with the specified peer.

---

## 3. Manual Management Interface (CLI Monitor)
A local interactive shell for administrators.

*   **Interface Name:** Command Line Monitor
*   **Type:** CLI (Standard Input/Output)
*   **Access Details:** Executed as a child process or via a specific monitor binary (refer to Installation section).
*   **Authentication:** OS-level user permissions.
*   **Commands:** Mirrors the Remote API functionality.
    *   `enb` / `ng_ran`: Lists connected base stations.
    *   `ue [reg]`: Lists active/registered UEs.
    *   `apn`: Lists configured APNs/DNNs.
    *   `log [options]`: Displays real-time logs.
    *   `pws_write <id>`: Starts broadcasting a Public Warning System message.
*   **Example:** `ue reg` $\rightarrow$ *Output: List of currently registered UEs.*

---

## 4. Low-Level System Interface
Interfaces interacting directly with the Linux OS for network plumbing.

*   **Interface Name:** Local Network Configurator
*   **Type:** Shell Script
*   **Access Details:** `sudo ./lte_init.sh [-6 <ifname>]`
*   **Parameters:** `-6` (Optional flag to specify a specific network interface name, e.g., `eth1`).
*   **Effect:** Configures IP forwarding, masquerading, and the `tun0` virtual interface used for UE traffic.

---

## Summary Table for Developers

| Function | Interface | Access Method | Format | Auth |
| :--- | :--- | :--- | :--- | :--- |
| **Initial Setup** | Config File | File System | JSON-like | OS Perms |
| **Real-time Control** | Remote API | WebSocket | JSON | HMAC-SHA256 |
| **Live Monitoring** | CLI Monitor | Terminal/SSH | Text/Cmd | OS Perms |
| **OS Networking** | `lte_init.sh` | Shell | Bash | Sudo/Root |

### Assumptions & Ambiguities
1.  **API Endpoint:** The documentation mentions `com_addr` in the config but does not provide a default IP. I have assumed the developer will read `com_addr` from the config file to determine the WebSocket URL.
2.  **CLI Monitor Execution:** The documentation describes the commands but not the exact binary name to launch the monitor. It is assumed to be bundled with the `ltemme` package.
3.  **SCTP/TCP Defaults:** For connectivity commands (e.g., `s6connect`), it is assumed that if `addr` is omitted, the system falls back to the address defined in the `.cfg` file.
