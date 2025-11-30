import React from "react";
import { Users, Clock, AlertCircle, Copy, Check } from "lucide-react";
import { useState } from "react";
import styles from "./LobbyView.module.css";

export default function LobbyView({ lobbyCode, lobbyData }) {
  const [copied, setCopied] = useState(false);

  const formatTime = (isoString) => {
    const date = new Date(isoString);
    return date.toLocaleTimeString("en-US", {
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  const copyCode = () => {
    navigator.clipboard.writeText(lobbyCode);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h2 className={styles.title}>Private Lobby</h2>
        <div className={styles.statusBadge}>Active</div>
      </div>

      <div className={styles.codeSection}>
        <div className={styles.codeLabel}>Lobby Code</div>
        <div className={styles.codeRow}>
          <div className={styles.code}>{lobbyCode}</div>
          <button onClick={copyCode} className={styles.copyIconBtn}>
            {copied ? <Check size={18} /> : <Copy size={18} />}
          </button>
        </div>
      </div>

      <div className={styles.infoGrid}>
        <div className={styles.infoCard}>
          <Users size={20} className={styles.infoIcon} />
          <div>
            <div className={styles.infoLabel}>Max Participants</div>
            <div className={styles.infoValue}>{lobbyData.max_participants}</div>
          </div>
        </div>

        <div className={styles.infoCard}>
          <Clock size={20} className={styles.infoIcon} />
          <div>
            <div className={styles.infoLabel}>Expires At</div>
            <div className={styles.infoValue}>
              {formatTime(lobbyData.expires_at)}
            </div>
          </div>
        </div>
      </div>

      <div className={styles.noticeBox}>
        <AlertCircle size={18} className={styles.noticeIcon} />
        <span>This lobby will expire at the scheduled time</span>
      </div>
    </div>
  );
}