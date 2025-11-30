import React, { useState } from "react";
import { Copy, Check, Users, Clock } from "lucide-react";
import styles from "./LobbyCreated.module.css";

export default function LobbyCreated({ lobbyCode, lobbyData }) {
  const [copied, setCopied] = useState(false);

  const copyLink = () => {
    const link = `${window.location.origin}?code=${lobbyCode}`;
    navigator.clipboard.writeText(link);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const formatTime = (isoString) => {
    const date = new Date(isoString);
    return date.toLocaleTimeString("en-US", {
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  return (
    <div className={styles.container}>
      <div className={styles.successBox}>
        <Check size={24} className={styles.checkIcon} />
        Lobby Created Successfully!
      </div>

      <div className={styles.codeBox}>
        <div className={styles.codeLabel}>Lobby Code</div>
        <div className={styles.code}>{lobbyCode}</div>
      </div>

      <button onClick={copyLink} className={styles.copyBtn}>
        {copied ? (
          <>
            <Check size={18} />
            Copied!
          </>
        ) : (
          <>
            <Copy size={18} />
            Copy Invite Link
          </>
        )}
      </button>

      <div className={styles.details}>
        <div className={styles.detailItem}>
          <Users size={18} className={styles.detailIcon} />
          <div>
            <div className={styles.detailLabel}>Max Participants</div>
            <div className={styles.detailValue}>{lobbyData.max_participants}</div>
          </div>
        </div>
        <div className={styles.detailItem}>
          <Clock size={18} className={styles.detailIcon} />
          <div>
            <div className={styles.detailLabel}>Expires At</div>
            <div className={styles.detailValue}>{formatTime(lobbyData.expires_at)}</div>
          </div>
        </div>
      </div>

      <p className={styles.shareText}>
        Share this link with your friends to join the lobby
      </p>
    </div>
  );
}