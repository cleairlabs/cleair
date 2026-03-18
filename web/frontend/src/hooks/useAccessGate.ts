import { useCallback, useEffect, useState } from "react";

type AccessState = "checking" | "locked" | "open";

export async function loadSessionStatus(backendUrl: string): Promise<boolean> {
  const response = await fetch(`${backendUrl}/auth/session`, { credentials: "include" });
  if (!response.ok) {
    return false;
  }
  const body = (await response.json()) as { authenticated: boolean };
  return body.authenticated;
}

export function useAccessGate(backendUrl: string) {
  const [accessState, setAccessState] = useState<AccessState>("checking");
  const [accessCode, setAccessCode] = useState("");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const refreshAccessState = useCallback(async () => {
    try {
      const isAuthenticated = await loadSessionStatus(backendUrl);
      setAccessState(isAuthenticated ? "open" : "locked");
      setErrorMessage(isAuthenticated ? null : "Session expired. Enter code again.");
    } catch {
      setAccessState("locked");
    }
  }, [backendUrl]);

  useEffect(() => {
    void refreshAccessState();
  }, [refreshAccessState]);

  const submitAccessCode = async () => {
    if (accessCode.length !== 6 || isSubmitting) return;
    setIsSubmitting(true);
    setErrorMessage(null);
    try {
      const response = await fetch(`${backendUrl}/auth/verify`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ code: accessCode }),
      });
      if (!response.ok) throw new Error(`Server returned ${response.status}`);
      setAccessCode("");
      setAccessState("open");
    } catch {
      setErrorMessage("Invalid code.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return {
    accessState,
    accessCode,
    setAccessCode,
    errorMessage,
    isSubmitting,
    refreshAccessState,
    submitAccessCode,
  };
}
