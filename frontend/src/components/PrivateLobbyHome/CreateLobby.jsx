import React, { useState } from "react";
import { Users, Clock, Loader2 } from "lucide-react";
import styles from "./CreateLobby.module.css";

export default function CreateLobby({ onCreateLobby, loading, error }) {
  const [maxParticipants, setMaxParticipants] = useState(3);
  const [timeRange, setTimeRange] = useState(30);

  const handleSubmit = () => {
    onCreateLobby(maxParticipants);
  };

  return (
    <div className={styles.container}>
      <h2 className={styles.title}>Create Private Lobby</h2>

      {error && (
        <div className={styles.errorBox}>
          {error}
        </div>
      )}

      <div className={styles.section}>
        <label className={styles.label}>
          <Users size={18} className={styles.icon} />
          Number of Participants
        </label>

        <div className={styles.buttonGroup}>
          {[2, 3, 4, 5].map((num) => (
            <button
              key={num}
              onClick={() => setMaxParticipants(num)}
              className={`${styles.optionBtn} ${
                maxParticipants === num ? styles.active : ""
              }`}
            >
              {num}
            </button>
          ))}
        </div>
      </div>

      <div className={styles.section}>
        <label className={styles.label}>
          <Clock size={18} className={styles.icon} />
          Expiry Time: {timeRange} minutes
        </label>

        <input
          type="range"
          min="15"
          max="60"
          step="15"
          value={timeRange}
          onChange={(e) => setTimeRange(Number(e.target.value))}
          className={styles.slider}
        />
      </div>

      <button
        onClick={handleSubmit}
        disabled={loading}
        className={styles.createBtn}
      >
        {loading ? (
          <>
            <Loader2 size={20} className={styles.spinner} />
            Creating...
          </>
        ) : (
          "Create Lobby"
        )}
      </button>
    </div>
  );
}