import { useEffect, useRef } from "react";

type AccessGateProps = {
  accessCode: string;
  errorMessage: string | null;
  isSubmitting: boolean;
  onAccessCodeChange: (accessCode: string) => void;
  onSubmit: () => void;
};

export function AccessGate({
  accessCode,
  errorMessage,
  isSubmitting,
  onAccessCodeChange,
  onSubmit,
}: AccessGateProps) {
  const inputRef = useRef<HTMLInputElement | null>(null);

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  const digits = accessCode.padEnd(6, " ").slice(0, 6).split("");

  return (
    <div className="access-gate-backdrop" onClick={() => inputRef.current?.focus()}>
      <div className="access-gate-card">
        <span className="access-gate-label">Private Demo</span>
        <h1 className="access-gate-title">Enter access code</h1>
        <form
          className="access-gate-form"
          onSubmit={(event) => {
            event.preventDefault();
            onSubmit();
          }}
        >
          <label className="access-gate-input-shell">
            <input
              ref={inputRef}
              className="access-gate-input"
              inputMode="numeric"
              autoComplete="one-time-code"
              maxLength={6}
              value={accessCode}
              onChange={(event) => onAccessCodeChange(event.target.value.replace(/\D/g, "").slice(0, 6))}
            />
            <div className="access-gate-digits" aria-hidden="true">
              {digits.map((digit, index) => (
                <span key={index} className="access-gate-digit">
                  {digit === " " ? "" : digit}
                </span>
              ))}
            </div>
          </label>
          <button className="access-gate-submit" disabled={isSubmitting || accessCode.length !== 6} type="submit">
            {isSubmitting ? "Verifying..." : "Continue"}
          </button>
        </form>
        <p className="access-gate-error">{errorMessage ?? "\u00A0"}</p>
      </div>
    </div>
  );
}
