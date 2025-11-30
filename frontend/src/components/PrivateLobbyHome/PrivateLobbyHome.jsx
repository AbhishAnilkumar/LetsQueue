import React, { useState, useEffect, useRef } from "react";
import CreateLobby from "./CreateLobby";
import LobbyCreated from "./LobbyCreated";
import LobbyView from "./LobbyView";
import api from "../../services/api";
import styles from "./PrivateLobbyHome.module.css";

export default function PrivateLobbyHome() {
  const [step, setStep] = useState("create");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [lobbyCode, setLobbyCode] = useState("");
  const [lobbyData, setLobbyData] = useState(null);
  
  const hasFetchedRef = useRef(false);

  useEffect(() => {
    if (hasFetchedRef.current) return;
    
    const urlParams = new URLSearchParams(window.location.search);
    const code = urlParams.get("code");
    
    if (code) {
      hasFetchedRef.current = true;
      
      // Check if we just created this lobby (stored in sessionStorage)
      const createdCode = sessionStorage.getItem("createdLobbyCode");
      const isCreator = createdCode === code;
      
      fetchLobbyByCode(code, isCreator);
    }
  }, []);

  const createLobby = async (maxParticipants) => {
    setLoading(true);
    setError("");
    try {
      const response = await api.post("/private-lobbies/", {
        max_participants: maxParticipants,
      });

      const code = response.data.lobby_code || response.data.code;
      const lobby = response.data.lobby || response.data;

      setLobbyCode(code);
      setLobbyData(lobby);
      setStep("created");
      
      // Store that we created this lobby
      sessionStorage.setItem("createdLobbyCode", code);
      
      window.history.pushState({}, "", `?code=${code}`);
    } catch (err) {
      console.error("Create lobby error:", err);
      setError(err.response?.data?.message || err.message || "Failed to create lobby");
    } finally {
      setLoading(false);
    }
  };

  const fetchLobbyByCode = async (code, isCreator = false) => {
    setLoading(true);
    setError("");
    try {
      const response = await api.get(`/private-lobbies/by-code/${code}/`);
      const lobby = response.data.lobby || response.data;

      setLobbyCode(code);
      setLobbyData(lobby);
      setStep(isCreator ? "created" : "view");
    } catch (err) {
      console.error("Fetch lobby error:", err);
      const message =
        err.response?.status === 410
          ? "This lobby has expired"
          : "Lobby not found";
      setError(message);
      setStep("create");
      window.history.pushState({}, "", window.location.pathname);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={styles.container}>
      <div className={styles.wrapper}>
        <header className={styles.header}>
          <h1 className={styles.title}>LetsQueue</h1>
          <p className={styles.subtitle}>Create private lobbies for your squad</p>
          <button disabled className={styles.comingSoonBtn}>
            Public Lobbies • Coming Soon
          </button>
        </header>

        {step === "create" && (
          <CreateLobby
            onCreateLobby={createLobby}
            loading={loading}
            error={error}
          />
        )}

        {step === "created" && lobbyCode && lobbyData && (
          <LobbyCreated lobbyCode={lobbyCode} lobbyData={lobbyData} />
        )}

        {step === "view" && lobbyCode && lobbyData && (
          <LobbyView lobbyCode={lobbyCode} lobbyData={lobbyData} />
        )}

        {loading && step === "create" && (
          <div style={{ 
            textAlign: 'center', 
            padding: '40px', 
            color: '#888',
            background: '#141414',
            border: '1px solid #2a2a2a',
            borderRadius: '12px'
          }}>
            Loading lobby...
          </div>
        )}
      </div>
    </div>
  );
}